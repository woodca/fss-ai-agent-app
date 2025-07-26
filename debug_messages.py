#!/usr/bin/env python3

from email_parser import EmailParser
import json

def debug_latest_messages():
    """Debug what messages are being extracted from Gmail"""
    
    try:
        parser = EmailParser()
        print("Debugging Gmail message extraction...\n")
        
        # Get recent messages with verbose output
        print("Fetching latest messages from Gmail...")
        messages = parser.get_google_voice_messages(max_results=5)
        
        print(f"Found {len(messages)} messages:\n")
        
        for i, msg in enumerate(messages, 1):
            print(f"Message {i}:")
            print(f"  ID: {msg.get('id')}")
            print(f"  Phone: {msg.get('phone_number')}")
            print(f"  Subject: {msg.get('subject')}")
            print(f"  Date: {msg.get('date')}")
            print(f"  Message Text: '{msg.get('message_text')}'")
            print(f"  Raw Body (first 200 chars): {msg.get('raw_body', '')[:200]}...")
            print()
        
        # Show what's in processed messages file
        try:
            with open('processed_messages.json', 'r') as f:
                processed = json.load(f)
            print(f"Already processed message count: {len(processed)}")
        except:
            print("No processed messages file found")
        
    except Exception as e:
        print(f"Debug failed: {e}")

if __name__ == "__main__":
    debug_latest_messages()