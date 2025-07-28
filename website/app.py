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

@app.route('/')
def home():
    """Home page with Apple-style design"""
    return render_template('index.html')

@app.route('/api/appointments')
def api_appointments():
    """API endpoint to get all appointments"""
    try:
        print(f"Current working directory: {os.getcwd()}")
        print(f"Looking for appointments.json at: {os.path.abspath('appointments.json')}")
        print(f"File exists: {os.path.exists('appointments.json')}")
        
        parser = GPTParser()
        appointments = parser.get_pending_appointments()
        
        print(f"Raw appointments count: {len(parser.appointments)}")
        print(f"Pending appointments count: {len(appointments)}")
        
        # Format appointments for the frontend
        formatted_appointments = []
        for apt in appointments:
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
                'original_text': apt.get('original_text'),
                'created_timestamp': apt.get('created_timestamp')
            })
        
        return jsonify({
            'success': True,
            'appointments': formatted_appointments,
            'total_count': len(formatted_appointments),
            'debug_info': {
                'cwd': os.getcwd(),
                'raw_count': len(parser.appointments),
                'pending_count': len(appointments)
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