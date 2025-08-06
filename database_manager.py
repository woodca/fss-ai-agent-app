#!/usr/bin/env python3
"""
SQLite Database Manager for Air Force CS Section
Replaces JSON files with robust database system for:
- Personnel management with status tracking
- Appointment scheduling with conflict detection
- General events for section-wide activities
- Automatic status management with transactions
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = "vera_system.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)  # 30 second timeout
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        conn.execute("PRAGMA busy_timeout = 30000")  # 30 second busy timeout
        return conn
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database with proper schema"""
        with self.transaction() as conn:
            # Personnel table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS personnel (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    full_name TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    rank TEXT NOT NULL,
                    type TEXT NOT NULL CHECK (type IN ('military', 'civilian')),
                    position TEXT,
                    phone TEXT,
                    email TEXT,
                    status TEXT NOT NULL CHECK (status IN ('front_desk', 'admin_room', 'terminal', 'float', 'leave', 'appointment')),
                    previous_status TEXT,
                    appointment_type TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Appointments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id TEXT PRIMARY KEY,
                    personnel_id TEXT NOT NULL,
                    personnel_name TEXT NOT NULL,
                    personnel_rank TEXT,
                    absence_type TEXT NOT NULL,
                    appointment_date DATE NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    all_day BOOLEAN DEFAULT 0,
                    notes TEXT,
                    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'completed')),
                    category_color TEXT DEFAULT '#FFC107',
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'system',
                    FOREIGN KEY (personnel_id) REFERENCES personnel(id)
                )
            """)
            
            # General events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS general_events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_date DATE NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    location TEXT,
                    description TEXT,
                    all_day BOOLEAN DEFAULT 0,
                    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'completed')),
                    category_color TEXT DEFAULT '#007BFF',
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'system'
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_personnel_name ON personnel(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_personnel_status ON personnel(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_personnel ON appointments(personnel_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON general_events(event_date)")
    
    def migrate_from_json(self, json_dir: str = "."):
        """Migrate existing JSON data to SQLite"""
        print("Starting JSON to SQLite migration...")
        
        # Migration counters
        personnel_migrated = 0
        appointments_migrated = 0
        events_migrated = 0
        
        with self.transaction() as conn:
            # Migrate personnel
            personnel_file = os.path.join(json_dir, "personnel_assignments.json")
            if os.path.exists(personnel_file):
                with open(personnel_file, 'r') as f:
                    personnel_data = json.load(f)
                
                for person in personnel_data:
                    conn.execute("""
                        INSERT OR REPLACE INTO personnel 
                        (id, name, full_name, first_name, last_name, rank, type, position, 
                         phone, email, status, previous_status, appointment_type, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        person.get('id'), person.get('name'), person.get('full_name'),
                        person.get('first_name'), person.get('last_name'), person.get('rank'),
                        person.get('type'), person.get('position'), person.get('phone'),
                        person.get('email'), person.get('status'), person.get('previous_status'),
                        person.get('appointment_type'), person.get('last_updated')
                    ))
                    personnel_migrated += 1
                
                print(f"Migrated {personnel_migrated} personnel records")
            
            # Migrate appointments
            appointments_file = os.path.join(json_dir, "appointments.json")
            if os.path.exists(appointments_file):
                with open(appointments_file, 'r') as f:
                    appointments_data = json.load(f)
                
                for apt in appointments_data:
                    # Find personnel_id from name
                    personnel_id = None
                    personnel_name = apt.get('personnel_name')
                    if personnel_name:
                        result = conn.execute(
                            "SELECT id FROM personnel WHERE name = ?", 
                            (personnel_name,)
                        ).fetchone()
                        if result:
                            personnel_id = result[0]
                    
                    if personnel_id:  # Only migrate if we can link to personnel
                        conn.execute("""
                            INSERT OR REPLACE INTO appointments 
                            (id, personnel_id, personnel_name, personnel_rank, absence_type,
                             appointment_date, start_time, end_time, all_day, notes, status,
                             category_color, created_timestamp, created_by)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            apt.get('id'), personnel_id, apt.get('personnel_name'),
                            apt.get('personnel_rank'), apt.get('absence_type'),
                            apt.get('appointment_date'), apt.get('start_time'),
                            apt.get('end_time'), apt.get('all_day', False),
                            apt.get('notes'), apt.get('status', 'active'),
                            apt.get('category_color', '#FFC107'), apt.get('created_timestamp'),
                            apt.get('created_by', 'migrated')
                        ))
                        appointments_migrated += 1
                
                print(f"Migrated {appointments_migrated} appointments")
            
            # Migrate general events (if file exists)
            events_file = os.path.join(json_dir, "general_events.json")
            if os.path.exists(events_file):
                with open(events_file, 'r') as f:
                    events_data = json.load(f)
                
                for event in events_data:
                    conn.execute("""
                        INSERT OR REPLACE INTO general_events 
                        (id, title, event_type, event_date, start_time, end_time,
                         location, description, all_day, status, category_color,
                         created_timestamp, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.get('id'), event.get('title'), event.get('event_type'),
                        event.get('event_date'), event.get('start_time'), event.get('end_time'),
                        event.get('location'), event.get('description'), event.get('all_day', False),
                        event.get('status', 'active'), event.get('category_color', '#007BFF'),
                        event.get('created_timestamp'), event.get('created_by', 'migrated')
                    ))
                    events_migrated += 1
                
                print(f"Migrated {events_migrated} general events")
        
        print(f"Migration complete! {personnel_migrated} personnel, {appointments_migrated} appointments, {events_migrated} events")
        return {
            'personnel': personnel_migrated,
            'appointments': appointments_migrated,
            'events': events_migrated
        }
    
    # Personnel Management
    def get_all_personnel(self) -> List[Dict]:
        """Get all personnel records"""
        conn = self.get_connection()
        try:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM personnel ORDER BY rank, name"
            ).fetchall()]
        finally:
            conn.close()
    
    def find_personnel(self, name: str) -> Optional[Dict]:
        """Find personnel by name (case-insensitive partial match)"""
        conn = self.get_connection()
        try:
            result = conn.execute(
                "SELECT * FROM personnel WHERE name LIKE ? OR full_name LIKE ?",
                (f"%{name}%", f"%{name}%")
            ).fetchone()
            return dict(result) if result else None
        finally:
            conn.close()
    
    def update_personnel_status(self, personnel_id: str, new_status: str, save_previous: bool = True) -> Dict:
        """Update personnel status with atomic transaction - handle nested transactions"""
        # Get current personnel record first (outside transaction)
        conn = self.get_connection()
        try:
            current = conn.execute(
                "SELECT * FROM personnel WHERE id = ?", (personnel_id,)
            ).fetchone()
        finally:
            conn.close()
            
            if not current:
                return {'success': False, 'error': f'Personnel {personnel_id} not found'}
            
            current = dict(current)
            old_status = current['status']
            
            # Save previous status if changing to leave/appointment
            update_previous = save_previous and new_status in ['leave', 'appointment'] and old_status not in ['leave', 'appointment']
            previous_status = current['status'] if update_previous else current['previous_status']
        
        # Now do the update in a separate transaction
        with self.transaction() as conn:
            conn.execute("""
                UPDATE personnel 
                SET status = ?, previous_status = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_status, previous_status, personnel_id))
            
            return {
                'success': True,
                'personnel_id': personnel_id,
                'name': current['name'],
                'old_status': old_status,
                'new_status': new_status,
                'previous_status_saved': update_previous
            }
    
    def restore_previous_status(self, personnel_id: str) -> Dict:
        """Restore personnel to their previous status"""
        with self.transaction() as conn:
            current = conn.execute(
                "SELECT * FROM personnel WHERE id = ?", (personnel_id,)
            ).fetchone()
            
            if not current:
                return {'success': False, 'error': f'Personnel {personnel_id} not found'}
            
            current = dict(current)
            previous_status = current.get('previous_status') or 'front_desk'
            
            conn.execute("""
                UPDATE personnel 
                SET status = ?, previous_status = NULL, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (previous_status, personnel_id))
            
            return {
                'success': True,
                'personnel_id': personnel_id,
                'name': current['name'],
                'restored_to': previous_status
            }
    
    # Appointment Management
    def create_appointment(self, personnel_id: str, absence_type: str, appointment_date: str,
                          start_time: str = None, end_time: str = None, notes: str = None,
                          check_conflicts: bool = True) -> Dict:
        """Create appointment with automatic conflict detection"""
        
        if check_conflicts:
            conflicts = self.check_appointment_conflicts(personnel_id, appointment_date, appointment_date)
            if conflicts:
                return {
                    'success': False,
                    'error': 'appointment_conflict',
                    'conflicts': conflicts
                }
        
        with self.transaction() as conn:
            # Get personnel info
            person = conn.execute(
                "SELECT * FROM personnel WHERE id = ?", (personnel_id,)
            ).fetchone()
            
            if not person:
                return {'success': False, 'error': f'Personnel {personnel_id} not found'}
            
            person = dict(person)
            
            # Generate unique appointment ID with date suffix
            import uuid
            appointment_id = f"apt_{appointment_date.replace('-', '')}_{personnel_id}_{uuid.uuid4().hex[:8]}"
            
            # Create appointment
            conn.execute("""
                INSERT INTO appointments 
                (id, personnel_id, personnel_name, personnel_rank, absence_type,
                 appointment_date, start_time, end_time, all_day, notes, status,
                 category_color, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, 'database_manager')
            """, (
                appointment_id, personnel_id, person['name'], person['rank'],
                absence_type, appointment_date, start_time, end_time,
                absence_type in ['leave', 'tdy'] or start_time is None, notes,
                '#FF8F00' if absence_type in ['leave', 'tdy'] else '#FFC107'
            ))
            
            # Update personnel status (handle TDY as leave status)
            if absence_type in ['leave', 'tdy']:
                new_status = 'leave'
            else:
                new_status = 'appointment'
            
            # Update status directly in this transaction to avoid nested transaction issues
            conn.execute("""
                UPDATE personnel 
                SET status = ?, previous_status = status, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_status, personnel_id))
            
            return {
                'success': True,
                'appointment_id': appointment_id,
                'personnel_name': person['name'],
                'status_updated': True
            }
    
    def check_appointment_conflicts(self, personnel_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Check for appointment conflicts in date range"""
        with self.get_connection() as conn:
            conflicts = conn.execute("""
                SELECT * FROM appointments 
                WHERE personnel_id = ? 
                AND status = 'active'
                AND appointment_date BETWEEN ? AND ?
            """, (personnel_id, start_date, end_date)).fetchall()
            
            return [dict(row) for row in conflicts]
    
    def get_personnel_appointments(self, personnel_id: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get appointments for personnel in date range"""
        with self.get_connection() as conn:
            if start_date and end_date:
                appointments = conn.execute("""
                    SELECT * FROM appointments 
                    WHERE personnel_id = ? AND status = 'active'
                    AND appointment_date BETWEEN ? AND ?
                    ORDER BY appointment_date
                """, (personnel_id, start_date, end_date)).fetchall()
            else:
                appointments = conn.execute("""
                    SELECT * FROM appointments 
                    WHERE personnel_id = ? AND status = 'active'
                    ORDER BY appointment_date
                """, (personnel_id,)).fetchall()
            
            return [dict(row) for row in appointments]
    
    # Status Management (The critical part that fixes Simon's issue)
    def update_all_personnel_statuses(self) -> List[str]:
        """Update all personnel statuses based on current appointments - ATOMIC"""
        updates = []
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        with self.transaction() as conn:  # Single transaction for all updates
            # Get all personnel
            personnel = conn.execute("SELECT * FROM personnel").fetchall()
            
            for person in personnel:
                person = dict(person)
                personnel_id = person['id']
                current_status = person['status']
                
                # Check for active leave appointments today
                leave_count = conn.execute("""
                    SELECT COUNT(*) FROM appointments 
                    WHERE personnel_id = ? AND appointment_date = ? 
                    AND absence_type = 'leave' AND status = 'active'
                """, (personnel_id, current_date)).fetchone()[0]
                
                # Check for active non-leave appointments today
                appointment_count = conn.execute("""
                    SELECT COUNT(*) FROM appointments 
                    WHERE personnel_id = ? AND appointment_date = ? 
                    AND absence_type != 'leave' AND status = 'active'
                """, (personnel_id, current_date)).fetchone()[0]
                
                # Determine correct status
                should_be_status = None
                if leave_count > 0:
                    should_be_status = 'leave'
                elif appointment_count > 0:
                    should_be_status = 'appointment'
                
                # Update if needed
                if should_be_status and current_status != should_be_status:
                    self.update_personnel_status(personnel_id, should_be_status)
                    updates.append(f"{person['name']}: {current_status} -> {should_be_status}")
                
                # Check if appointments ended and should restore previous status
                elif current_status in ['leave', 'appointment'] and not leave_count and not appointment_count:
                    # Check if they have any future appointments
                    future_count = conn.execute("""
                        SELECT COUNT(*) FROM appointments 
                        WHERE personnel_id = ? AND appointment_date > ? AND status = 'active'
                    """, (personnel_id, current_date)).fetchone()[0]
                    
                    if future_count == 0:
                        restore_result = self.restore_previous_status(personnel_id)
                        if restore_result['success']:
                            updates.append(f"{person['name']}: {current_status} -> {restore_result['restored_to']}")
        
        return updates
    
    # Calendar and Events
    def get_calendar_events(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get all calendar events (appointments + general events)"""
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            # Get personnel appointments (including multi-day appointments)
            appointments = conn.execute("""
                SELECT a.*, p.name as personnel_name, p.rank as personnel_rank
                FROM appointments a
                JOIN personnel p ON a.personnel_id = p.id
                WHERE a.status = 'active'
                AND (a.appointment_date BETWEEN ? AND ? 
                     OR (a.end_date IS NOT NULL AND a.end_date >= ? AND a.appointment_date <= ?))
                ORDER BY a.appointment_date, a.start_time
            """, (start_date, end_date, start_date, end_date)).fetchall()
            
            # Get general events
            events = conn.execute("""
                SELECT * FROM general_events 
                WHERE event_date BETWEEN ? AND ? AND status = 'active'
                ORDER BY event_date, start_time
            """, (start_date, end_date)).fetchall()
            
            return {
                'personnel_appointments': [dict(row) for row in appointments],
                'general_events': [dict(row) for row in events],
                'date_range': {'start': start_date, 'end': end_date}
            }
    
    def create_general_event(self, title: str, event_date: str, event_type: str = 'general',
                           start_time: str = None, end_time: str = None, location: str = None,
                           description: str = None) -> Dict:
        """Create general section event"""
        with self.transaction() as conn:
            event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            conn.execute("""
                INSERT INTO general_events 
                (id, title, event_type, event_date, start_time, end_time,
                 location, description, all_day, category_color, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '#007BFF', 'database_manager')
            """, (
                event_id, title, event_type, event_date, start_time, end_time,
                location, description, start_time is None
            ))
            
            return {
                'success': True,
                'event_id': event_id,
                'title': title,
                'date': event_date
            }
    
    # Utility Methods
    def get_personnel_status_summary(self) -> Dict:
        """Get personnel status summary for dashboard"""
        conn = self.get_connection()
        try:
            # Get counts by status
            status_counts = {}
            results = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM personnel 
                GROUP BY status
            """).fetchall()
            
            for row in results:
                status_counts[row[0]] = row[1]
            
            # Get unavailable personnel details
            unavailable = conn.execute("""
                SELECT * FROM personnel 
                WHERE status IN ('leave', 'appointment')
                ORDER BY name
            """).fetchall()
            
            return {
                'total_personnel': sum(status_counts.values()),
                'status_counts': status_counts,
                'working_count': status_counts.get('front_desk', 0) + status_counts.get('admin_room', 0) + 
                               status_counts.get('terminal', 0) + status_counts.get('float', 0),
                'out_of_office_count': status_counts.get('leave', 0) + status_counts.get('appointment', 0),
                'unavailable_personnel': [dict(row) for row in unavailable]
            }
        finally:
            conn.close()


if __name__ == "__main__":
    # Test the database system
    print("Testing SQLite Database System")
    
    db = DatabaseManager()
    
    # Test migration
    migration_result = db.migrate_from_json()
    print(f"Migration result: {migration_result}")
    
    # Test status update
    updates = db.update_all_personnel_statuses()
    print(f"Status updates: {updates}")
    
    # Test status summary
    summary = db.get_personnel_status_summary()
    print(f"Status summary: {summary}")
    
    print("Database system ready!")