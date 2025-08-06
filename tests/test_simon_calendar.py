#!/usr/bin/env python3

import requests
import json

try:
    response = requests.get('http://localhost:5000/api/appointments')
    print('API response status:', response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total appointments: {data['total_appointments']}")
        
        simon_apts = [apt for apt in data['appointments'] if 'simon' in apt.get('personnel_name', '').lower()]
        print(f'Simon appointments in API: {len(simon_apts)}')
        
        for apt in simon_apts:
            print(f"- {apt['absence_type']} on {apt['appointment_date']}")
            if apt.get('end_date'):
                print(f"  End date: {apt['end_date']}")
            else:
                print(f"  No end_date field found")
            print(f"  All fields: {list(apt.keys())}")
            print(f"  Raw appointment: {apt}")
            
    else:
        print('API Error:', response.text)
        
except Exception as e:
    print(f'Connection error: {e}')
    print('Make sure the Flask server is running on localhost:5000')