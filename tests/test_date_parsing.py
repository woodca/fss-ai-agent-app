#!/usr/bin/env python3

from gpt_parser import GPTParser
from datetime import datetime
import json

def test_date_parsing():
    """Test date parsing with current date context"""
    
    try:
        parser = GPTParser()
        print("Testing date parsing with current date context...\n")
        print(f"Current date: {datetime.now().strftime('%A, %B %d, %Y')}\n")
        
        # Test messages with relative dates
        test_messages = [
            {
                'phone_number': '+14408293193',
                'message_text': 'Dental appointment tomorrow at 1400',
                'id': 'date_test1'
            },
            {
                'phone_number': '+14408293193', 
                'message_text': 'Medical appt Monday 1pm-3pm',
                'id': 'date_test2'
            },
            {
                'phone_number': '+14408293193',
                'message_text': 'Personal business today at 0900',
                'id': 'date_test3'
            },
            {
                'phone_number': '+14408293193',
                'message_text': 'Leave next Friday all day',
                'id': 'date_test4'
            }
        ]
        
        for i, msg in enumerate(test_messages, 1):
            print(f"Test {i}: {msg['message_text']}")
            
            try:
                result = parser.process_message(msg)
                
                if result.get('status') == 'processed':
                    analysis = result.get('gpt_analysis', {})
                    print(f"   Status: Processed")
                    print(f"   Date parsed: {analysis.get('appointment_date')}")
                    print(f"   Time: {analysis.get('start_time')}")
                    print(f"   Type: {analysis.get('absence_type')}")
                else:
                    print(f"   Status: Error - {result.get('error')}")
                    
            except Exception as e:
                print(f"   Error: {e}")
            
            print()
        
        # Show what dates were actually stored
        print("Stored appointments with corrected dates:")
        recent_appointments = [apt for apt in parser.appointments if 'date_test' in apt.get('original_message_id', '')]
        
        for apt in recent_appointments:
            print(f"   - {apt.get('personnel_name')}: {apt.get('absence_type')} on {apt.get('appointment_date')} at {apt.get('start_time')}")
            print(f"     Original: \"{apt.get('original_text')}\"")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_date_parsing()