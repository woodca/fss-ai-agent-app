#!/usr/bin/env python3
"""
Twilio SMS Handler for Air Force CS Section
Handles incoming SMS messages and sends responses via Twilio
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from database_manager import DatabaseManager
import re

class TwilioHandler:
    def __init__(self):
        # Load Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER', '+18134381333')
        
        # Initialize Twilio client if credentials available
        self.client = None
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        
        # Initialize database manager
        self.db = DatabaseManager()
        
        # Track processed messages to avoid duplicates
        self.processed_messages_file = 'processed_messages.json'
        self.processed_messages = self._load_processed_messages()
    
    def _load_processed_messages(self) -> set:
        """Load set of processed message SIDs"""
        try:
            with open(self.processed_messages_file, 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()
    
    def _save_processed_messages(self):
        """Save processed message SIDs"""
        with open(self.processed_messages_file, 'w') as f:
            json.dump(list(self.processed_messages), f)
    
    def verify_personnel_by_phone(self, phone_number: str) -> Optional[Dict]:
        """Verify personnel identity by phone number"""
        # Normalize phone number (remove non-digits, add +1 if needed)
        digits = re.sub(r'\D', '', phone_number)
        if len(digits) == 10:
            digits = '1' + digits
        if len(digits) == 11 and digits[0] == '1':
            normalized = '+' + digits
        else:
            normalized = phone_number
        
        # Look up personnel by phone
        with self.db.transaction() as conn:
            cursor = conn.execute("""
                SELECT * FROM personnel 
                WHERE phone = ? OR phone = ? OR phone = ?
            """, (phone_number, normalized, digits))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
        
        return None
    
    def process_incoming_sms(self, from_number: str, body: str, message_sid: str) -> str:
        """Process incoming SMS and return response"""
        
        # Check if already processed
        if message_sid in self.processed_messages:
            return "Message already processed."
        
        # Verify sender
        personnel = self.verify_personnel_by_phone(from_number)
        if not personnel:
            return "Your phone number is not registered in our system. Please contact the CS section."
        
        # Mark as processed
        self.processed_messages.add(message_sid)
        self._save_processed_messages()
        
        # Parse message content
        body_lower = body.lower().strip()
        
        # Handle different command types
        if any(word in body_lower for word in ['appointment', 'appt', 'schedule']):
            return self._handle_appointment_request(personnel, body)
        elif any(word in body_lower for word in ['cancel', 'reschedule']):
            return self._handle_appointment_change(personnel, body)
        elif any(word in body_lower for word in ['status', 'where', 'location']):
            return self._handle_status_query(personnel)
        elif any(word in body_lower for word in ['leave', 'tdy', 'out']):
            return self._handle_leave_notification(personnel, body)
        elif any(word in body_lower for word in ['help', 'commands']):
            return self._get_help_message(personnel)
        else:
            return self._handle_general_message(personnel, body)
    
    def _handle_appointment_request(self, personnel: Dict, message: str) -> str:
        """Handle appointment scheduling request"""
        # Parse appointment details from message
        appointment_info = self._parse_appointment_details(message)
        
        if not appointment_info['date']:
            return f"Hi {personnel['rank']} {personnel['last_name']}, please specify a date for your appointment. Example: 'Schedule appointment tomorrow at 1400 for ID card'"
        
        # Create appointment
        try:
            apt_id = self.db.create_appointment(
                personnel_id=personnel['id'],
                absence_type=appointment_info['type'],
                appointment_date=appointment_info['date'],
                start_time=appointment_info['start_time'],
                end_time=appointment_info['end_time'],
                notes=f"Requested via SMS: {message[:100]}",
                all_day=False
            )
            
            return f"✓ Appointment confirmed for {appointment_info['date']} at {appointment_info['start_time'] or 'TBD'}. Type: {appointment_info['type']}. Reply CANCEL to cancel."
        except Exception as e:
            return f"Unable to schedule appointment: {str(e)}. Please call the CS section."
    
    def _handle_appointment_change(self, personnel: Dict, message: str) -> str:
        """Handle appointment cancellation or rescheduling"""
        # Get active appointments for this person
        appointments = self.db.get_personnel_appointments(personnel['id'])
        active_apts = [a for a in appointments if a['status'] == 'active']
        
        if not active_apts:
            return f"{personnel['rank']} {personnel['last_name']}, you have no active appointments to modify."
        
        if 'cancel' in message.lower():
            # Cancel most recent appointment (update status to cancelled)
            latest_apt = active_apts[0]
            with self.db.transaction() as conn:
                conn.execute("""
                    UPDATE appointments 
                    SET status = 'cancelled' 
                    WHERE id = ?
                """, (latest_apt['id'],))
            return f"✓ Your appointment on {latest_apt['appointment_date']} has been cancelled."
        else:
            return "To cancel an appointment, reply CANCEL. To reschedule, please call the CS section."
    
    def _handle_status_query(self, personnel: Dict) -> str:
        """Handle status query"""
        status = personnel['status']
        status_map = {
            'front_desk': 'at the Front Desk',
            'admin_room': 'in the Admin Room',
            'terminal': 'at a Terminal',
            'float': 'Floating (available for tasking)',
            'leave': 'on Leave',
            'appointment': 'at an Appointment'
        }
        
        return f"{personnel['rank']} {personnel['last_name']}, you are currently marked as {status_map.get(status, status)}."
    
    def _handle_leave_notification(self, personnel: Dict, message: str) -> str:
        """Handle leave/TDY notification"""
        # Parse dates from message
        date_info = self._parse_date_range(message)
        
        if date_info['start_date']:
            # Update status to leave
            self.db.update_personnel_status(personnel['id'], 'leave')
            
            # Create leave appointment
            self.db.create_appointment(
                personnel_id=personnel['id'],
                absence_type='Leave/TDY',
                appointment_date=date_info['start_date'],
                end_time=date_info['end_date'],
                all_day=True,
                notes=f"Notified via SMS: {message[:100]}"
            )
            
            return f"✓ Leave recorded from {date_info['start_date']} to {date_info['end_date'] or 'TBD'}. Have a safe trip!"
        else:
            return "Please specify your leave dates. Example: 'On leave from Dec 20 to Jan 3'"
    
    def _handle_general_message(self, personnel: Dict, message: str) -> str:
        """Handle general/unrecognized messages"""
        return f"Hi {personnel['rank']} {personnel['last_name']}, message received. Reply HELP for available commands or call the CS section for assistance."
    
    def _get_help_message(self, personnel: Dict) -> str:
        """Return help message with available commands"""
        return f"""CS SMS Commands:
• APPOINTMENT [date] [type] - Schedule appointment
• CANCEL - Cancel latest appointment
• STATUS - Check your current location
• LEAVE [dates] - Report leave/TDY
• HELP - Show this message

Examples:
"Appointment tomorrow 2pm ID card"
"On leave Dec 20-27"
"Cancel appointment"
"""
    
    def _parse_appointment_details(self, message: str) -> Dict:
        """Parse appointment details from message text"""
        result = {
            'date': None,
            'start_time': None,
            'end_time': None,
            'type': 'General'
        }
        
        # Parse date (tomorrow, Monday, Dec 20, etc.)
        message_lower = message.lower()
        today = datetime.now()
        
        if 'tomorrow' in message_lower:
            result['date'] = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'today' in message_lower:
            result['date'] = today.strftime('%Y-%m-%d')
        else:
            # Try to extract date patterns
            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})', message)
            if date_match:
                month, day = date_match.groups()
                year = today.year
                if int(month) < today.month:
                    year += 1
                result['date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Parse time
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm|[ap]\.m\.)?|\b(\d{1,2})\s*(am|pm|[ap]\.m\.)', message_lower)
        if time_match:
            groups = time_match.groups()
            if groups[3]:  # Format: "2pm"
                hour = int(groups[3])
                minute = '00'
                period = groups[4]
            else:  # Format: "2:30pm" or "14:30"
                hour = int(groups[0])
                minute = groups[1] or '00'
                period = groups[2]
            
            if period and 'p' in period and hour < 12:
                hour += 12
            elif period and 'a' in period and hour == 12:
                hour = 0
            
            result['start_time'] = f"{hour:02d}:{minute}"
            # Default to 1-hour appointment
            end_hour = hour + 1
            result['end_time'] = f"{end_hour:02d}:{minute}"
        
        # Parse appointment type
        types = {
            'id': 'ID Card',
            'cac': 'CAC/ID Card',
            'record': 'Records',
            'travel': 'Travel/DTS',
            'dts': 'Travel/DTS',
            'leave': 'Leave/LeaveWeb',
            'leaveweb': 'Leave/LeaveWeb',
            'medical': 'Medical',
            'dental': 'Dental',
            'finance': 'Finance',
            'mpf': 'MPF'
        }
        
        for keyword, apt_type in types.items():
            if keyword in message_lower:
                result['type'] = apt_type
                break
        
        return result
    
    def _parse_date_range(self, message: str) -> Dict:
        """Parse date range from message"""
        result = {'start_date': None, 'end_date': None}
        
        # Look for date patterns
        today = datetime.now()
        message_lower = message.lower()
        
        # Simple patterns
        if 'tomorrow' in message_lower:
            result['start_date'] = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'next week' in message_lower:
            result['start_date'] = (today + timedelta(days=7)).strftime('%Y-%m-%d')
            result['end_date'] = (today + timedelta(days=14)).strftime('%Y-%m-%d')
        
        # Date range pattern (Dec 20-27, 12/20 to 12/27, etc.)
        range_match = re.search(r'(\d{1,2})[/-](\d{1,2})\s*(?:to|-)\s*(\d{1,2})[/-]?(\d{1,2})?', message)
        if range_match:
            groups = range_match.groups()
            start_month, start_day = int(groups[0]), int(groups[1])
            
            if groups[3]:  # Full end date
                end_month, end_day = int(groups[2]), int(groups[3])
            else:  # Just end day
                end_month = start_month
                end_day = int(groups[2])
            
            year = today.year
            if start_month < today.month:
                year += 1
            
            result['start_date'] = f"{year}-{start_month:02d}-{start_day:02d}"
            result['end_date'] = f"{year}-{end_month:02d}-{end_day:02d}"
        
        return result
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS via Twilio"""
        if not self.client:
            print(f"Twilio client not initialized. Would send to {to_number}: {message}")
            return False
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=to_number
            )
            print(f"SMS sent successfully. SID: {message.sid}")
            return True
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return False
    
    def handle_webhook(self, request_form) -> str:
        """Handle Twilio webhook request and return TwiML response"""
        # Extract message details from Twilio webhook
        from_number = request_form.get('From', '')
        body = request_form.get('Body', '')
        message_sid = request_form.get('MessageSid', '')
        
        # Process the message
        response_text = self.process_incoming_sms(from_number, body, message_sid)
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        
        return str(resp)