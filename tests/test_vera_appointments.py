#!/usr/bin/env python3
"""
Comprehensive Test Suite for Vera Appointment System
Tests all appointment functionality including:
- Personnel appointments with conflict detection
- Leave management with status automation
- General event processing
- Duplicate prevention
- Status restoration
"""

import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from appointment_manager import AppointmentManager
from vera_agent import VeraAgent

class TestVeraAppointments:
    def __init__(self):
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp(prefix="vera_test_")
        self.original_dir = os.getcwd()
        
        # Setup test data
        self.setup_test_data()
        
        # Initialize managers
        os.chdir(self.test_dir)
        self.appointment_manager = AppointmentManager(self.test_dir)
        
        # We'll mock Vera for testing since we need API key
        self.vera_responses = []
    
    def setup_test_data(self):
        """Create test personnel data"""
        test_personnel = [
            {
                "id": "pers_001",
                "name": "SSgt Simon",
                "full_name": "SSgt Simon",
                "rank": "SSgt",
                "type": "military",
                "status": "float",
                "previous_status": None,
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": "pers_002", 
                "name": "SrA Taylor",
                "full_name": "SrA Taylor",
                "rank": "SrA",
                "type": "military",
                "status": "front_desk",
                "previous_status": None,
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": "pers_003",
                "name": "A1C Rodriguez", 
                "full_name": "A1C Rodriguez",
                "rank": "A1C",
                "type": "military",
                "status": "terminal",
                "previous_status": None,
                "last_updated": datetime.now().isoformat()
            }
        ]
        
        # Save test data
        personnel_file = os.path.join(self.test_dir, "personnel_assignments.json")
        with open(personnel_file, 'w') as f:
            json.dump(test_personnel, f, indent=2)
        
        # Create empty appointments and events files
        appointments_file = os.path.join(self.test_dir, "appointments.json")
        events_file = os.path.join(self.test_dir, "general_events.json")
        
        with open(appointments_file, 'w') as f:
            json.dump([], f)
        with open(events_file, 'w') as f:
            json.dump([], f)
    
    def cleanup(self):
        """Clean up test files"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_personnel_leave_appointment(self):
        """Test creating leave appointments for personnel"""
        print("\n=== Testing Personnel Leave Appointments ===")
        
        # Test single day leave
        result = self.appointment_manager.create_personnel_appointment(
            personnel_name="Simon",
            appointment_type="leave",
            start_date="2025-08-06"
        )
        
        assert result['success'], f"Single day leave failed: {result}"
        assert result['appointments_created'] == 1
        print(f"✅ Single day leave: {result['message']}")
        
        # Test multi-day leave
        result = self.appointment_manager.create_personnel_appointment(
            personnel_name="Taylor",
            appointment_type="leave", 
            start_date="2025-08-07",
            end_date="2025-08-09"
        )
        
        assert result['success'], f"Multi-day leave failed: {result}"
        assert result['appointments_created'] == 3  # 3 days
        print(f"✅ Multi-day leave: {result['message']}")
        
        # Verify status changes
        simon = self.appointment_manager.find_personnel("Simon")
        taylor = self.appointment_manager.find_personnel("Taylor")
        
        assert simon['status'] == 'leave', f"Simon status not updated: {simon['status']}"
        assert simon['previous_status'] == 'float', f"Simon previous status not saved: {simon['previous_status']}"
        
        assert taylor['status'] == 'leave', f"Taylor status not updated: {taylor['status']}"
        assert taylor['previous_status'] == 'front_desk', f"Taylor previous status not saved: {taylor['previous_status']}"
        
        print("✅ Personnel statuses updated correctly")
    
    def test_medical_appointment(self):
        """Test creating medical appointments"""
        print("\n=== Testing Medical Appointments ===")
        
        result = self.appointment_manager.create_personnel_appointment(
            personnel_name="Rodriguez",
            appointment_type="medical",
            start_date="2025-08-06",
            start_time="0900",
            end_time="1100",
            notes="Annual checkup"
        )
        
        assert result['success'], f"Medical appointment failed: {result}"
        print(f"✅ Medical appointment: {result['message']}")
        
        # Verify status change
        rodriguez = self.appointment_manager.find_personnel("Rodriguez")
        assert rodriguez['status'] == 'appointment', f"Rodriguez status not updated: {rodriguez['status']}"
        assert rodriguez['previous_status'] == 'terminal', f"Rodriguez previous status not saved"
        
        print("✅ Medical appointment status updated correctly")
    
    def test_conflict_detection(self):
        """Test appointment conflict detection"""
        print("\n=== Testing Conflict Detection ===")
        
        # Try to schedule appointment on same day as existing leave
        result = self.appointment_manager.create_personnel_appointment(
            personnel_name="Simon",  # Already has leave on 2025-08-06
            appointment_type="medical",
            start_date="2025-08-06",
            start_time="1000"
        )
        
        assert not result['success'], "Conflict detection failed - should have detected conflict"
        assert result['error'] == 'appointment_conflict'
        assert len(result['conflicts']) > 0
        print(f"✅ Conflict detected: {result['message']}")
        
        # Test force replace
        result = self.appointment_manager.create_personnel_appointment(
            personnel_name="Simon",
            appointment_type="medical", 
            start_date="2025-08-06",
            start_time="1000",
            force_replace=True
        )
        
        assert result['success'], f"Force replace failed: {result}"
        assert result['conflicts_replaced'] > 0
        print(f"✅ Force replace worked: {result['message']}")
    
    def test_general_events(self):
        """Test creating general section events"""
        print("\n=== Testing General Events ===")
        
        # Test PT event
        result = self.appointment_manager.create_general_event(
            title="Section PT",
            date="2025-08-06",
            start_time="0630",
            location="Pier on BayShore",
            description="Mandatory PT for all personnel. Air Force PT gear required.",
            event_type="PT"
        )
        
        assert result['success'], f"PT event failed: {result}"
        print(f"✅ PT event: {result['message']}")
        
        # Test meeting event
        result = self.appointment_manager.create_general_event(
            title="All Hands Meeting",
            date="2025-08-07", 
            start_time="1400",
            location="Conference Room",
            description="Monthly section meeting for all personnel",
            event_type="meeting"
        )
        
        assert result['success'], f"Meeting event failed: {result}"
        print(f"✅ Meeting event: {result['message']}")
    
    def test_status_restoration(self):
        """Test automatic status restoration when appointments end"""
        print("\n=== Testing Status Restoration ===")
        
        # Create appointment ending today
        today = datetime.now().strftime('%Y-%m-%d')
        result = self.appointment_manager.create_personnel_appointment(
            personnel_name="Rodriguez",
            appointment_type="leave",
            start_date=today
        )
        
        assert result['success'], "Failed to create test leave"
        
        # Verify status is leave
        rodriguez = self.appointment_manager.find_personnel("Rodriguez")
        assert rodriguez['status'] == 'leave'
        
        # Test ending appointments (simulate day after)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        restored = self.appointment_manager.end_appointments_for_date(tomorrow)
        
        # Should restore Rodriguez since his leave ended
        assert len(restored) > 0, "No personnel were restored"
        print(f"✅ Personnel restored: {restored}")
        
        # Verify status restored
        rodriguez = self.appointment_manager.find_personnel("Rodriguez")
        assert rodriguez['status'] == 'appointment', f"Rodriguez status not restored correctly: {rodriguez['status']}"
    
    def test_calendar_integration(self):
        """Test calendar data retrieval"""
        print("\n=== Testing Calendar Integration ===")
        
        events = self.appointment_manager.get_all_events_for_calendar()
        
        assert 'personnel_appointments' in events
        assert 'general_events' in events
        
        personnel_count = events['total_personnel_appointments']
        general_count = events['total_general_events']
        
        print(f"✅ Calendar integration: {personnel_count} personnel appointments, {general_count} general events")
        
        # Verify color coding
        for apt in events['personnel_appointments']:
            assert 'category_color' in apt, "Missing category_color in appointment"
            
        for event in events['general_events']:
            assert event['category_color'] == '#007BFF', "General events should be blue"
            
        print("✅ Color coding verified")
    
    def test_vera_message_parsing(self):
        """Test Vera's ability to parse different message types"""
        print("\n=== Testing Vera Message Parsing ===")
        
        # We'd test these if we had Vera initialized with API key
        test_messages = [
            "simon is on leave until friday",
            "Taylor has a medical appointment tomorrow at 0900",
            "PT at 0630 tomorrow at the pier, mandatory for all",
            "All hands meeting at 1400 in conference room"
        ]
        
        for message in test_messages:
            print(f"  📝 Would test: '{message}'")
        
        print("✅ Message parsing test cases identified")
    
    def run_all_tests(self):
        """Run all test cases"""
        print("🚀 Starting Vera Appointment System Tests")
        print(f"📁 Test directory: {self.test_dir}")
        
        try:
            self.test_personnel_leave_appointment()
            self.test_medical_appointment()
            self.test_conflict_detection()
            self.test_general_events()
            self.test_status_restoration()
            self.test_calendar_integration()
            self.test_vera_message_parsing()
            
            print("\n🎉 All tests passed!")
            return True
            
        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
            return False
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
            return False
        finally:
            self.cleanup()


if __name__ == "__main__":
    tester = TestVeraAppointments()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Vera appointment system is working correctly!")
        exit(0)
    else:
        print("\n❌ Tests failed - system needs fixes")
        exit(1)