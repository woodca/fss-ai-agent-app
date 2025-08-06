#!/usr/bin/env python3
"""
Test database connectivity and data retrieval
"""

from database_manager import DatabaseManager
import json

def test_database():
    """Test database methods"""
    print("Testing DatabaseManager...")
    
    try:
        db = DatabaseManager()
        
        # Test get_all_personnel
        print("\n1. Testing get_all_personnel():")
        personnel = db.get_all_personnel()
        print(f"   Found {len(personnel)} personnel records")
        if personnel:
            print(f"   First person: {personnel[0].get('name')} - {personnel[0].get('status')}")
        
        # Test get_personnel_status_summary
        print("\n2. Testing get_personnel_status_summary():")
        summary = db.get_personnel_status_summary()
        print(f"   Total personnel: {summary.get('total_personnel')}")
        print(f"   Status counts: {summary.get('status_counts')}")
        print(f"   Working count: {summary.get('working_count')}")
        print(f"   Out of office count: {summary.get('out_of_office_count')}")
        print(f"   Unavailable personnel: {len(summary.get('unavailable_personnel', []))}")
        
        # Test the exact data structure that the API should return
        print("\n3. Simulating API response structure:")
        
        # Calculate military vs civilian counts
        military_count = sum(1 for p in personnel if p.get('type') == 'military')
        civilian_count = sum(1 for p in personnel if p.get('type') == 'civilian')
        
        # Group personnel by status/assignment
        assignments = {
            'floor': {'personnel': []},
            'admin_room': {'personnel': []}, 
            'terminal': {'personnel': []},
            'float': {'personnel': []}
        }
        
        for person in personnel:
            status = person.get('status', 'unknown')
            
            # Map status to assignment categories
            if status in ['front_desk', 'working']:
                assignments['floor']['personnel'].append(person)
            elif status == 'admin_room':
                assignments['admin_room']['personnel'].append(person)
            elif status == 'terminal':
                assignments['terminal']['personnel'].append(person)
            elif status == 'float':
                assignments['float']['personnel'].append(person)
        
        # Add count field to assignments
        for assignment_key in assignments:
            assignments[assignment_key]['count'] = len(assignments[assignment_key]['personnel'])
        
        # Get unavailable personnel details
        unavailable_personnel = summary.get('unavailable_personnel', [])
        
        stats = {
            'total_personnel': summary.get('total_personnel', 0),
            'military_count': military_count,
            'civilian_count': civilian_count,
            'working_count': summary.get('working_count', 0),
            'out_of_office_count': summary.get('out_of_office_count', 0)
        }
        
        api_response = {
            'success': True,
            'stats': stats,
            'assignments': assignments,
            'unavailable_personnel': unavailable_personnel,
            'debug_info': {
                'source': 'database',
                'status_counts': summary.get('status_counts', {})
            }
        }
        
        print(f"   API Response Stats: {stats}")
        print(f"   Assignment counts:")
        for key, value in assignments.items():
            print(f"     {key}: {value['count']} personnel")
        
        print(f"\n   Full API response structure:")
        print(json.dumps(api_response, indent=2, default=str))
        
        return api_response
        
    except Exception as e:
        print(f"Error testing database: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_database()