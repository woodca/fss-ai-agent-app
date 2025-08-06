#!/usr/bin/env python3
"""
Test the Flask endpoint directly without running the server
"""

import sys
import os
sys.path.append('.')

# Set working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager

def test_endpoint_logic():
    """Test the exact logic from the Flask endpoint"""
    print("Testing Flask endpoint logic...")
    
    try:
        # Initialize database manager
        db = DatabaseManager()
        
        print("Getting personnel status from database...")
        
        # Get personnel status summary from database
        summary = db.get_personnel_status_summary()
        personnel_list = db.get_all_personnel()
        
        print(f"Summary: {summary}")
        print(f"Personnel list count: {len(personnel_list)}")
        
        # Group personnel by status/assignment
        assignments = {
            'floor': {'personnel': []},
            'admin_room': {'personnel': []}, 
            'terminal': {'personnel': []},
            'float': {'personnel': []}
        }
        
        for person in personnel_list:
            status = person.get('status', 'unknown')
            print(f"Processing person: {person.get('name')} with status: {status}")
            
            # Map status to assignment categories
            if status in ['front_desk', 'working']:
                assignments['floor']['personnel'].append(person)
            elif status == 'admin_room':
                assignments['admin_room']['personnel'].append(person)
            elif status == 'terminal':
                assignments['terminal']['personnel'].append(person)
            elif status == 'float':
                assignments['float']['personnel'].append(person)
            # For leave/appointment, they won't be in assignments but will be in out_of_office
        
        # Get unavailable personnel details
        unavailable_personnel = summary.get('unavailable_personnel', [])
        
        # Calculate military vs civilian counts
        military_count = sum(1 for p in personnel_list if p.get('type') == 'military')
        civilian_count = sum(1 for p in personnel_list if p.get('type') == 'civilian')
        
        # Add count field to assignments
        for assignment_key in assignments:
            assignments[assignment_key]['count'] = len(assignments[assignment_key]['personnel'])
        
        stats = {
            'total_personnel': summary.get('total_personnel', 0),
            'military_count': military_count,
            'civilian_count': civilian_count,
            'working_count': summary.get('working_count', 0),
            'out_of_office_count': summary.get('out_of_office_count', 0)
        }
        
        result = {
            'success': True,
            'stats': stats,
            'assignments': assignments,
            'unavailable_personnel': unavailable_personnel,
            'debug_info': {
                'source': 'database',
                'status_counts': summary.get('status_counts', {})
            }
        }
        
        print(f"Final result stats: {result['stats']}")
        print(f"Assignment counts:")
        for key, value in result['assignments'].items():
            print(f"  {key}: {value['count']} personnel")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_endpoint_logic()