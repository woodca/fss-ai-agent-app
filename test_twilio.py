#!/usr/bin/env python3
"""
Test script for Twilio SMS integration
Tests the handler without actually sending SMS messages
"""

import os
from twilio_handler import TwilioHandler
from database_manager import DatabaseManager

def test_twilio_handler():
    """Test Twilio handler with various scenarios"""
    
    print("=" * 50)
    print("TWILIO SMS HANDLER TEST")
    print("=" * 50)
    
    # Initialize handler
    handler = TwilioHandler()
    db = DatabaseManager()
    
    # Test scenarios
    test_cases = [
        {
            "name": "A1C Gauci - Appointment Request",
            "phone": "+18038690528",
            "message": "Appointment tomorrow 1400 ID card",
            "sid": "TEST001"
        },
        {
            "name": "SSgt Woodley - Status Check",
            "phone": "+18034093219",
            "message": "STATUS",
            "sid": "TEST002"
        },
        {
            "name": "TSgt Smith - Leave Notification",
            "phone": "+18038037111",
            "message": "On leave Dec 20-27",
            "sid": "TEST003"
        },
        {
            "name": "Unknown Number",
            "phone": "+15555551234",
            "message": "Need appointment",
            "sid": "TEST004"
        },
        {
            "name": "A1C Gauci - Help Request",
            "phone": "+18038690528",
            "message": "HELP",
            "sid": "TEST005"
        },
        {
            "name": "A1C Gauci - Cancel Appointment",
            "phone": "+18038690528",
            "message": "Cancel appointment",
            "sid": "TEST006"
        }
    ]
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"From: {test['phone']}")
        print(f"Message: {test['message']}")
        print("-" * 30)
        
        response = handler.process_incoming_sms(
            from_number=test['phone'],
            body=test['message'],
            message_sid=test['sid']
        )
        
        print(f"Response: {response}")
        print("=" * 50)
    
    # Show current appointments
    print("\n" + "=" * 50)
    print("CURRENT APPOINTMENTS IN DATABASE")
    print("=" * 50)
    
    appointments = db.get_calendar_events()
    for apt in appointments[:5]:  # Show first 5
        if apt['event_type'] == 'appointment':
            print(f"- {apt['title']} on {apt['start']}")

def check_twilio_credentials():
    """Check if Twilio credentials are configured"""
    print("\n" + "=" * 50)
    print("TWILIO CONFIGURATION CHECK")
    print("=" * 50)
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone = os.getenv('TWILIO_PHONE_NUMBER', '+18134381333')
    
    print(f"Account SID: {'✓ Configured' if account_sid else '✗ Missing'}")
    print(f"Auth Token: {'✓ Configured' if auth_token else '✗ Missing'}")
    print(f"Phone Number: {phone}")
    
    if not account_sid or not auth_token:
        print("\n⚠️  Add these to your .env file:")
        print("TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        print("TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        print("TWILIO_PHONE_NUMBER=+18134381333")
        print("\nGet these from: https://console.twilio.com")
    else:
        print("\n✅ Twilio credentials configured!")
        print("Ready to send and receive SMS messages.")

def test_phone_lookup():
    """Test phone number lookup for all personnel"""
    print("\n" + "=" * 50)
    print("PERSONNEL PHONE NUMBER VERIFICATION")
    print("=" * 50)
    
    db = DatabaseManager()
    handler = TwilioHandler()
    
    personnel = db.get_all_personnel()
    
    for person in personnel:
        phone = person.get('phone')
        if phone:
            verified = handler.verify_personnel_by_phone(phone)
            status = "✓" if verified else "✗"
            print(f"{status} {person['name']}: {phone}")
        else:
            print(f"✗ {person['name']}: No phone number")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    check_twilio_credentials()
    test_phone_lookup()
    test_twilio_handler()
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Add Twilio credentials to .env file")
    print("2. Deploy to Railway")
    print("3. Configure webhook in Twilio Console")
    print("4. Test with real SMS to (813) 438-1333")