#!/usr/bin/env python3

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

class GoogleVoiceResponder:
    """
    Handle sending responses back through Google Voice via Gmail
    Since Google Voice forwards messages to Gmail, we can send responses
    by sending emails to the Google Voice email gateway
    """
    
    def __init__(self):
        self.gmail_user = os.getenv('GMAIL_USER')  # Your Gmail address
        self.gmail_password = os.getenv('GMAIL_APP_PASSWORD')  # App-specific password
        
        if not self.gmail_user or not self.gmail_password:
            print("⚠️  Warning: Gmail credentials not found in environment variables")
            print("   Set GMAIL_USER and GMAIL_APP_PASSWORD to enable response sending")
    
    def send_response(self, recipient_phone, message):
        """
        Send a response message to a phone number via Google Voice
        
        Args:
            recipient_phone (str): Phone number to send to
            message (str): Message content to send
        """
        try:
            if not self.gmail_user or not self.gmail_password:
                # Just log the response for now
                print(f"📱 Response to {recipient_phone}: {message}")
                return {'success': True, 'method': 'logged', 'message': message}
            
            # Format the Google Voice email address
            # Google Voice uses: [your_google_voice_number]@txt.voice.google.com
            # But for responses, we need to use a different approach
            
            # For now, we'll implement a simple email notification system
            # In production, you'd integrate with Google Voice API or SMS gateway
            
            subject = f"Vera Response to {recipient_phone}"
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = self.gmail_user  # Send to yourself for now
            msg['Subject'] = subject
            
            # Email body with response details
            body = f"""
Vera Response
====================

To: {recipient_phone}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Message:
{message}

---
This is an automated response from the Vera system.
In production, this would be sent directly to the recipient via Google Voice.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            text = msg.as_string()
            server.sendmail(self.gmail_user, self.gmail_user, text)
            server.quit()
            
            print(f"📧 Email notification sent for response to {recipient_phone}")
            
            return {
                'success': True,
                'method': 'email_notification',
                'message': message,
                'recipient': recipient_phone
            }
            
        except Exception as e:
            print(f"❌ Error sending response: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': message,
                'recipient': recipient_phone
            }
    
    def send_clarification_question(self, recipient_phone, question):
        """
        Send a clarification question back to the sender
        
        Args:
            recipient_phone (str): Phone number to send to
            question (str): Clarification question to ask
        """
        clarification_message = f"🤖 Vera:\n\n{question}\n\nPlease reply with more details."
        
        return self.send_response(recipient_phone, clarification_message)
    
    def send_status_confirmation(self, recipient_phone, person_name, updates_made):
        """
        Send confirmation of status update
        
        Args:
            recipient_phone (str): Phone number to send to
            person_name (str): Name of person updated
            updates_made (list): List of updates made
        """
        updates_text = " and ".join(updates_made)
        confirmation_message = f"✅ Updated {person_name}'s {updates_text}."
        
        return self.send_response(recipient_phone, confirmation_message)


# Test function
def test_responder():
    """Test the Google Voice responder"""
    print("🤖 Testing Google Voice Responder\n")
    
    responder = GoogleVoiceResponder()
    
    # Test responses
    test_cases = [
        {
            'phone': '555-123-4567',
            'message': '✅ Updated A1C Davis\'s assignment to terminal.'
        },
        {
            'phone': '555-123-4568', 
            'message': '🤖 Vera:\n\nI couldn\'t find "Johnson" in our roster. Did you mean one of these people?\nTSgt Johnson\nSSgt Martinez\n\nPlease reply with more details.'
        }
    ]
    
    for test in test_cases:
        print(f"Sending to {test['phone']}:")
        print(f"Message: {test['message']}\n")
        
        result = responder.send_response(test['phone'], test['message'])
        
        if result.get('success'):
            print(f"✅ Response sent successfully via {result.get('method')}")
        else:
            print(f"❌ Failed to send response: {result.get('error')}")
        
        print("-" * 50)


if __name__ == "__main__":
    from datetime import datetime
    test_responder()