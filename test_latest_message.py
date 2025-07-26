#!/usr/bin/env python3

from gpt_parser import GPTParser

def test_latest_message():
    """Test processing the latest message"""
    
    try:
        parser = GPTParser()
        print("Testing latest message processing...\n")
        
        # Create test message with the actual extracted content
        test_message = {
            'phone_number': '+14408293193',
            'message_text': 'I got a personal appointment 7 aug at 0900 that will be about an hour long.',
            'id': '19844afce946ca03'
        }
        
        print(f"Message: {test_message['message_text']}")
        print(f"From: {test_message['phone_number']}")
        
        # Process the message
        result = parser.process_message(test_message)
        
        print(f"\nProcessing result:")
        print(f"Status: {result.get('status')}")
        
        if result.get('status') == 'processed':
            analysis = result.get('gpt_analysis', {})
            print(f"\nClaude Analysis:")
            for key, value in analysis.items():
                print(f"  {key}: {value}")
            
            # Check if it was stored as appointment
            print(f"\nWas it stored as appointment?")
            recent_appointments = [apt for apt in parser.appointments 
                                 if apt.get('original_message_id') == '19844afce946ca03']
            if recent_appointments:
                apt = recent_appointments[0]
                print(f"YES - Stored as: {apt.get('personnel_name')} ({apt.get('absence_type')}) on {apt.get('appointment_date')} at {apt.get('start_time')}")
            else:
                print("NO - Not stored as appointment")
                
        else:
            print(f"Error: {result.get('error')}")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_latest_message()