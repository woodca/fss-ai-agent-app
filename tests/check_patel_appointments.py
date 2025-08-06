#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import DatabaseManager

db = DatabaseManager()
patel = db.find_personnel('patel')

if patel:
    print(f'Patel ID: {patel["id"]}')
    print(f'Patel status: {patel["status"]}')
    
    appointments = db.get_personnel_appointments(patel['id'])
    print(f'Patel appointments: {len(appointments)}')
    
    for apt in appointments:
        print(f'- {apt["absence_type"]} on {apt["appointment_date"]} (ID: {apt.get("id", "unknown")})')
else:
    print('Patel not found in roster')