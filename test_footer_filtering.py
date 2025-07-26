#!/usr/bin/env python3

from email_parser import EmailParser

def test_footer_filtering():
    """Test that footer text is properly filtered out"""
    
    # Simulate a Google Voice email body that might extract footer text
    test_body = """
<https://voice.google.com>
I have a dental appointment tomorrow at 2pm.
YOUR ACCOUNT <https://voice.google.com> HELP CENTER
<https://support.google.com/voice#topic=1707989> HELP FORUM
<https://productforums.google.com/forum/#!forum/voice>
This email was sent to you because you indicated that you'd like to receive
email notifications for text messages. If you don't want to receive such
emails in the future, please update your email notification settings
<https://voice.google.com/settings#messaging>.
Google LLC
1600 Amphitheatre Pkwy
Mountain View CA 94043 USA
"""
    
    parser = EmailParser()
    
    print("Testing footer filtering...")
    print("Test body contains both message and footer text")
    print()
    
    extracted = parser._extract_message_text(test_body)
    
    print(f"Extracted message: '{extracted}'")
    print()
    
    # Test what we expect vs what we don't want
    expected_good = "I have a dental appointment tomorrow at 2pm."
    not_wanted = "emails in the future, please update your email notification settings"
    
    if extracted == expected_good:
        print("SUCCESS: Extracted the correct message content")
    elif not_wanted in extracted:
        print("FAILED: Extracted footer text instead of message")
    else:
        print(f"UNEXPECTED: Got different text: '{extracted}'")
    
    # Test another problematic pattern
    test_body2 = """
<https://voice.google.com>
This email was sent to you because you indicated that you'd like to receive
email notifications for text messages. If you don't want to receive such
emails in the future, please update your email notification settings
<https://voice.google.com/settings#messaging>.
I need to schedule a medical appointment for next week.
Google LLC
"""
    
    print("\nTesting another pattern...")
    extracted2 = parser._extract_message_text(test_body2)
    print(f"Extracted message: '{extracted2}'")
    
    if "I need to schedule a medical appointment" in extracted2:
        print("SUCCESS: Found the actual message despite footer text")
    else:
        print("FAILED: Did not extract the correct message")

if __name__ == "__main__":
    test_footer_filtering()