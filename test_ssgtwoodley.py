#!/usr/bin/env python3

from gpt_parser import GPTParser
import json

def test_ssgtwoodley_message():
    """Test with SSgt Woodley's actual phone number"""
    
    try:
        parser = GPTParser()
        print("Testing with SSgt Woodley's information...\n")
        
        # Test message from SSgt Woodley
        test_message = {
            'phone_number': '+14408293193',
            'message_text': 'Dental appointment tomorrow at 1400',
            'id': 'woodley_test_1'
        }
        
        print(f"Processing message from: {test_message['phone_number']}")
        print(f"Message: {test_message['message_text']}")
        
        # Check if personnel is recognized
        personnel = parser.get_personnel_by_phone(test_message['phone_number'])
        if personnel:
            print(f"Personnel identified: {personnel['full_name']} ({personnel['rank']})")
        else:
            print("Personnel not found in roster")
        
        # Process the message
        result = parser.process_message(test_message)
        
        if result.get('status') == 'processed':
            analysis = result.get('gpt_analysis', {})
            print(f"\nMessage processed successfully!")
            print(f"Absence report: {analysis.get('is_absence_report')}")
            print(f"Type: {analysis.get('absence_type')}")
            print(f"Date: {analysis.get('appointment_date')}")
            print(f"Time: {analysis.get('start_time')}")
            
            # Show current appointments
            print(f"\nCurrent appointments:")
            appointments = parser.get_pending_appointments()
            for apt in appointments:
                if apt.get('phone_number') == test_message['phone_number']:
                    print(f"  - {apt.get('personnel_name', 'Unknown')} ({apt.get('absence_type')})")
                    print(f"    Time: {apt.get('start_time')} on {apt.get('appointment_date')}")
                    print(f"    ID: {apt.get('id')}")
        else:
            print(f"Error: {result.get('error')}")
        
        # Show manning status
        print(f"\nManning status (assuming 10 total personnel):")
        manning = parser.get_manning_status(10)
        print(f"Currently out: {manning['currently_out']}")
        print(f"Available: {manning['available']}")
        print(f"Availability: {manning['availability_percentage']:.1f}%")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_ssgtwoodley_message()