#!/usr/bin/env python3

from gpt_parser import GPTParser
import json
from datetime import datetime, date

def test_manning_calculation():
    """Test manning calculation functionality"""
    
    try:
        parser = GPTParser()
        print("Testing manning calculation...\n")
        
        # Clear existing appointments for clean test
        parser.appointments = []
        
        # Add some test appointments for today
        today_str = date.today().isoformat()
        current_hour = datetime.now().hour
        
        # Create realistic test appointments
        test_appointments = [
            {
                'id': 'test_dental_1',
                'phone_number': '+1555000001',
                'absence_type': 'dental',
                'appointment_date': today_str,
                'start_time': f"{current_hour-1:02d}00",  # Started 1 hour ago
                'end_time': f"{current_hour+1:02d}00",    # Ends in 1 hour
                'all_day': False,
                'affects_manning': True,
                'status': 'active'
            },
            {
                'id': 'test_medical_1', 
                'phone_number': '+1555000002',
                'absence_type': 'medical',
                'appointment_date': today_str,
                'start_time': f"{current_hour+2:02d}00",  # Starts in 2 hours
                'end_time': f"{current_hour+3:02d}00",    # Future appointment
                'all_day': False,
                'affects_manning': True,
                'status': 'active'
            },
            {
                'id': 'test_leave_1',
                'phone_number': '+1555000003', 
                'absence_type': 'leave',
                'appointment_date': today_str,
                'all_day': True,
                'affects_manning': True,
                'status': 'active'
            },
            {
                'id': 'test_personal_1',
                'phone_number': '+1555000004',
                'absence_type': 'personal_business', 
                'appointment_date': today_str,
                'start_time': f"{current_hour-2:02d}00",  # Already returned
                'end_time': f"{current_hour-1:02d}00",
                'all_day': False,
                'affects_manning': True,
                'status': 'active'
            }
        ]
        
        # Add test appointments
        parser.appointments = test_appointments
        
        # Test manning calculation with different personnel counts
        for total_personnel in [10, 15, 20]:
            print(f"Manning Status for {total_personnel} total personnel:")
            
            manning = parser.get_manning_status(total_personnel)
            
            print(f"   Currently Out: {manning['currently_out']}")
            print(f"   Available: {manning['available']}")
            print(f"   Availability: {manning['availability_percentage']:.1f}%")
            print("   Who's Out:")
            
            for person in manning['out_details']:
                print(f"      - {person['phone']} ({person['type']}) - {person['time']}")
            
            print()
        
        # Test without total personnel specified
        print("Manning Status (no total specified):")
        manning = parser.get_manning_status()
        print(f"   Currently Out: {manning['currently_out']}")
        print(f"   Available: {manning['available']}")
        print(f"   Timestamp: {manning['timestamp']}")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_manning_calculation()