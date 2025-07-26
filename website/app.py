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

app = Flask(__name__)

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

if __name__ == '__main__':
    print("Starting FSS AI Agent Web Server...")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)