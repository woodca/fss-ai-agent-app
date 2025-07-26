#!/usr/bin/env python3

from gpt_parser import GPTParser
import json

def test_message_parsing():
    """Test Claude API parsing with sample troop messages"""
    
    try:
        parser = GPTParser()
        print("Testing Claude API message parsing...\n")
        
        # Sample messages troops might send
        test_messages = [
            {
                'phone_number': '+1234567890',
                'message_text': 'Dental appointment Monday at 1300',
                'id': 'test1'
            },
            {
                'phone_number': '+1234567891', 
                'message_text': 'Medical appt tomorrow 1pm-3pm',
                'id': 'test2'
            },
            {
                'phone_number': '+1234567892',
                'message_text': 'Personal business Friday 0900 for 2 hours',
                'id': 'test3'
            },
            {
                'phone_number': '+1234567893',
                'message_text': 'Leave all day Thursday',
                'id': 'test4'
            },
            {
                'phone_number': '+1234567894',
                'message_text': 'Hey sergeant, how are you doing?',
                'id': 'test5'
            }
        ]
        
        for i, msg in enumerate(test_messages, 1):
            print(f"Test {i}: {msg['message_text']}")
            print(f"   From: {msg['phone_number']}")
            
            try:
                result = parser.process_message(msg)
                
                if result.get('status') == 'processed':
                    analysis = result.get('gpt_analysis', {})
                    print(f"   Status: Processed")
                    print(f"   Analysis:")
                    for key, value in analysis.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"   Status: Error - {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"   Error: {e}")
            
            print()
        
        # Show current appointments and contacts
        print("Current Appointments:")
        appointments = parser.get_pending_appointments()
        for apt in appointments:
            print(f"   - {apt.get('id')} - {apt.get('phone_number')}")
            print(f"     Type: {apt.get('service_type')}")
            print(f"     Time: {apt.get('preferred_datetime')}")
            print()
        
        print(f"Total Contacts: {len(parser.contacts)}")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_message_parsing()