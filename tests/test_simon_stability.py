#!/usr/bin/env python3
"""
Test Simon's status stability with database system
Verify that his status doesn't revert from 'leave' back to 'appointment'
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from appointment_manager import AppointmentManager
import time

def test_simon_stability():
    manager = AppointmentManager()
    
    print("=== Testing Simon's Status Stability ===")
    
    # Run status updates multiple times to test stability
    for i in range(5):
        print(f"\n--- Update Round {i+1} ---")
        
        # Check Simon's status before update
        simon_before = manager.find_personnel("Simon")
        print(f"Before update: {simon_before.get('status')} (previous: {simon_before.get('previous_status')})")
        
        # Run status update
        updates = manager.update_all_personnel_statuses()
        print(f"Updates made: {updates}")
        
        # Check Simon's status after update
        simon_after = manager.find_personnel("Simon")
        print(f"After update: {simon_after.get('status')} (previous: {simon_after.get('previous_status')})")
        
        # Verify status didn't change incorrectly
        if simon_before.get('status') == 'leave' and simon_after.get('status') != 'leave':
            print("ERROR: Simon's leave status was incorrectly changed!")
            return False
        elif simon_before.get('status') == simon_after.get('status'):
            print("Status stable - no incorrect changes")
        else:
            print(f"Status changed: {simon_before.get('status')} -> {simon_after.get('status')}")
        
        time.sleep(1)  # Small delay between tests
    
    print("\n=== Final Status Check ===")
    final_simon = manager.find_personnel("Simon")
    print(f"Simon's final status: {final_simon.get('status')} (previous: {final_simon.get('previous_status')})")
    
    # Check his active appointments
    appointments = manager.db.get_personnel_appointments("pers_004")  # Simon's ID
    active_leave = [apt for apt in appointments if apt.get('absence_type') == 'leave' and apt.get('status') == 'active']
    print(f"Simon has {len(active_leave)} active leave appointments")
    
    if active_leave and final_simon.get('status') == 'leave':
        print("SUCCESS: Simon's status is correctly 'leave' and matches his active appointments!")
        return True
    else:
        print("ISSUE: Status doesn't match appointments or something is wrong")
        return False

if __name__ == "__main__":
    success = test_simon_stability()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")