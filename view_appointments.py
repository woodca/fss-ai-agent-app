#!/usr/bin/env python3

from gpt_parser import GPTParser
from datetime import datetime, date
import json

def view_appointments():
    """Display all appointments in a calendar-like view"""
    
    try:
        parser = GPTParser()
        appointments = parser.get_pending_appointments()
        
        print("=" * 80)
        print("APPOINTMENT CALENDAR VIEW")
        print("=" * 80)
        
        if not appointments:
            print("No appointments currently stored.\n")
            return
        
        # Group appointments by date
        appointments_by_date = {}
        today = date.today()
        
        for apt in appointments:
            apt_date = apt.get('appointment_date', 'Unknown')
            if apt_date not in appointments_by_date:
                appointments_by_date[apt_date] = []
            appointments_by_date[apt_date].append(apt)
        
        # Sort dates
        sorted_dates = sorted(appointments_by_date.keys())
        
        for apt_date in sorted_dates:
            try:
                date_obj = datetime.fromisoformat(apt_date).date()
                is_today = date_obj == today
                
                # Format date display
                date_display = date_obj.strftime('%A, %B %d, %Y')
                if is_today:
                    date_display += " (TODAY)"
                
                print(f"\n{date_display}")
                print("-" * len(date_display))
                
            except:
                print(f"\n{apt_date}")
                print("-" * 20)
            
            # Sort appointments by time for this date
            date_appointments = sorted(appointments_by_date[apt_date], 
                                     key=lambda x: x.get('start_time', '0000'))
            
            for apt in date_appointments:
                name = apt.get('personnel_name', 'Unknown')
                rank = apt.get('personnel_rank', '')
                absence_type = apt.get('absence_type', 'unknown')
                
                # Format time display
                if apt.get('all_day', False):
                    time_display = "All Day"
                else:
                    start_time = apt.get('start_time', 'Unknown')
                    end_time = apt.get('end_time')
                    
                    if start_time and start_time != 'Unknown':
                        # Format military time
                        try:
                            hour = int(start_time[:2])
                            minute = int(start_time[2:]) if len(start_time) > 2 else 0
                            time_str = f"{hour:02d}:{minute:02d}"
                            
                            if end_time:
                                end_hour = int(end_time[:2])
                                end_minute = int(end_time[2:]) if len(end_time) > 2 else 0
                                end_str = f"{end_hour:02d}:{end_minute:02d}"
                                time_display = f"{time_str} - {end_str}"
                            else:
                                time_display = f"{time_str}+"
                        except:
                            time_display = start_time
                    else:
                        time_display = "Time TBD"
                
                # Display appointment
                print(f"  - {time_display:12} | {name:15} | {absence_type.title():15} |")
                
                # Show original message if available
                original_text = apt.get('original_text', '')
                if original_text:
                    print(f"    -> \"{original_text}\"")
                
                print(f"    -> ID: {apt.get('id', 'Unknown')}")
                print()
        
        # Summary statistics
        print("=" * 80) 
        print("SUMMARY")
        print("=" * 80)
        print(f"Total appointments: {len(appointments)}")
        
        # Count by type
        type_counts = {}
        for apt in appointments:
            apt_type = apt.get('absence_type', 'unknown')
            type_counts[apt_type] = type_counts.get(apt_type, 0) + 1
        
        print("By type:")
        for apt_type, count in sorted(type_counts.items()):
            print(f"  {apt_type.title()}: {count}")
        
        # Manning status
        print(f"\nManning Status:")
        manning = parser.get_manning_status(13)  # Assuming 13 total personnel
        print(f"  Currently out: {manning['currently_out']}")
        print(f"  Available: {manning['available']}")
        print(f"  Availability: {manning['availability_percentage']:.1f}%")
        
        if manning['out_details']:
            print(f"\n  Who's currently out:")
            for person in manning['out_details']:
                print(f"    - {person['phone']} ({person['type']}) - {person['time']}")
        
        print()
        
    except Exception as e:
        print(f"Error displaying appointments: {e}")

if __name__ == "__main__":
    view_appointments()