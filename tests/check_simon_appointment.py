#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('vera_system.db')
conn.row_factory = sqlite3.Row

appointment = conn.execute('SELECT * FROM appointments WHERE personnel_id = "pers_004"').fetchone()

print('Simon appointment details:')
for key in appointment.keys():
    print(f'  {key}: {appointment[key]}')

conn.close()