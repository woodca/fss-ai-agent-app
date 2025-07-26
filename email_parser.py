import os
import json
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import re
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class EmailParser:
    def __init__(self, credentials_path='credentials.json', token_path='token.pickle'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.processed_messages_file = 'processed_messages.json'
        self.processed_messages = self._load_processed_messages()
    
    def _load_processed_messages(self):
        """Load the list of already processed message IDs"""
        try:
            with open(self.processed_messages_file, 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()
    
    def _save_processed_messages(self):
        """Save the list of processed message IDs"""
        with open(self.processed_messages_file, 'w') as f:
            json.dump(list(self.processed_messages), f)
    
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def get_google_voice_messages(self, max_results=10):
        """Retrieve Google Voice messages from Gmail"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Search for messages from Google Voice
            query = 'from:txt.voice.google.com OR from:voice-noreply@google.com'
            result = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = result.get('messages', [])
            parsed_messages = []
            
            for message in messages:
                msg_id = message['id']
                
                # Skip if already processed
                if msg_id in self.processed_messages:
                    continue
                
                # Get full message details
                msg = self.service.users().messages().get(
                    userId='me', id=msg_id, format='full'
                ).execute()
                
                parsed_msg = self._parse_google_voice_message(msg)
                if parsed_msg:
                    parsed_messages.append(parsed_msg)
                    self.processed_messages.add(msg_id)
            
            # Save updated processed messages
            self._save_processed_messages()
            return parsed_messages
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def _parse_google_voice_message(self, message):
        """Parse a Google Voice message from Gmail"""
        try:
            headers = message['payload'].get('headers', [])
            subject = ''
            sender = ''
            date = ''
            
            # Extract headers
            for header in headers:
                name = header.get('name', '').lower()
                value = header.get('value', '')
                
                if name == 'subject':
                    subject = value
                elif name == 'from':
                    sender = value
                elif name == 'date':
                    date = value
            
            # Extract message body
            body = self._extract_message_body(message['payload'])
            
            # Parse Google Voice specific information
            phone_number = self._extract_phone_number(subject, body)
            message_text = self._extract_message_text(body)
            
            if not message_text:
                return None
            
            return {
                'id': message['id'],
                'phone_number': phone_number,
                'message_text': message_text,
                'subject': subject,
                'sender': sender,
                'date': date,
                'timestamp': datetime.now().isoformat(),
                'raw_body': body
            }
            
        except Exception as e:
            print(f'Error parsing message: {e}')
            return None
    
    def _extract_message_body(self, payload):
        """Extract the message body from Gmail payload"""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        elif payload['mimeType'] == 'text/plain':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def _extract_phone_number(self, subject, body):
        """Extract phone number from Google Voice message"""
        # Google Voice usually includes phone number in subject like "SMS from +1234567890"
        phone_match = re.search(r'\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})', subject + ' ' + body)
        if phone_match:
            return f"+1{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"
        return "Unknown"
    
    def _extract_message_text(self, body):
        """Extract the actual text message content from Google Voice email"""
        # Google Voice emails typically have the message after certain markers
        lines = body.split('\n')
        
        # Look for the actual message content (usually after some Google Voice formatting)
        message_text = ''
        found_voice_header = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Look for Google Voice header patterns
            if 'voice.google.com' in line.lower():
                found_voice_header = True
                continue
            
            # After finding the header, look for the message content
            if found_voice_header:
                # Skip URLs and common Google Voice text
                if any(skip in line.lower() for skip in ['http', 'voice.google.com', 'your account', 'help center', 'support.google']):
                    continue
                
                # Skip very short lines (likely formatting)
                if len(line) < 5:
                    continue
                
                # IMPORTANT: Skip lines that are clearly email footer content
                if any(footer in line.lower() for footer in [
                    'this email was sent', 'email notifications', 'notification settings',
                    'if you don\'t want to receive', 'update your email', 'google llc',
                    'mountain view', 'amphitheatre pkwy'
                ]):
                    continue
                
                # This should be the actual message - collect multiple lines if needed
                if len(line) > 5 and not line.startswith('<'):
                    message_lines = [line]
                    
                    # Look ahead for continuation lines
                    for j in range(i + 1, min(i + 3, len(lines))):  # Check next 2 lines
                        next_line = lines[j].strip()
                        if (next_line and 
                            len(next_line) > 5 and 
                            not next_line.startswith('<') and
                            not any(skip in next_line.lower() for skip in ['http', 'voice.google.com', 'your account', 'help center', 'support.google']) and
                            not any(footer in next_line.lower() for footer in [
                                'this email was sent', 'email notifications', 'notification settings',
                                'if you don\'t want to receive', 'update your email', 'google llc'
                            ])):
                            message_lines.append(next_line)
                        else:
                            break
                    
                    message_text = ' '.join(message_lines)
                    break
        
        # Fallback: If no specific pattern found, try to find meaningful content
        if not message_text:
            meaningful_lines = []
            for line in lines:
                line = line.strip()
                # Skip obvious non-message content including email footer text
                if (len(line) > 10 and 
                    not any(skip in line.lower() for skip in ['http', 'google', 'voice', 'reply', 'unsubscribe', 'account', 'help', 'support']) and
                    not any(footer in line.lower() for footer in [
                        'this email was sent', 'email notifications', 'notification settings',
                        'if you don\'t want to receive', 'update your email', 'google llc',
                        'mountain view', 'amphitheatre pkwy'
                    ]) and
                    not line.startswith('<') and
                    not line.startswith('=')):
                    meaningful_lines.append(line)
            
            if meaningful_lines:
                # Take the first meaningful line that looks like a message
                message_text = meaningful_lines[0]
        
        return message_text.strip()
