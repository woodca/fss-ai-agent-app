#!/usr/bin/env python3
"""
Railway Production Debugging Script for Twilio SMS Integration
Tests the exact configuration and client initialization used in production
"""

import os
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import traceback

def debug_twilio_credentials():
    """Debug Twilio credential format and client initialization"""
    print("TWILIO RAILWAY PRODUCTION DEBUG")
    print("=" * 60)
    
    # Get environment variables (simulating Railway production)
    account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'SK24ff5e025086c2314f64aca2694e92d0')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN', '0ce46917d95963bedf8f80bbe91e1c36')
    twilio_phone = os.getenv('TWILIO_PHONE_NUMBER', '+18134381333')
    
    print(f"Account SID: {account_sid}")
    print(f"Auth Token: {auth_token[:8]}{'*' * (len(auth_token)-8)}")
    print(f"Phone: {twilio_phone}")
    print()
    
    # Check credential format
    print("CREDENTIAL FORMAT ANALYSIS:")
    if account_sid.startswith('SK'):
        print("🔍 ISSUE FOUND: Account SID starts with 'SK' (API Key format)")
        print("   Expected: Account SID should start with 'AC' for standard auth")
        print("   Current format suggests this is an API Key, not Account SID")
        print()
    elif account_sid.startswith('AC'):
        print("✅ Account SID format looks correct (starts with 'AC')")
        print()
    else:
        print("⚠️  Unknown Account SID format")
        print()
    
    # Test client initialization
    print("CLIENT INITIALIZATION TEST:")
    try:
        client = Client(account_sid, auth_token)
        print("✅ Twilio client initialized successfully")
        
        # Test account fetch (this will fail if credentials are wrong)
        try:
            account = client.api.accounts(account_sid).fetch()
            print(f"✅ Account verified: {account.friendly_name}")
            return client
        except Exception as e:
            print(f"❌ Account verification failed: {e}")
            print("   This indicates credential authentication issues")
            return None
            
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        print("   Full traceback:")
        traceback.print_exc()
        return None

def debug_api_key_vs_account_sid():
    """Debug the difference between API Key and Account SID authentication"""
    print("\nAPI KEY vs ACCOUNT SID AUTHENTICATION:")
    print("=" * 60)
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'SK24ff5e025086c2314f64aca2694e92d0')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN', '0ce46917d95963bedf8f80bbe91e1c36')
    
    if account_sid.startswith('SK'):
        print("DETECTED: API Key Authentication")
        print("API Key format: SK + 32 chars")
        print("Auth method: Using API Key instead of Account SID")
        print()
        print("RECOMMENDED FIX:")
        print("1. Get your actual Account SID from Twilio Console")
        print("   - Should start with 'AC' + 32 characters")
        print("   - Found on main dashboard: https://console.twilio.com")
        print()
        print("2. OR modify client initialization for API Key auth:")
        print("   client = Client(username=api_key_sid, password=api_key_secret, account_sid=main_account_sid)")
        print()
        
        # Check if we have the main account SID somewhere
        print("3. Alternative: Use current credentials as API Key with main Account SID")
        print("   You need to find your main Account SID (AC...)")
    else:
        print("Using Account SID authentication (standard method)")

def test_webhook_response_format():
    """Test TwiML response format that webhook should return"""
    print("\nWEBHOOK RESPONSE FORMAT TEST:")
    print("=" * 60)
    
    # Simulate webhook data
    sample_data = {
        'From': '+15551234567',
        'Body': 'test message',
        'MessageSid': 'SM1234567890abcdef1234567890abcdef'
    }
    
    try:
        # Create TwiML response like our webhook does
        resp = MessagingResponse()
        resp.message("Test response message")
        twiml_str = str(resp)
        
        print("✅ TwiML Response Generated Successfully:")
        print(twiml_str)
        print()
        print("Expected Content-Type: text/xml")
        print("Expected Status Code: 200")
        
    except Exception as e:
        print(f"❌ TwiML response generation failed: {e}")
        traceback.print_exc()

def debug_personnel_lookup():
    """Debug personnel phone number lookup"""
    print("\nPERSONNEL LOOKUP DEBUG:")
    print("=" * 60)
    
    try:
        from database_manager import DatabaseManager
        db = DatabaseManager()
        
        # Get personnel with phone numbers
        with db.transaction() as conn:
            cursor = conn.execute("SELECT id, rank, last_name, phone FROM personnel WHERE phone IS NOT NULL")
            personnel = cursor.fetchall()
            
        if personnel:
            print(f"✅ Found {len(personnel)} personnel with phone numbers:")
            for p in personnel:
                print(f"   {p['rank']} {p['last_name']}: {p['phone']}")
        else:
            print("⚠️  No personnel found with phone numbers")
            print("   This could prevent SMS authentication")
            
    except Exception as e:
        print(f"❌ Database lookup failed: {e}")
        traceback.print_exc()

def main():
    """Run all debug tests"""
    client = debug_twilio_credentials()
    debug_api_key_vs_account_sid()
    test_webhook_response_format()
    debug_personnel_lookup()
    
    print("\nSUMMARY:")
    print("=" * 60)
    if client:
        print("✅ Twilio client can be initialized")
        print("🔍 Check if account verification passed above")
    else:
        print("❌ Twilio client initialization failed")
        print("🚨 This is likely why SMS replies aren't being sent")
    
    print("\nNEXT STEPS:")
    print("1. Fix credential format issue (API Key vs Account SID)")
    print("2. Verify webhook endpoint receives requests")
    print("3. Test actual SMS sending in production")
    print("4. Check Railway logs for any errors")

if __name__ == '__main__':
    main()