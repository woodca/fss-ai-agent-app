#!/usr/bin/env python3

from flask import Flask, render_template, jsonify
import sys
import os

# Add parent directory to path so we can import gpt_parser
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Change working directory to parent so file paths work correctly
os.chdir(parent_dir)

from gpt_parser import GPTParser
from vera_agent import VeraAgent
from database_manager import DatabaseManager
from appointment_manager import AppointmentManager
from flask import request
import json
from datetime import datetime

app = Flask(__name__)

# Store conversation context with persistence
conversation_contexts = {}
CONVERSATION_FILE = 'conversation_contexts.json'

def load_conversation_contexts():
    """Load conversation contexts from file"""
    global conversation_contexts
    try:
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, 'r') as f:
                conversation_contexts = json.load(f)
        else:
            conversation_contexts = {}
    except Exception as e:
        print(f"Error loading conversation contexts: {e}")
        conversation_contexts = {}

def save_conversation_contexts():
    """Save conversation contexts to file"""
    try:
        with open(CONVERSATION_FILE, 'w') as f:
            json.dump(conversation_contexts, f, indent=2)
    except Exception as e:
        print(f"Error saving conversation contexts: {e}")

# Load existing conversation contexts on startup
load_conversation_contexts()

# Initialize database and appointment manager for API endpoints
db = DatabaseManager()
appointment_manager = AppointmentManager()

@app.route('/')
def home():
    """Home page with Apple-style design"""
    return render_template('index.html')

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
    """API endpoint to get manning status from database"""
    try:
        print("Getting manning status from database...")
        
        # Get personnel status summary from database
        summary = db.get_personnel_status_summary()
        
        # Create manning status similar to GPTParser format
        manning = {
            'total_personnel': summary.get('total_personnel', 0),
            'working': summary.get('working_count', 0),
            'out_of_office': summary.get('out_of_office_count', 0),
            'status_breakdown': summary.get('status_counts', {}),
            'availability_percentage': round((summary.get('working_count', 0) / max(summary.get('total_personnel', 1), 1)) * 100, 1)
        }
        
        print(f"Database manning status: {manning}")
        
        return jsonify({
            'success': True,
            'manning': manning,
            'debug_info': {
                'source': 'database'
            }
        })
    
    except Exception as e:
        print(f"Error getting manning status from database: {e}")
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

@app.route('/api/contacts')
def api_contacts():
    """API endpoint to get contact information from database"""
    try:
        print("Getting contacts from database...")
        
        # Get all personnel from database (which includes contact info)
        personnel = db.get_all_personnel()
        
        # Format as contacts with phone/email information
        contacts = []
        for person in personnel:
            if person.get('phone') or person.get('email'):
                contacts.append({
                    'id': person.get('id'),
                    'name': person.get('name'),
                    'full_name': person.get('full_name'),
                    'rank': person.get('rank'),
                    'position': person.get('position'),
                    'phone': person.get('phone'),
                    'email': person.get('email'),
                    'type': person.get('type'),
                    'status': person.get('status')
                })
        
        print(f"Database contacts count: {len(contacts)}")
        
        return jsonify({
            'success': True,
            'contacts': contacts,
            'total_count': len(contacts),
            'debug_info': {
                'source': 'database'
            }
        })
    
    except Exception as e:
        print(f"Error getting contacts from database: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai-agent/message', methods=['POST'])
def ai_agent_message():
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
        
        # Get conversation context
        if sender_id not in conversation_contexts:
            conversation_contexts[sender_id] = []
        
        context = conversation_contexts[sender_id]
        
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
        conversation_contexts[sender_id] = context
        
        # Save conversation contexts to file
        save_conversation_contexts()
        
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

if __name__ == '__main__':
    print("Starting Vera Web Server...")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)