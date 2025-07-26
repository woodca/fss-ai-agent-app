#!/usr/bin/env python3

from gpt_parser import GPTParser
import json

def test_single_command():
    """Test a single status command to debug the issue"""
    
    print("DEBUG: Status Command Processing\n")
    
    try:
        parser = GPTParser()
        print("Parser initialized")
        
        # Test the exact command that's failing
        message_data = {
            'id': 'test_001',
            'message_text': 'A1C Davis to admin room',
            'phone_number': 'test_phone',
            'source': 'debug',
            'timestamp': '2025-07-26T00:00:00'
        }
        
        print(f"Testing command: '{message_data['message_text']}'")
        print("-" * 50)
        
        # Process the command
        result = parser.process_status_command(message_data, 'test_phone')
        
        print("\nResult:")
        print(f"Success: {result.get('success', False)}")
        print(f"Message: {result.get('message', 'None')}")
        print(f"Response Message: {result.get('response_message', 'None')}")
        print(f"Needs Clarification: {result.get('needs_clarification', False)}")
        print(f"Person Updated: {result.get('person_updated', 'None')}")
        
        if result.get('person_updated'):
            person = result['person_updated']
            print(f"\nPerson Details:")
            print(f"  Name: {person.get('name')}")
            print(f"  Assignment: {person.get('assignment')}")
            print(f"  Status: {person.get('status')}")
        
        # Show current personnel list for reference
        print("\nCurrent Personnel in System:")
        assignments = parser.get_personnel_assignments()
        for person in assignments.get('personnel', [])[:5]:  # Show first 5
            print(f"  - {person.get('name')} ({person.get('assignment')})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_command()