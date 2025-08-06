# Twilio SMS Integration Setup Guide

## Your Twilio Phone Number
- **Phone Number**: (813) 438-1333
- **Format for Twilio**: +18134381333

## Step 1: Get Your Twilio Credentials

1. Log in to your Twilio Console: https://console.twilio.com
2. On the dashboard, you'll see:
   - **Account SID**: Starts with "AC..." (34 characters)
   - **Auth Token**: Click "View" to reveal (32 characters)
3. Copy both values - you'll need them for Step 2

To check if your number is toll-free or local:
- In Twilio Console, go to Phone Numbers > Manage > Active Numbers
- Click on your number (813) 438-1333
- It will show the type (likely "Local" for 813 area code - Tampa, FL)

## Step 2: Set Environment Variables

Add these to your `.env` file:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+18134381333
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Configure Twilio Webhook (Railway Deployment)

Since you're using Railway for hosting:

1. **Get your Railway app URL**:
   - It will be something like: `https://your-app-name.up.railway.app`

2. **Configure Twilio Webhook**:
   - Go to Twilio Console
   - Navigate to Phone Numbers > Manage > Active Numbers
   - Click on (813) 438-1333
   - In the "Messaging" section:
     - **When a message comes in**: 
       - Webhook: `https://your-app-name.up.railway.app/api/twilio/sms`
       - Method: HTTP POST
   - Click "Save"

3. **Add Environment Variables to Railway**:
   - Go to your Railway project
   - Click on your service
   - Go to "Variables" tab
   - Add:
     - `TWILIO_ACCOUNT_SID` = Your Account SID
     - `TWILIO_AUTH_TOKEN` = Your Auth Token
     - `TWILIO_PHONE_NUMBER` = +18134381333

## Step 5: Test the Integration

### Local Testing (Optional)
For local testing, you can use ngrok to expose your local server:
```bash
# Install ngrok
pip install pyngrok

# Start your Flask app
python start_website.py

# In another terminal, expose it
ngrok http 5000

# Use the ngrok URL in Twilio webhook settings temporarily
```

### Production Testing
Once deployed to Railway:

1. **Test Basic Connection**:
   - Text "HELP" to (813) 438-1333
   - You should receive a list of available commands

2. **Test Personnel Verification**:
   - The system will verify the sender's phone number against the database
   - All 14 personnel already have phone numbers stored

3. **Test Commands**:
   - `HELP` - Get command list
   - `STATUS` - Check current location/status
   - `APPOINTMENT tomorrow 2pm ID card` - Schedule appointment
   - `CANCEL` - Cancel latest appointment
   - `LEAVE Dec 20-27` - Report leave dates

## How It Works

### Incoming SMS Flow:
1. Troop texts (813) 438-1333
2. Twilio receives the SMS
3. Twilio sends webhook POST to your Railway app at `/api/twilio/sms`
4. Your app:
   - Verifies sender's phone number against personnel database
   - Processes the command (appointment, status, leave, etc.)
   - Updates database as needed
   - Sends response back via Twilio

### Security Features:
- Only registered personnel phone numbers can interact with the system
- Each message is tracked to prevent duplicates
- All actions are logged with timestamps

## Available SMS Commands

Personnel can text these commands:

### Appointment Management
- `Appointment [date] [time] [type]`
  - Example: "Appointment tomorrow 2pm ID card"
  - Example: "Schedule appt Friday 0900 for CAC"

### Status Updates
- `STATUS` - Check current duty location
- `LEAVE [dates]` - Report leave/TDY
  - Example: "On leave Dec 20 to Jan 3"
  - Example: "TDY next week"

### Appointment Changes
- `CANCEL` - Cancel most recent appointment
- `RESCHEDULE` - Instructions to call CS section

### Help
- `HELP` - Show available commands

## Response Types

The system sends automatic SMS responses for:
- ✅ Appointment confirmations with date/time
- 📍 Current status/location queries
- ❌ Cancellation confirmations
- 📅 Leave/TDY acknowledgments
- ❓ Unrecognized message guidance

## Conversation Threading

The system currently processes each SMS independently. If you want conversation context:
- Messages include personnel name in responses
- Recent appointment history is considered
- Future enhancement: Multi-message conversations

## SMS Delivery Tracking

Currently, the system:
- Logs all sent messages with Twilio Message SID
- Does not track delivery status
- Future enhancement: Webhook for delivery receipts

## Troubleshooting

### Message Not Received
1. Check Twilio Console > Monitor > Logs
2. Verify webhook URL is correct and HTTPS
3. Check Railway logs for incoming requests

### Personnel Not Recognized
- Verify phone number format in database
- System handles: +1XXXXXXXXXX, 1XXXXXXXXXX, XXXXXXXXXX
- Check exact format in personnel table

### Webhook Errors
- Railway logs will show detailed error messages
- Common issues:
  - Missing environment variables
  - Database connection issues
  - Twilio credentials incorrect

## Testing Without Sending Real SMS

For development, you can test the handler directly:
```python
from twilio_handler import TwilioHandler

handler = TwilioHandler()
response = handler.process_incoming_sms(
    from_number="+18038690528",  # A1C Gauci's number
    body="Appointment tomorrow 1400 ID card",
    message_sid="TEST123"
)
print(response)
```

## Next Steps

1. Get your Twilio credentials from the console
2. Add them to Railway environment variables
3. Deploy the updated code
4. Configure the webhook in Twilio
5. Test with a simple "HELP" message

The system is now ready to receive and process SMS messages from your troops!