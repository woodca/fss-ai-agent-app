#!/usr/bin/env python3

from email_parser import EmailParser
import json

def debug_latest_message():
    """Debug the most recent message that didn't make it to calendar"""
    
    try:
        parser = EmailParser()
        print("Debugging latest message extraction...\n")
        
        # Get the very latest message only
        print("Fetching most recent message from Gmail...")
        messages = parser.get_google_voice_messages(max_results=1)
        
        if not messages:
            print("No new messages found")
            return
        
        msg = messages[0]
        print(f"Latest Message Details:")
        print(f"  ID: {msg.get('id')}")
        print(f"  Phone: {msg.get('phone_number')}")  
        print(f"  Subject: {msg.get('subject')}")
        print(f"  Date: {msg.get('date')}")
        print(f"  Extracted Message: '{msg.get('message_text')}'")
        print(f"\nFull Raw Body:")
        print("=" * 60)
        print(msg.get('raw_body', ''))
        print("=" * 60)
        
        # Let's also show what lines were found
        lines = msg.get('raw_body', '').split('\n')
        print(f"\nBody broken into lines:")
        for i, line in enumerate(lines[:20]):  # Show first 20 lines
            print(f"  {i:2d}: '{line.strip()}'")
        
    except Exception as e:
        print(f"Debug failed: {e}")

if __name__ == "__main__":
    debug_latest_message()