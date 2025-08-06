# Twilio SMS Integration Debugging Guide

## Issue Summary

**Problem**: Twilio webhook receives SMS messages but doesn't send replies back to users.

**Root Cause Identified**: Railway environment uses API Key format credentials (`SK...`) instead of Account SID format (`AC...`), causing Twilio client initialization issues.

## Fixes Applied

### 1. Enhanced TwilioHandler Initialization
- **File**: `twilio_handler.py`
- **Change**: Added detection for API Key vs Account SID format
- **Impact**: Proper Twilio client initialization with both credential types

### 2. Improved Webhook Error Handling
- **File**: `start_website.py`
- **Change**: Added comprehensive logging to `/api/twilio/sms` endpoint
- **Impact**: Better debugging visibility in Railway logs

### 3. Enhanced SMS Sending with Debug Logging
- **File**: `twilio_handler.py`
- **Change**: Added detailed error logging for SMS sending failures
- **Impact**: Clear error messages when SMS sending fails

## Testing Steps for Railway Environment

### Step 1: Deploy the Fixes
```bash
git add .
git commit -m "Fix Twilio API Key authentication and enhance webhook logging"
git push origin main
```

Railway will automatically redeploy with the changes.

### Step 2: Monitor Railway Logs
1. Go to https://railway.app/
2. Select your fssagent project
3. Click on your service
4. Go to 'Logs' tab
5. Look for initialization messages:
   - `🔧 Initializing Twilio client with API Key: SK24ff5e...`
   - `✅ Twilio client initialized successfully`
   - `✅ Found main account SID: AC...`

### Step 3: Test Webhook Endpoint
Run the production test script:
```bash
python tests/test_twilio_production.py
```

This will:
- Test webhook endpoint accessibility
- Simulate Twilio webhook requests
- Test various phone number formats
- Test different SMS commands

### Step 4: Send Real SMS Test
1. Send SMS to `(813) 438-1333` from a registered phone number
2. Watch Railway logs for:
   - `🔄 Twilio webhook received`
   - `✅ Valid webhook: From +1234567890`
   - `✅ TwilioHandler client ready`
   - `📤 Sending SMS to +1234567890`
   - `✅ SMS sent successfully. SID: SM...`

### Step 5: Debug Common Issues

#### If client initialization fails:
```
❌ Failed to initialize Twilio client: [error]
```
**Solution**: Check Railway environment variables are set correctly:
- `TWILIO_ACCOUNT_SID` = `SK24ff5e025086c2314f64aca2694e92d0`
- `TWILIO_AUTH_TOKEN` = `0ce46917d95963bedf8f80bbe91e1c36`
- `TWILIO_PHONE_NUMBER` = `+18134381333`

#### If webhook receives but no SMS sent:
```
🔄 Twilio webhook received
❌ TwilioHandler client not initialized
```
**Solution**: Check credential authentication. Run local debug script.

#### If personnel not found:
```
Your phone number is not registered in our system
```
**Solution**: Add phone numbers to database or test with registered number.

## Local Development Testing

### Run Debug Script
```bash
python tests/debug_twilio_railway.py
```

This script tests:
- Credential format detection
- Twilio client initialization
- TwiML response format
- Personnel phone lookup

### Expected Output
```
TWILIO RAILWAY PRODUCTION DEBUG
============================================================
Account SID: SK24ff5e025086c2314f64aca2694e92d0
🔍 ISSUE FOUND: Account SID starts with 'SK' (API Key format)
✅ Twilio client initialized successfully
✅ Account verified: [Account Name]
```

## Environment Variables Verification

Your Railway environment should have:

```bash
TWILIO_ACCOUNT_SID=SK24ff5e025086c2314f64aca2694e92d0
TWILIO_AUTH_TOKEN=0ce46917d95963bedf8f80bbe91e1c36
TWILIO_PHONE_NUMBER=+18134381333
```

## Webhook URL Verification

Ensure Twilio Console has webhook URL set to:
```
https://fssagent.com/api/twilio/sms
```

Method: `POST`
Content-Type: `application/x-www-form-urlencoded`

## Common Error Messages and Solutions

### 1. Authentication Failed
```
❌ Error sending SMS: Unable to create record: Authenticate
```
**Solution**: API Key credentials may be incorrect or expired. Verify in Twilio Console.

### 2. Phone Number Not Verified
```
❌ Error sending SMS: The number +1234567890 is unverified
```
**Solution**: For trial accounts, add number to verified list in Twilio Console.

### 3. Invalid Phone Number Format
```
❌ Error sending SMS: Invalid 'To' Phone Number
```
**Solution**: Ensure phone numbers are in E.164 format (+1234567890).

## Next Steps After Deployment

1. **Monitor Logs**: Watch Railway logs during first few SMS tests
2. **Test Commands**: Send various commands (status, appointment, help)
3. **Verify Responses**: Confirm SMS replies are received by users
4. **Check Database**: Ensure appointments and status updates are recorded

## Rollback Plan

If issues persist, revert to previous version:
```bash
git revert HEAD
git push origin main
```

Then investigate credential format with Twilio support.

## Support Resources

- **Twilio Console**: https://console.twilio.com
- **Railway Dashboard**: https://railway.app/
- **Debug Scripts**: `tests/debug_twilio_railway.py`, `tests/test_twilio_production.py`