#!/usr/bin/env python3

import requests
import json

try:
    response = requests.get('http://localhost:5000/api/appointments')
    print('API response status:', response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total appointments: {data['total_appointments']}")
        
        patel_apts = [apt for apt in data['appointments'] if 'patel' in apt.get('personnel_name', '').lower()]
        print(f'Patel appointments in API: {len(patel_apts)}')
        
        for apt in patel_apts[:5]:  # Show first 5 appointments
            print(f"- {apt['absence_type']} on {apt['appointment_date']}")
            if apt.get('end_date'):
                print(f"  End date: {apt['end_date']}")
            print(f"  All day: {apt.get('all_day', False)}")
            print(f"  Category color: {apt.get('category_color', 'none')}")
            
        if len(patel_apts) > 5:
            print(f"... and {len(patel_apts) - 5} more appointments")
            
    else:
        print('API Error:', response.text)
        
except Exception as e:
    print(f'Connection error: {e}')
    print('Make sure the Flask server is running on localhost:5000')