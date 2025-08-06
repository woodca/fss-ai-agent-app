#!/usr/bin/env python3

import json
import os
from datetime import datetime, timedelta
import pytz

class CalendarManager:
    def __init__(self):
        self.appointments_file = 'appointments.json'
        self.personnel_file = 'personnel_assignments.json'
        self.eastern = pytz.timezone('US/Eastern')
        
        # Load data
        self.appointments = self._load_json_file(self.appointments_file, [])
        self.personnel = self._load_json_file(self.personnel_file, [])
        
        # Cache valid personnel names for quick lookup
        self.valid_personnel_names = {person['name'] for person in self.personnel}
        
    def _load_json_file(self, filename, default):
        """Load JSON file or return default if file doesn't exist"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return default
    
    def _save_json_file(self, filename, data):
        """Save data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def validate_and_clean_appointments(self):
        """Remove appointments without valid personnel names and add categories"""
        valid_appointments = []
        removed_count = 0
        
        for appointment in self.appointments:
            personnel_name = appointment.get('personnel_name')
            category = appointment.get('category', self._determine_category(appointment))
            
            # Events don't need valid personnel names (they're squadron-wide)
            if category == 'event':
                appointment['category'] = category
                valid_appointments.append(appointment)
            # Appointments and leave need valid personnel names
            elif personnel_name and personnel_name in self.valid_personnel_names:
                appointment['category'] = category
                valid_appointments.append(appointment)
            else:
                print(f"Removing invalid appointment: {personnel_name or 'NULL'} not found in roster")
                removed_count += 1
        
        print(f"Validation complete: {removed_count} invalid appointments removed")
        self.appointments = valid_appointments
        self._save_json_file(self.appointments_file, self.appointments)
        
        return removed_count
    
    def _determine_category(self, appointment):
        """Determine calendar category based on absence_type"""
        absence_type = appointment.get('absence_type', '').lower()
        
        if absence_type == 'leave':
            return 'leave'
        elif absence_type in ['medical', 'dental', 'personal_business', 'other']:
            return 'appointment'
        else:
            # Default to appointment for unknown types
            return 'appointment'
    
    def add_event(self, title, date, start_time=None, end_time=None, all_day=False):
        """Add a squadron-wide event"""
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        event = {
            'id': event_id,
            'category': 'event',
            'title': title,
            'appointment_date': date,
            'start_time': start_time,
            'end_time': end_time,
            'all_day': all_day,
            'personnel_name': None,  # Events don't belong to specific personnel
            'absence_type': 'event',
            'status': 'active',
            'created_timestamp': datetime.now().isoformat(),
            'created_by': 'calendar_manager'
        }
        
        self.appointments.append(event)
        self._save_json_file(self.appointments_file, self.appointments)
        return event
    
    def get_current_time_eastern(self):
        """Get current time in Eastern timezone"""
        return datetime.now(self.eastern)
    
    def should_personnel_be_at_appointment(self, personnel_name, current_time=None):
        """Check if personnel should currently be at an appointment"""
        if current_time is None:
            current_time = self.get_current_time_eastern()
        
        current_date = current_time.strftime('%Y-%m-%d')
        current_time_str = current_time.strftime('%H%M')
        
        for appointment in self.appointments:
            if (appointment.get('personnel_name') == personnel_name and 
                appointment.get('appointment_date') == current_date and
                appointment.get('status') == 'active'):
                
                # Check if it's a leave day (all day)
                if (appointment.get('category') == 'leave' or 
                    appointment.get('absence_type') == 'leave' or 
                    appointment.get('all_day')):
                    # Return 'leave' for leave appointments, 'appointment' for others
                    if (appointment.get('category') == 'leave' or 
                        appointment.get('absence_type') == 'leave'):
                        return 'leave'
                    else:
                        return 'appointment'
                
                # Check if currently within appointment time
                start_time = appointment.get('start_time')
                end_time = appointment.get('end_time')
                
                if start_time:
                    if end_time:
                        # Has both start and end time
                        if start_time <= current_time_str <= end_time:
                            return 'appointment'
                    else:
                        # Only has start time, assume 1 hour duration
                        start_datetime = datetime.strptime(f"{current_date} {start_time}", '%Y-%m-%d %H%M')
                        end_datetime = start_datetime + timedelta(hours=1)
                        
                        if start_datetime <= current_time.replace(tzinfo=None) <= end_datetime:
                            return 'appointment'
        
        return None
    
    def should_personnel_be_on_leave(self, personnel_name, current_date=None):
        """Check if personnel should be on leave for the given date"""
        if current_date is None:
            current_date = self.get_current_time_eastern().strftime('%Y-%m-%d')
        
        for appointment in self.appointments:
            if (appointment.get('personnel_name') == personnel_name and
                (appointment.get('category') == 'leave' or appointment.get('absence_type') == 'leave') and
                appointment.get('status') == 'active'):
                
                start_date = appointment.get('appointment_date')
                end_date = appointment.get('end_date', start_date)  # Default to single day
                
                if start_date <= current_date <= end_date:
                    return True
        
        return False
    
    def update_personnel_statuses(self):
        """Update all personnel statuses based on current appointments"""
        current_time = self.get_current_time_eastern()
        updates_made = []
        
        for person in self.personnel:
            personnel_name = person['name']
            current_status = person['status']
            
            # Check if should be on leave
            if self.should_personnel_be_on_leave(personnel_name):
                if current_status != 'leave':
                    person['status'] = 'leave'
                    person['last_updated'] = datetime.now().isoformat()
                    updates_made.append(f"{personnel_name}: {current_status} → leave")
            
            # Check if should be at appointment
            elif self.should_personnel_be_at_appointment(personnel_name, current_time):
                appointment_status = self.should_personnel_be_at_appointment(personnel_name, current_time)
                if current_status != appointment_status:
                    person['status'] = appointment_status
                    person['last_updated'] = datetime.now().isoformat()
                    updates_made.append(f"{personnel_name}: {current_status} → {appointment_status}")
            
            # If not on leave or appointment, keep their work assignment status
            # (don't automatically change back - let manual updates handle work assignments)
        
        if updates_made:
            self._save_json_file(self.personnel_file, self.personnel)
            print(f"Status updates made: {len(updates_made)} changes")
        
        return updates_made
    
    def get_calendar_events(self, start_date=None, end_date=None):
        """Get all calendar events for a date range"""
        if start_date is None:
            start_date = self.get_current_time_eastern().strftime('%Y-%m-%d')
        
        if end_date is None:
            end_date = (self.get_current_time_eastern() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        events = []
        
        for appointment in self.appointments:
            if appointment.get('status') != 'active':
                continue
                
            appointment_date = appointment.get('appointment_date')
            if start_date <= appointment_date <= end_date:
                events.append(appointment)
        
        return sorted(events, key=lambda x: (x.get('appointment_date', ''), x.get('start_time') or '0000'))
    
    def get_events_by_category(self, start_date=None, end_date=None):
        """Get events grouped by category with color coding"""
        events = self.get_calendar_events(start_date, end_date)
        
        categorized = {
            'appointment': {'color': '#007bff', 'events': []},  # Blue
            'leave': {'color': '#28a745', 'events': []},        # Green  
            'event': {'color': '#6f42c1', 'events': []}         # Purple
        }
        
        for event in events:
            category = event.get('category', 'appointment')
            if category in categorized:
                categorized[category]['events'].append(event)
        
        return categorized

if __name__ == "__main__":
    # Test the calendar manager
    calendar = CalendarManager()
    
    print("Validating and cleaning appointments...")
    removed = calendar.validate_and_clean_appointments()
    
    print("Updating personnel statuses...")
    updates = calendar.update_personnel_statuses()
    
    print("Getting upcoming events...")
    events = calendar.get_events_by_category()
    
    for category, data in events.items():
        print(f"\n{category.upper()} ({data['color']}):")
        for event in data['events'][:5]:  # Show first 5
            print(f"  - {event.get('personnel_name', 'Squadron')}: {event.get('appointment_date')} {event.get('start_time', 'All Day')}")