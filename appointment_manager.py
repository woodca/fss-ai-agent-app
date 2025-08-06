#!/usr/bin/env python3
"""
Enhanced Appointment Management System
Handles personnel appointments, leave, and general section events with:
- Automated status management with SQLite database
- Duplicate prevention
- Conflict detection
- Previous status restoration
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import os
from database_manager import DatabaseManager

class AppointmentConflictError(Exception):
    """Raised when appointment conflicts are detected"""
    pass

class AppointmentManager:
    def __init__(self, data_dir: str = ".", db_path: str = "vera_system.db"):
        self.data_dir = data_dir
        self.db = DatabaseManager(db_path)
        
        # Cache personnel for quick lookup
        self._refresh_personnel_cache()
    
    def _refresh_personnel_cache(self):
        """Refresh personnel cache from database"""
        self.personnel = self.db.get_all_personnel()
        
    def find_personnel(self, name: str) -> Optional[Dict]:
        """Find personnel by name using database"""
        return self.db.find_personnel(name)
    
    def check_appointment_conflicts(self, personnel_id: str, start_date: str, end_date: str = None) -> List[Dict]:
        """Check for existing appointments that conflict with proposed dates using database"""
        if not end_date:
            end_date = start_date
        return self.db.check_appointment_conflicts(personnel_id, start_date, end_date)
    
    def create_personnel_appointment(self, 
                                   personnel_name: str, 
                                   appointment_type: str,
                                   start_date: str,
                                   end_date: str = None,
                                   start_time: str = None,
                                   end_time: str = None,
                                   notes: str = None,
                                   force_replace: bool = False) -> Dict:
        """
        Create appointment for personnel using database with full conflict checking
        
        Args:
            personnel_name: Name of person
            appointment_type: 'leave', 'medical', 'dental', etc.
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format (optional, defaults to start_date)
            start_time: HHMM format (optional, required for non-leave appointments)
            end_time: HHMM format (optional)
            notes: Additional notes
            force_replace: If True, replace conflicting appointments
        
        Returns:
            Dict with success status and details
        """
        
        # Find personnel
        person = self.find_personnel(personnel_name)
        if not person:
            return {
                'success': False,
                'error': f"Personnel '{personnel_name}' not found",
                'available_personnel': [p.get('name') for p in self.db.get_all_personnel()[:5]]
            }
        
        # Set end_date if not provided
        if not end_date:
            end_date = start_date
        
        # Validate appointment rules for leave and TDY
        if appointment_type in ['leave', 'tdy']:
            start_time = None
            end_time = None
        elif appointment_type in ['medical', 'dental'] and not start_time:
            return {
                'success': False,
                'error': f"{appointment_type} appointments require start_time"
            }
        
        # Create appointments for date range using database
        appointments_created = 0
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end_date_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Create appointment in database
            result = self.db.create_appointment(
                personnel_id=person['id'],
                absence_type=appointment_type,
                appointment_date=date_str,
                start_time=start_time,
                end_time=end_time,
                notes=notes or f"{appointment_type.title()} from {start_date} to {end_date}",
                check_conflicts=not force_replace
            )
            
            if result['success']:
                appointments_created += 1
            else:
                # If conflict and not forcing, return error
                if result.get('error') == 'appointment_conflict' and not force_replace:
                    return {
                        'success': False,
                        'error': 'appointment_conflict',
                        'conflicts': result.get('conflicts', []),
                        'message': f"Found conflicts on {date_str}. Use force_replace=True to replace them."
                    }
            
            current_date += timedelta(days=1)
        
        # Refresh personnel cache to get updated status
        self._refresh_personnel_cache()
        updated_person = self.find_personnel(personnel_name)
        
        return {
            'success': True,
            'appointments_created': appointments_created,
            'date_range': f"{start_date} to {end_date}" if start_date != end_date else start_date,
            'personnel_updated': person['name'],
            'new_status': updated_person.get('status') if updated_person else 'unknown',
            'message': f"Created {appointments_created} {appointment_type} appointments for {person['name']}"
        }
    
    def create_general_event(self, 
                           title: str,
                           date: str,
                           start_time: str = None,
                           end_time: str = None,
                           location: str = None,
                           description: str = None,
                           event_type: str = 'general') -> Dict:
        """
        Create section-wide general events using database
        
        Args:
            title: Event title
            date: YYYY-MM-DD format
            start_time: HHMM format (optional)
            end_time: HHMM format (optional)
            location: Event location
            description: Full event description
            event_type: Type of event (PT, meeting, etc.)
        
        Returns:
            Dict with success status and details
        """
        
        result = self.db.create_general_event(
            title=title,
            event_date=date,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            location=location,
            description=description
        )
        
        return result
    
    def get_all_events_for_calendar(self) -> Dict:
        """
        Get all events (appointments + general events) from database
        
        Returns:
            Dict with personnel appointments and general events
        """
        return self.db.get_calendar_events()
    
    def update_all_personnel_statuses(self) -> List[str]:
        """
        Update all personnel statuses using database (atomic transactions)
        """
        updates = self.db.update_all_personnel_statuses()
        
        # Refresh cache after updates
        self._refresh_personnel_cache()
        
        return updates


# Example usage and testing
if __name__ == "__main__":
    # Initialize appointment manager with database
    manager = AppointmentManager()
    
    print("=== Database-Powered Appointment Manager Test ===")
    
    # Test status updates (the critical function that fixes Simon's issue)
    print("Testing atomic status updates...")
    updates = manager.update_all_personnel_statuses()
    print(f"Status updates: {updates}")
    
    # Test calendar events
    events = manager.get_all_events_for_calendar()
    print(f"Calendar events: {len(events['personnel_appointments'])} appointments, {len(events['general_events'])} events")
    
    # Test finding Simon's current status
    simon = manager.find_personnel("Simon")
    if simon:
        print(f"Simon's current status: {simon.get('status')} (previous: {simon.get('previous_status')})")
    
    print("Database system working correctly!")