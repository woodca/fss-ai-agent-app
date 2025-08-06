#!/usr/bin/env python3

from gpt_parser import GPTParser
import json
from datetime import datetime

def test_smith_leave_command():
    """Test the specific Smith leave command"""
    
    print("Testing Smith leave command processing\n")
    
    parser = GPTParser()
    
    command = "smith is going to be on leave starting tomorrow until 30 jul coming back 31 jul"
    
    message_data = {
        'id': 'test_smith_leave',
        'message_text': command,
        'phone_number': 'test_phone',
        'source': 'debug',
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"Command: {command}")
    print("-" * 60)
    
    # Process the command
    result = parser.process_status_command(message_data, 'test_phone')
    
    print(f"Success: {result.get('success', False)}")
    print(f"Response: {result.get('response_message', 'No response')}")
    
    if result.get('appointment_created'):
        apt = result['appointment_created']
        print(f"\nAppointment Created:")
        print(f"  ID: {apt.get('id')}")
        print(f"  Person: {apt.get('personnel_name')}")
        print(f"  Type: {apt.get('absence_type')}")
        print(f"  Start Date: {apt.get('appointment_date')}")
        print(f"  End Date: {apt.get('end_date', 'Not specified')}")
        
    if result.get('person_updated'):
        person = result['person_updated']
        print(f"\nPerson Status Updated:")
        print(f"  Name: {person.get('name')}")
        print(f"  Status: {person.get('status')}")
        
    # Check what appointments exist for Smith
    appointments = parser.get_pending_appointments()
    smith_appointments = [apt for apt in appointments if 'Smith' in apt.get('personnel_name', '')]
    
    print(f"\nSmith appointments in system: {len(smith_appointments)}")
    for apt in smith_appointments:
        print(f"- {apt.get('personnel_name')} ({apt.get('absence_type')}) on {apt.get('appointment_date')}")

if __name__ == "__main__":
    test_smith_leave_command()