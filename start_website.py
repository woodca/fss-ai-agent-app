#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

from gpt_parser import GPTParser
from calendar_manager import CalendarManager
from vera_agent import VeraAgent
from database_manager import DatabaseManager
from twilio_handler import TwilioHandler

app = Flask(__name__, 
            template_folder='website/templates',
            static_folder='static')

# Initialize database manager
db = DatabaseManager()

@app.route('/')
def home():
    """Serve React app"""
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app for any non-API routes"""
    if path.startswith('api/'):
        # Let API routes handle themselves
        return None
    try:
        # Try to serve the specific file
        return app.send_static_file(path)
    except:
        # Fall back to React app for client-side routing
        return app.send_static_file('index.html')

@app.route('/section-leads')
def section_leads():
    """Section leads page"""
    return render_template('section_leads.html')

@app.route('/calendar')
def calendar():
    """Section calendar page"""
    return render_template('appointments.html')

@app.route('/api/appointments')
def api_appointments():
    """API endpoint to get all appointments from database"""
    try:
        print(f"Getting appointments from database...")
        
        # Get calendar events from database
        events_data = db.get_calendar_events()
        
        # Format appointments for the frontend
        formatted_appointments = []
        for apt in events_data['personnel_appointments']:
            formatted_appointments.append({
                'id': apt.get('id'),
                'personnel_name': apt.get('personnel_name', 'Unknown'),
                'personnel_rank': apt.get('personnel_rank'),
                'absence_type': apt.get('absence_type'),
                'appointment_date': apt.get('appointment_date'),
                'end_date': apt.get('end_date'),  # Include end_date for multi-day appointments
                'start_time': apt.get('start_time'),
                'end_time': apt.get('end_time'),
                'duration_hours': apt.get('duration_hours'),
                'all_day': apt.get('all_day', False),
                'notes': apt.get('notes'),
                'created_timestamp': apt.get('created_timestamp'),
                'category_color': apt.get('category_color', '#FFC107')
            })
        
        # Also include general events
        formatted_events = []
        for event in events_data['general_events']:
            formatted_events.append({
                'id': event.get('id'),
                'title': event.get('title'),
                'event_type': event.get('event_type'),
                'event_date': event.get('event_date'),
                'start_time': event.get('start_time'),
                'end_time': event.get('end_time'),
                'location': event.get('location'),
                'description': event.get('description'),
                'all_day': event.get('all_day', False),
                'category_color': event.get('category_color', '#007BFF')
            })
        
        print(f"Database appointments count: {len(formatted_appointments)}")
        print(f"Database general events count: {len(formatted_events)}")
        
        return jsonify({
            'success': True,
            'appointments': formatted_appointments,
            'general_events': formatted_events,
            'total_appointments': len(formatted_appointments),
            'total_events': len(formatted_events),
            'debug_info': {
                'source': 'database',
                'date_range': events_data['date_range']
            }
        })
    
    except Exception as e:
        print(f"Error in api_appointments: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/manning')
def api_manning():
    """API endpoint to get manning status"""
    try:
        parser = GPTParser()
        manning = parser.get_manning_status(13)  # Assuming 13 total personnel
        
        return jsonify({
            'success': True,
            'manning': manning
        })
    
    except Exception as e:
        print(f"Error in api_manning: {e}")
        # Return default manning if API key is missing
        if "API key" in str(e):
            return jsonify({
                'success': True,
                'manning': {
                    'total': 13,
                    'available': 0,
                    'unavailable': 0,
                    'message': 'API key not configured'
                }
            })
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/contacts')
def api_contacts():
    """API endpoint to get contact information"""
    try:
        parser = GPTParser()
        
        return jsonify({
            'success': True,
            'contacts': parser.contacts,
            'total_count': len(parser.contacts)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/personnel-status')
def api_personnel_status():
    """API endpoint to get personnel status and assignments from database"""
    try:
        print("Getting personnel status from database...")
        
        # Get personnel status summary from database
        summary = db.get_personnel_status_summary()
        personnel_list = db.get_all_personnel()
        
        # Group personnel by status/assignment
        assignments = {
            'floor': {'personnel': []},
            'admin_room': {'personnel': []}, 
            'terminal': {'personnel': []},
            'float': {'personnel': []}
        }
        
        for person in personnel_list:
            status = person.get('status', 'unknown')
            
            # Map status to assignment categories
            if status in ['front_desk', 'working']:
                assignments['floor']['personnel'].append(person)
            elif status == 'admin_room':
                assignments['admin_room']['personnel'].append(person)
            elif status == 'terminal':
                assignments['terminal']['personnel'].append(person)
            elif status == 'float':
                assignments['float']['personnel'].append(person)
            # For leave/appointment, they won't be in assignments but will be in out_of_office
        
        # Get unavailable personnel details
        unavailable_personnel = summary.get('unavailable_personnel', [])
        
        # Calculate military vs civilian counts
        military_count = sum(1 for p in personnel_list if p.get('type') == 'military')
        civilian_count = sum(1 for p in personnel_list if p.get('type') == 'civilian')
        
        # Add count field to assignments
        for assignment_key in assignments:
            assignments[assignment_key]['count'] = len(assignments[assignment_key]['personnel'])
        
        stats = {
            'total_personnel': summary.get('total_personnel', 0),
            'military_count': military_count,
            'civilian_count': civilian_count,
            'working_count': summary.get('working_count', 0),
            'out_of_office_count': summary.get('out_of_office_count', 0)
        }
        
        print(f"Database personnel stats: {stats}")
        print(f"Unavailable personnel count: {len(unavailable_personnel)}")
        
        return jsonify({
            'success': True,
            'stats': stats,
            'assignments': assignments,
            'unavailable_personnel': unavailable_personnel,
            'debug_info': {
                'source': 'database',
                'status_counts': summary.get('status_counts', {})
            }
        })
        
    except Exception as e:
        print(f"Error getting personnel status from database: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/personnel')
def api_personnel():
    """API endpoint to get all personnel data from database"""
    try:
        # Get personnel data from database
        personnel = db.get_all_personnel()
        
        return jsonify({
            'success': True,
            'personnel': personnel,
            'total_count': len(personnel)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/personnel-appointments')
def api_personnel_appointments():
    """API endpoint to get appointments with personnel information"""
    try:
        import json
        from datetime import datetime, timedelta
        
        # Load personnel data
        with open('personnel_assignments.json', 'r') as f:
            personnel_data = json.load(f)
        personnel = {p['name']: p for p in personnel_data}
        
        # Get appointments from existing GPT parser
        parser = GPTParser()
        appointments = parser.get_pending_appointments()
        
        # Enhance appointments with personnel data
        enhanced_appointments = []
        for apt in appointments:
            personnel_name = apt.get('personnel_name', '')
            person_info = personnel.get(personnel_name, {})
            
            enhanced_apt = {
                'id': apt.get('id'),
                'personnel_name': personnel_name,
                'personnel_rank': apt.get('personnel_rank') or person_info.get('rank'),
                'personnel_type': person_info.get('type', 'unknown'),
                'status': person_info.get('status', 'unknown'),
                'absence_type': apt.get('absence_type'),
                'appointment_date': apt.get('appointment_date'),
                'start_time': apt.get('start_time'),
                'end_time': apt.get('end_time'),
                'duration_hours': apt.get('duration_hours'),
                'all_day': apt.get('all_day', False),
                'original_text': apt.get('original_text'),
                'created_timestamp': apt.get('created_timestamp')
            }
            enhanced_appointments.append(enhanced_apt)
        
        return jsonify({
            'success': True,
            'appointments': enhanced_appointments,
            'total_count': len(enhanced_appointments)
        })
    
    except Exception as e:
        print(f"Error in api_personnel_appointments: {e}")
        # Return empty appointments if API key is missing
        if "API key" in str(e):
            return jsonify({
                'success': True,
                'appointments': [],
                'total_count': 0,
                'message': 'API key not configured - showing empty appointments'
            })
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai-agent/message', methods=['POST'])
def api_ai_agent_message():
    """API endpoint for Vera chat interface - Now with full Claude intelligence!"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        sender_id = data.get('sender_id', 'web_user')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # Initialize Vera Agent
        vera = VeraAgent()
        
        # Get conversation context (stored in memory for this session)
        if not hasattr(api_ai_agent_message, 'conversation_contexts'):
            api_ai_agent_message.conversation_contexts = {}
        
        if sender_id not in api_ai_agent_message.conversation_contexts:
            api_ai_agent_message.conversation_contexts[sender_id] = []
        
        context = api_ai_agent_message.conversation_contexts[sender_id]
        
        # Chat with Vera (full Claude intelligence!)
        response_message = vera.chat(message, context)
        
        # Store context
        context.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        context.append({
            'role': 'assistant',
            'content': response_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 exchanges (20 messages)
        if len(context) > 20:
            context = context[-20:]
        api_ai_agent_message.conversation_contexts[sender_id] = context
        
        return jsonify({
            'success': True,
            'ai_response': response_message,
            'response': response_message,
            'message_type': 'chat_response'
        })
        
    except Exception as e:
        print(f"Error in ai_agent_message: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'ai_response': 'Sorry, I encountered an error. Please try again.'
        }), 500

@app.route('/api/twilio/sms', methods=['POST'])
def twilio_sms_webhook():
    """Webhook endpoint for incoming Twilio SMS messages"""
    try:
        # Initialize Twilio handler
        twilio = TwilioHandler()
        
        # Process the webhook and get TwiML response
        twiml_response = twilio.handle_webhook(request.form)
        
        # Return TwiML response with proper content type
        return twiml_response, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        print(f"Error processing Twilio webhook: {e}")
        # Return empty TwiML response on error
        from twilio.twiml.messaging_response import MessagingResponse
        resp = MessagingResponse()
        return str(resp), 200, {'Content-Type': 'text/xml'}


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("Starting Vera Web Server...")
    print(f"Visit: http://localhost:{port}")
    app.run(debug=debug, host='127.0.0.1', port=port)