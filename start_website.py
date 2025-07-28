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

app = Flask(__name__, 
            template_folder='website/templates',
            static_folder='website/static')

@app.route('/')
def home():
    """Home page with Apple-style design"""
    return render_template('index.html')

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
    """API endpoint to get all calendar events (appointments, leave, events)"""
    try:
        calendar_mgr = CalendarManager()
        
        # Update personnel statuses in real-time
        calendar_mgr.update_personnel_statuses()
        
        # Get events by category with colors
        events_by_category = calendar_mgr.get_events_by_category()
        
        # Flatten for backward compatibility while adding new structure
        all_events = []
        for category, data in events_by_category.items():
            for event in data['events']:
                event['category_color'] = data['color']
                all_events.append(event)
        
        return jsonify({
            'success': True,
            'appointments': all_events,  # Keep old name for compatibility
            'events_by_category': events_by_category,
            'total_count': len(all_events)
        })
    
    except Exception as e:
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
    """API endpoint to get current personnel staffing status with real-time updates"""
    try:
        calendar_mgr = CalendarManager()
        
        # Update personnel statuses based on current appointments/leave
        updates_made = calendar_mgr.update_personnel_statuses()
        
        # Load updated personnel data
        personnel = calendar_mgr.personnel
        
        print(f"Loaded {len(personnel)} personnel records")
        if updates_made:
            print(f"Real-time updates made: {updates_made}")
        
        # Calculate staffing stats
        total_personnel = len(personnel)
        military_count = len([p for p in personnel if p['type'] == 'military'])
        civilian_count = len([p for p in personnel if p['type'] == 'civilian'])
        
        # Working count = people in work locations (front_desk, admin_room, terminal, float)
        # Out of office = people unavailable (leave, appointment)
        working_statuses = ['front_desk', 'admin_room', 'terminal', 'float']
        unavailable_statuses = ['leave', 'appointment']
        
        working_count = len([p for p in personnel if p['status'] in working_statuses])
        out_of_office_count = len([p for p in personnel if p['status'] in unavailable_statuses])
        
        # Assignment breakdown by status
        assignments = {
            'terminal': [p for p in personnel if p['status'] == 'terminal'],
            'admin_room': [p for p in personnel if p['status'] == 'admin_room'],
            'floor': [p for p in personnel if p['status'] == 'front_desk'],
            'float': [p for p in personnel if p['status'] == 'float']
        }
        
        assignment_stats = {}
        for assignment, people in assignments.items():
            assignment_stats[assignment] = {
                'count': len(people),
                'personnel': people  # Send the full person objects, not just extracted fields
            }
        
        # Ensure all sections exist even if empty
        for section in ['terminal', 'admin_room', 'floor', 'float']:
            if section not in assignment_stats:
                assignment_stats[section] = {'count': 0, 'personnel': []}
        
        result = {
            'success': True,
            'stats': {
                'total_personnel': total_personnel,
                'military_count': military_count,
                'civilian_count': civilian_count,
                'working_count': working_count,
                'out_of_office_count': out_of_office_count
            },
            'assignments': assignment_stats,
            'real_time_updates': updates_made,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Returning result with {len(assignment_stats)} assignment categories")
        return jsonify(result)
    
    except Exception as e:
        import traceback
        print(f"Error in api_personnel_status: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/personnel')
def api_personnel():
    """API endpoint to get all personnel data"""
    try:
        import json
        
        # Load personnel data from file
        with open('personnel_assignments.json', 'r') as f:
            personnel = json.load(f)
        
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


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("Starting Vera Web Server...")
    print(f"Visit: http://localhost:{port}")
    app.run(debug=debug, host='127.0.0.1', port=port)