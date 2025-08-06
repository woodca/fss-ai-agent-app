#!/usr/bin/env python3

import requests
import json

def test_ai_agent_api():
    """Test the AI agent web API"""
    
    print("🧪 Testing Vera Web API\n")
    
    # Test URL
    url = "http://localhost:5000/api/ai-agent/message"
    
    # Test cases
    test_messages = [
        "How many people are available?",
        "A1C Davis to terminal", 
        "Show me current staffing",
        "Wilson is now available",
        "Who's working on the floor?",
        "Put Garcia on admin room"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"--- Test {i} ---")
        print(f"Message: '{message}'")
        
        try:
            # Send request
            payload = {
                "message": message,
                "sender_id": f"test_user_{i}"
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data.get('success', False)}")
                print(f"Type: {data.get('message_type', 'unknown')}")
                print(f"Response: {data.get('ai_response', 'No response')}")
                
                if data.get('person_updated'):
                    person = data['person_updated']
                    print(f"Updated: {person.get('rank')} {person.get('name')}")
                    print(f"New assignment: {person.get('assignment')}")
                    print(f"New status: {person.get('status')}")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_ai_agent_api()