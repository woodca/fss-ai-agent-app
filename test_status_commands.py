#!/usr/bin/env python3

from gpt_parser import GPTParser
import json

def test_status_commands():
    """Test the status command processing functionality"""
    
    print("🤖 Testing FSS AI Agent Status Command Processing\n")
    
    # Initialize the parser
    try:
        parser = GPTParser()
        print("✅ GPT Parser initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing parser: {e}")
        return
    
    # Test commands
    test_commands = [
        {
            'message_text': 'Airman Patel moved to terminal',
            'phone_number': '555-123-4567'
        },
        {
            'message_text': 'SSgt Martinez is now available',
            'phone_number': '555-123-4568'
        },
        {
            'message_text': 'SrA Wilson on leave',
            'phone_number': '555-123-4569'
        },
        {
            'message_text': 'A1C Davis to admin room',
            'phone_number': '555-123-4570'
        },
        {
            'message_text': 'Thompson moved to floor',
            'phone_number': '555-123-4571'
        },
        {
            'message_text': 'Put Johnson on terminals',
            'phone_number': '555-123-4572'
        }
    ]
    
    print("🧪 Testing status commands:\n")
    
    for i, command in enumerate(test_commands, 1):
        print(f"--- Test {i} ---")
        print(f"Command: '{command['message_text']}'")
        print(f"From: {command['phone_number']}")
        
        try:
            # Process the status command
            result = parser.process_status_command(command, command['phone_number'])
            
            print(f"Success: {result.get('success', False)}")
            
            if result.get('success'):
                print(f"✅ {result.get('response_message', 'Update completed')}")
                if 'person_updated' in result:
                    person = result['person_updated']
                    print(f"   Updated: {person.get('rank')} {person.get('name')}")
                    print(f"   Assignment: {person.get('assignment')}")
                    print(f"   Status: {person.get('status')}")
            elif result.get('needs_clarification'):
                print(f"❓ Needs clarification:")
                print(f"   {result.get('response_message', 'No message')}")
            else:
                print(f"❌ Failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error processing command: {e}")
        
        print()
    
    print("📊 Current Personnel Status:")
    try:
        assignments = parser.get_personnel_assignments()
        personnel = assignments.get('personnel', [])
        
        for person in personnel:
            name = f"{person.get('rank', '')} {person.get('name', '')}"
            assignment = person.get('assignment', 'Unknown')
            status = person.get('status', 'Unknown')
            last_updated = person.get('last_updated', 'Never')
            
            print(f"  {name:<20} | {assignment:<12} | {status:<12} | {last_updated[:19]}")
            
    except Exception as e:
        print(f"❌ Error getting personnel status: {e}")

if __name__ == "__main__":
    test_status_commands()