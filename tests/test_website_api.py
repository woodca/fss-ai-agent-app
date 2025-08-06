#!/usr/bin/env python3

from gpt_parser import GPTParser
import json
import os

def test_api_data():
    """Test what data the website API would return"""
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Looking for appointments.json at: {os.path.abspath('appointments.json')}")
    print(f"File exists: {os.path.exists('appointments.json')}")
    
    try:
        parser = GPTParser()
        
        print(f"\nRaw appointments loaded: {len(parser.appointments)}")
        if parser.appointments:
            print("Sample appointment:")
            print(json.dumps(parser.appointments[0], indent=2))
        
        appointments = parser.get_pending_appointments()
        print(f"Active appointments: {len(appointments)}")
        
        if appointments:
            print("\nFirst active appointment:")
            print(json.dumps(appointments[0], indent=2))
        
        # Test manning status
        manning = parser.get_manning_status(13)
        print(f"\nManning status:")
        print(f"  Currently out: {manning['currently_out']}")
        print(f"  Available: {manning['available']}")
        print(f"  Availability: {manning['availability_percentage']:.1f}%")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_data()