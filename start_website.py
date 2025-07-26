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
    """API endpoint to get all appointments"""
    try:
        parser = GPTParser()
        appointments = parser.get_pending_appointments()
        
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
            'total_count': len(formatted_appointments)
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
    """API endpoint to get current personnel staffing status"""
    try:
        import json
        
        # Load personnel data from file
        with open('personnel_assignments.json', 'r') as f:
            personnel = json.load(f)
        
        # Calculate staffing stats
        total_personnel = len(personnel)
        military_count = len([p for p in personnel if p['type'] == 'military'])
        civilian_count = len([p for p in personnel if p['type'] == 'civilian'])
        
        # Working count = people actively working assignments
        # Out of office = people who cannot work (on_leave + on_appointment)
        working_count = len([p for p in personnel if p['status'] == 'working'])
        out_of_office_count = len([p for p in personnel if p['status'] in ['on_leave', 'on_appointment']])
        
        # Assignment breakdown - only include personnel who are currently working
        assignments = {
            'terminal': [p for p in personnel if p['assignment'] == 'terminal' and p['status'] == 'working'],
            'admin_room': [p for p in personnel if p['assignment'] == 'admin_room' and p['status'] == 'working'],
            'floor': [p for p in personnel if p['assignment'] == 'floor' and p['status'] == 'working'],
            'section_leads': [p for p in personnel if p['assignment'] == 'section_leads' and p['status'] == 'working']
        }
        
        assignment_stats = {}
        for assignment, people in assignments.items():
            assignment_stats[assignment] = {
                'count': len(people),
                'personnel': [{'name': p['name'], 'rank': p['rank'], 'status': p['status']} for p in people]
            }
        
        return jsonify({
            'success': True,
            'stats': {
                'total_personnel': total_personnel,
                'military_count': military_count,
                'civilian_count': civilian_count,
                'working_count': working_count,
                'out_of_office_count': out_of_office_count
            },
            'assignments': assignment_stats,
            'timestamp': '2025-07-26T' + str(10 + (len(personnel) % 12)).zfill(2) + ':00:00'
        })
    
    except Exception as e:
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
                'assignment': person_info.get('assignment', 'unknown'),
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai-agent/message', methods=['POST'])
def api_ai_agent_message():
    """API endpoint for section leads to send messages to the AI agent"""
    try:
        data = request.get_json()
        message_text = data.get('message', '').strip()
        sender_id = data.get('sender_id', 'web_user')  # Could be user session ID
        
        if not message_text:
            return jsonify({
                'success': False,
                'error': 'Message text is required'
            }), 400
        
        # Create message data structure similar to email messages
        message_data = {
            'id': f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sender_id}",
            'message_text': message_text,
            'phone_number': f'web_user_{sender_id}',  # Identify as web user
            'source': 'web_interface',
            'timestamp': datetime.now().isoformat()
        }
        
        # Initialize GPT parser
        parser = GPTParser()
        
        # Check if this is a simple greeting or general message first
        simple_messages = ['hey', 'hello', 'hi', 'good morning', 'good afternoon', 'good evening', 'how are you', 'what can you do', 'help']
        is_simple_message = any(simple.lower() in message_text.lower() for simple in simple_messages)
        
        if is_simple_message:
            # Handle as a general query/greeting directly
            response = process_general_query(message_text, parser)
        else:
            # Try to process as a status command first
            status_result = parser.process_status_command(message_data, message_data['phone_number'])
            
            if status_result.get('success'):
                # This was a successful status command
                response = {
                    'success': True,
                    'message_type': 'status_command',
                    'ai_response': status_result.get('response_message', 'Command processed'),
                    'needs_clarification': False,
                    'person_updated': status_result.get('person_updated'),
                    'updates_made': status_result.get('updates_made', [])
                }
            elif status_result.get('needs_clarification'):
                # Status command needs clarification - only if it seems like a real command attempt
                confidence = status_result.get('confidence', 'low')
                if confidence in ['medium', 'high']:
                    response = {
                        'success': True,
                        'message_type': 'clarification',
                        'ai_response': status_result.get('response_message', 'I need more information'),
                        'needs_clarification': True,
                        'question': status_result.get('question', '')
                    }
                else:
                    # Low confidence - treat as general query instead
                    response = process_general_query(message_text, parser)
            elif status_result.get('message') == 'Not recognized as a status command':
                # Try processing as a general query/question
                response = process_general_query(message_text, parser)
            else:
                # Status command failed with an error
                response = {
                    'success': False,
                    'message_type': 'error',
                    'ai_response': status_result.get('response_message', 'I had trouble with that command. Please try again.'),
                    'needs_clarification': False
                }
        
        # Log the interaction
        print(f"Web interface message from {sender_id}: {message_text}")
        print(f"AI response: {response.get('ai_response', 'No response')}")
        print(f"Message type: {response.get('message_type', 'unknown')}")
        if response.get('person_updated'):
            person = response['person_updated']
            print(f"Person updated: {person.get('rank')} {person.get('name')} -> {person.get('assignment')}/{person.get('status')}")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error processing AI agent message: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'ai_response': 'Sorry, I encountered an error processing your message. Please try again.'
        }), 500

def process_general_query(message_text, parser):
    """Process general queries and questions from section leads"""
    try:
        # Handle simple greetings with predefined responses
        greetings = {
            'hey': "Hey there! I'm your FSS AI Agent. I can help you update personnel status, check appointments, or answer questions about section operations. Try: 'A1C Davis to admin room' or ask me about current staffing.",
            'hello': "Hello! I'm here to help with section operations. You can ask me about personnel assignments, update statuses, or check appointments. What do you need?",
            'hi': "Hi! I'm your AI assistant for the customer service section. I can help with personnel updates, appointment tracking, and operational questions. How can I assist you?",
            'good morning': "Good morning! Ready to help with today's operations. You can update personnel status, check assignments, or ask about appointments. What's on your agenda?",
            'good afternoon': "Good afternoon! How can I help with section operations today? I can assist with personnel updates, appointment management, or answer questions about staffing.",
            'good evening': "Good evening! Still here to help with any section needs. Whether it's personnel updates or checking tomorrow's schedule, I'm ready to assist.",
            'help': "I can help you with several things:\n• Update personnel: 'A1C Davis to admin room'\n• Check appointments: 'Who has appointments today?'\n• Personnel status: 'Who's available?'\n• Schedule leave: 'Smith on leave tomorrow'\n\nWhat would you like to do?",
            'what can you do': "I can help you:\n• Update personnel assignments (terminal, admin room, floor)\n• Track appointments and leave\n• Answer questions about current staffing\n• Schedule appointments for personnel\n• Provide operational status updates\n\nJust type your request naturally!"
        }
        
        message_lower = message_text.lower().strip()
        for greeting, response in greetings.items():
            if greeting in message_lower:
                return {
                    'success': True,
                    'message_type': 'greeting',
                    'ai_response': response,
                    'needs_clarification': False
                }
        
        # For other general queries, use Claude
        query_prompt = f"""
        You are an AI assistant for an Air Force customer service section operations dashboard. 
        A section lead has sent you a message that is not a status update command.
        
        This could be:
        1. A question about current staffing or appointments
        2. A request for information or statistics
        3. A general inquiry about operations
        
        Current context:
        - You have access to personnel assignments and appointment data
        - You can provide information about who's available, on appointments, etc.
        - Keep responses concise and professional
        
        Message: {message_text}
        
        Provide a helpful response. If you need specific data, indicate what type of information would be helpful.
        
        Respond in JSON format:
        {{
            "response_type": "information/question/help",
            "response_message": "Your response here",
            "needs_data": "personnel/appointments/both/none",
            "suggested_action": "string or null"
        }}
        """
        
        # Call Claude API
        response = parser.client.create_message(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.3,
            system="You are an AI assistant for military operations management. Respond only in valid JSON format.",
            messages=[
                {"role": "user", "content": query_prompt}
            ]
        )
        
        # Parse response
        gpt_response = response.content[0].text.strip()
        
        # Try to extract JSON from the response (sometimes Claude adds extra text)
        try:
            # Look for JSON block in the response
            if '{' in gpt_response and '}' in gpt_response:
                start = gpt_response.find('{')
                end = gpt_response.rfind('}') + 1
                json_text = gpt_response[start:end]
                parsed_response = json.loads(json_text)
            else:
                # If no JSON found, create a simple response
                parsed_response = {
                    "response_type": "information",
                    "response_message": gpt_response,
                    "needs_data": "none"
                }
        except json.JSONDecodeError:
            # Fallback to a simple response
            parsed_response = {
                "response_type": "information", 
                "response_message": "I understand your question. Let me help you with that.",
                "needs_data": "both"
            }
        
        # If the AI needs data, try to provide it
        response_message = parsed_response.get('response_message', 'I understand your question.')
        needs_data = parsed_response.get('needs_data', 'none')
        
        if needs_data in ['personnel', 'both']:
            # Add current personnel info to the response
            assignments = parser.get_personnel_assignments()
            personnel = assignments.get('personnel', [])
            
            # Count current assignments
            assignment_counts = {}
            for person in personnel:
                assignment = person.get('assignment', 'unknown')
                status = person.get('status', 'unknown')
                key = f"{assignment}_{status}"
                assignment_counts[key] = assignment_counts.get(key, 0) + 1
            
            # Enhance response with current data
            if 'terminals' in message_text.lower():
                terminal_count = len([p for p in personnel if p.get('assignment') == 'terminal'])
                response_message += f"\n\nCurrently {terminal_count} personnel assigned to terminals."
            elif 'available' in message_text.lower():
                available_count = len([p for p in personnel if p.get('status') == 'available'])
                response_message += f"\n\nCurrently {available_count} personnel available."
        
        if needs_data in ['appointments', 'both']:
            # Add appointment info if requested
            appointments = parser.get_pending_appointments()
            if 'today' in message_text.lower() or 'appointments' in message_text.lower():
                today_count = len([apt for apt in appointments if apt.get('appointment_date') == datetime.now().strftime('%Y-%m-%d')])
                response_message += f"\n\n{today_count} appointments scheduled for today."
        
        return {
            'success': True,
            'message_type': 'general_query',
            'ai_response': response_message,
            'needs_clarification': False
        }
        
    except Exception as e:
        print(f"Error processing general query: {e}")
        return {
            'success': True,
            'message_type': 'error',
            'ai_response': 'I had trouble understanding your question. Could you please rephrase it or be more specific?',
            'needs_clarification': True
        }

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("Starting FSS AI Agent Web Server...")
    print(f"Visit: http://localhost:{port}")
    app.run(debug=debug, host='0.0.0.0', port=port)