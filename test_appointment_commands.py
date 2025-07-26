#!/usr/bin/env python3

from gpt_parser import GPTParser
import json
from datetime import datetime

def test_appointment_commands():
    """Test various appointment scheduling commands"""
    
    print("DEBUG: Appointment Command Testing\n")
    
    parser = GPTParser()
    
    # Test commands that should create appointments
    test_commands = [
        "Schedule A1C Davis for dental appointment tomorrow at 1000",
        "SrA Wilson has medical appointment today at 1400", 
        "Schedule TSgt Johnson for leave on 2025-07-27 all day",
        "A1C Brown personal business appointment at 0930 for 2 hours",
        "Add medical appointment for SrA Thompson on 2025-07-28 from 0800 to 1000"
    ]
    
    for i, command in enumerate(test_commands):
        print(f"\n{'='*60}")
        print(f"Test {i+1}: {command}")
        print(f"{'='*60}")
        
        message_data = {
            'id': f'test_apt_{i+1}',
            'message_text': command,
            'phone_number': 'test_phone',
            'source': 'debug',
            'timestamp': datetime.now().isoformat()
        }
        
        # Process the command
        result = parser.process_status_command(message_data, 'test_phone')
        
        print(f"Success: {result.get('success', False)}")
        print(f"Message Type: {'Appointment' if result.get('appointment_created') else 'Status' if result.get('person_updated') else 'Other'}")
        print(f"AI Response: {result.get('response_message', 'No response')}")
        
        if result.get('appointment_created'):
            apt = result['appointment_created']
            print(f"\nAppointment Created:")
            print(f"  ID: {apt.get('id')}")
            print(f"  Person: {apt.get('personnel_name')}")
            print(f"  Type: {apt.get('absence_type')}")
            print(f"  Date: {apt.get('appointment_date')}")
            print(f"  Time: {apt.get('start_time')} - {apt.get('end_time', 'TBD')}")
            print(f"  All Day: {apt.get('all_day', False)}")
            
        if result.get('person_updated'):
            person = result['person_updated']
            print(f"\nPerson Status Updated:")
            print(f"  Name: {person.get('name')}")
            print(f"  Status: {person.get('status')}")
        
        if not result.get('success'):
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Needs Clarification: {result.get('needs_clarification', False)}")
    
    # Show current appointments
    print(f"\n{'='*60}")
    print("Current Appointments in System:")
    print(f"{'='*60}")
    
    appointments = parser.get_pending_appointments()
    if appointments:
        for apt in appointments[-5:]:  # Show last 5
            print(f"- {apt.get('personnel_name', 'Unknown')} ({apt.get('absence_type', 'unknown')}) on {apt.get('appointment_date', 'TBD')}")
    else:
        print("No appointments found")

if __name__ == "__main__":
    test_appointment_commands()