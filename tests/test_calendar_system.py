#!/usr/bin/env python3

from calendar_manager import CalendarManager
import json
from datetime import datetime, timedelta

def test_calendar_system():
    calendar = CalendarManager()
    
    print("=== Testing Calendar System ===")
    
    # Add a squadron event
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    event = calendar.add_event(
        title="Squadron PT",
        date=tomorrow,
        start_time="0730",
        end_time="0830",
        all_day=False
    )
    print(f"Added event: {event['title']} on {event['appointment_date']}")
    
    # Add a leave entry
    leave_entry = {
        'id': f"leave_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'category': 'leave',
        'personnel_name': 'SSgt Woodley',
        'personnel_rank': 'SSgt',
        'absence_type': 'leave',
        'appointment_date': tomorrow,
        'start_time': None,
        'end_time': None,
        'all_day': True,
        'status': 'active',
        'created_timestamp': datetime.now().isoformat(),
        'original_text': 'Testing leave entry',
        'created_by': 'test_system'
    }
    
    calendar.appointments.append(leave_entry)
    calendar._save_json_file(calendar.appointments_file, calendar.appointments)
    print(f"Added leave: {leave_entry['personnel_name']} on {leave_entry['appointment_date']}")
    
    # Test real-time status updates
    print("\n=== Testing Real-time Status Updates ===")
    updates = calendar.update_personnel_statuses()
    if updates:
        print(f"Status updates made: {updates}")
    else:
        print("No status updates needed at this time")
    
    # Show categorized events
    print("\n=== Events by Category ===")
    events_by_category = calendar.get_events_by_category()
    
    for category, data in events_by_category.items():
        print(f"\n{category.upper()} ({data['color']}):")
        for event in data['events']:
            if event.get('personnel_name'):
                print(f"  - {event['personnel_name']}: {event['appointment_date']} {event.get('start_time', 'All Day')}")
            else:
                print(f"  - {event.get('title', 'Event')}: {event['appointment_date']} {event.get('start_time', 'All Day')}")
    
    print(f"\n=== Total Events: {sum(len(data['events']) for data in events_by_category.values())} ===")

if __name__ == "__main__":
    test_calendar_system()