#!/usr/bin/env python3
"""
Production Testing Script for Twilio SMS Integration
Comprehensive tests to validate SMS functionality on Railway deployment
"""

import os
import requests
import json
from datetime import datetime

class TwilioProductionTester:
    def __init__(self, base_url="https://fssagent.com"):
        self.base_url = base_url
        self.webhook_url = f"{base_url}/api/twilio/sms"
        
    def test_webhook_endpoint(self):
        """Test if webhook endpoint is accessible"""
        print("WEBHOOK ENDPOINT TEST")
        print("=" * 50)
        
        try:
            # Test GET request (should return 405 Method Not Allowed)
            response = requests.get(self.webhook_url, timeout=10)
            print(f"GET {self.webhook_url}: {response.status_code}")
            
            if response.status_code == 405:
                print("✅ Endpoint exists (correct 405 for GET on POST-only endpoint)")
            elif response.status_code == 404:
                print("❌ Endpoint not found - check deployment")
            else:
                print(f"⚠️  Unexpected status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
            
        return True
    
    def simulate_twilio_webhook(self, test_phone="+15551234567", test_message="test status"):
        """Simulate a Twilio webhook POST request"""
        print("\nTWILIO WEBHOOK SIMULATION")
        print("=" * 50)
        
        # Simulate Twilio webhook payload
        webhook_data = {
            'From': test_phone,
            'To': '+18134381333',
            'Body': test_message,
            'MessageSid': f'SM{datetime.now().strftime("%Y%m%d%H%M%S")}test',
            'AccountSid': 'AC_test_account',
            'MessagingServiceSid': '',
            'NumMedia': '0',
            'NumSegments': '1',
            'SmsStatus': 'received',
            'SmsMessageSid': f'SM{datetime.now().strftime("%Y%m%d%H%M%S")}test'
        }
        
        print(f"Simulating webhook with data: {json.dumps(webhook_data, indent=2)}")
        
        try:
            response = requests.post(
                self.webhook_url,
                data=webhook_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=15
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response content: {response.text[:500]}...")
            
            # Check if response is valid TwiML
            if response.status_code == 200:
                if 'text/xml' in response.headers.get('content-type', ''):
                    print("✅ Valid TwiML response received")
                    
                    # Check if TwiML contains a message
                    if '<Message>' in response.text:
                        print("✅ TwiML contains reply message")
                    else:
                        print("⚠️  TwiML response has no message content")
                else:
                    print("⚠️  Response not in XML format")
                    
                return True
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def test_personnel_authentication(self):
        """Test different phone number formats for personnel lookup"""
        print("\nPERSONNEL AUTHENTICATION TEST")
        print("=" * 50)
        
        # Test with various phone formats
        test_phones = [
            "+15551234567",  # Full international
            "15551234567",   # No plus
            "5551234567",    # No country code
            "(555) 123-4567", # Formatted
            "555-123-4567"   # Dashed
        ]
        
        for phone in test_phones:
            print(f"\nTesting phone: {phone}")
            success = self.simulate_twilio_webhook(phone, "status")
            print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    def test_command_variations(self):
        """Test different SMS command variations"""
        print("\nCOMMAND VARIATIONS TEST")
        print("=" * 50)
        
        test_commands = [
            "status",
            "STATUS",
            "where am I",
            "appointment tomorrow 2pm",
            "schedule appt monday 1400 ID card",
            "cancel appointment",
            "help",
            "HELP",
            "leave dec 20-27",
            "on tdy next week",
            "random message that should trigger general handler"
        ]
        
        for command in test_commands:
            print(f"\n📱 Testing: '{command}'")
            success = self.simulate_twilio_webhook("+15551234567", command)
            print(f"   {'✅ Processed' if success else '❌ Failed'}")
    
    def check_railway_logs(self):
        """Instructions for checking Railway deployment logs"""
        print("\nRAILWAY LOGS CHECK")
        print("=" * 50)
        print("To check production logs:")
        print("1. Go to https://railway.app/")
        print("2. Select your fssagent project")
        print("3. Click on your service")
        print("4. Go to 'Logs' tab")
        print("5. Look for:")
        print("   - '🔄 Twilio webhook received'")
        print("   - '✅ TwilioHandler client ready'")
        print("   - '❌ TwilioHandler client not initialized'")
        print("   - Any credential-related errors")
        print("   - SMS sending attempts and results")
        print()
        print("Alternative - Railway CLI:")
        print("railway logs --service=<your-service-name>")
    
    def environment_check(self):
        """Check expected environment configuration"""
        print("\nENVIRONMENT CONFIGURATION CHECK")
        print("=" * 50)
        
        required_env = [
            ('TWILIO_ACCOUNT_SID', 'SK24ff5e025086c2314f64aca2694e92d0'),
            ('TWILIO_AUTH_TOKEN', '0ce46917d95963bedf8f80bbe91e1c36'),
            ('TWILIO_PHONE_NUMBER', '+18134381333')
        ]
        
        print("Expected Railway environment variables:")
        for var_name, expected_value in required_env:
            if var_name == 'TWILIO_AUTH_TOKEN':
                print(f"   {var_name} = {expected_value[:8]}{'*' * (len(expected_value)-8)}")
            else:
                print(f"   {var_name} = {expected_value}")
        
        print("\nNote: The ACCOUNT_SID starting with 'SK' indicates API Key format")
        print("The updated TwilioHandler should handle this correctly now.")
    
    def run_all_tests(self):
        """Run all production tests"""
        print("TWILIO PRODUCTION TESTING SUITE")
        print("=" * 60)
        print(f"Target URL: {self.base_url}")
        print(f"Webhook: {self.webhook_url}")
        print("=" * 60)
        
        # Run tests
        self.environment_check()
        endpoint_ok = self.test_webhook_endpoint()
        
        if endpoint_ok:
            self.simulate_twilio_webhook()
            self.test_personnel_authentication()
            self.test_command_variations()
        
        self.check_railway_logs()
        
        print("\n" + "=" * 60)
        print("PRODUCTION TESTING COMPLETE")
        print("Next steps:")
        print("1. Check Railway logs for detailed error information")
        print("2. Test with real SMS to verify end-to-end functionality")
        print("3. Monitor webhook responses for TwiML format issues")
        
def main():
    """Run production tests"""
    tester = TwilioProductionTester()
    tester.run_all_tests()

if __name__ == '__main__':
    main()