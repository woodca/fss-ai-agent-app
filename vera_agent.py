#!/usr/bin/env python3

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from anthropic_direct import AnthropicDirect

# Load .env file only if it exists
if os.path.exists('.env'):
    load_dotenv()

# Clear any proxy settings
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

class VeraAgent:
    """Vera - Full Claude agent with function calling capabilities"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")
        
        self.client = AnthropicDirect(self.api_key)
        
        # Data files
        self.appointments_file = 'appointments.json'
        self.contacts_file = 'contacts.json'
        self.personnel_file = 'personnel.json'
        self.personnel_assignments_file = 'personnel_assignments.json'
        
        # Load data
        self.appointments = self._load_json_file(self.appointments_file, [])
        self.contacts = self._load_json_file(self.contacts_file, [])
        self.personnel = self._load_json_file(self.personnel_file, [])
        self.personnel_assignments = self._load_json_file(self.personnel_assignments_file, [])
    
    def _load_json_file(self, filename, default):
        """Load JSON file or return default if file doesn't exist"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return default
    
    def _save_json_file(self, filename, data):
        """Save data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    # FUNCTION DEFINITIONS - These are the tools Vera can use
    
    def get_personnel_roster(self):
        """Get the current personnel roster with statuses"""
        return {
            "function": "get_personnel_roster",
            "result": self.personnel_assignments,
            "summary": f"Retrieved roster of {len(self.personnel_assignments)} personnel"
        }
    
    def update_personnel_status(self, personnel_name, new_status):
        """Update a person's status (front_desk, admin_room, terminal, float, leave, on_appointment)"""
        # Find person
        person_found = None
        for person in self.personnel_assignments:
            person_name_field = person.get('name', '').lower()
            if personnel_name.lower() in person_name_field:
                person_found = person
                break
        
        if not person_found:
            return {
                "function": "update_personnel_status",
                "success": False,
                "error": f"Could not find '{personnel_name}' in roster",
                "available_personnel": [p.get('name') for p in self.personnel_assignments[:5]]
            }
        
        # Update status
        old_status = person_found.get('status')
        person_found['status'] = new_status
        person_found['last_updated'] = datetime.now().isoformat()
        
        # Save
        self._save_json_file(self.personnel_assignments_file, self.personnel_assignments)
        
        return {
            "function": "update_personnel_status",
            "success": True,
            "person_updated": person_found.get('name'),
            "old_status": old_status,
            "new_status": new_status,
            "message": f"Updated {person_found.get('name')} from {old_status} to {new_status}"
        }
    
    def add_appointment(self, personnel_name, appointment_type, appointment_date, start_time=None, end_time=None, all_day=False, notes=None):
        """Add an appointment/leave entry to the calendar"""
        # Find person
        person_found = None
        for person in self.personnel_assignments:
            person_name_field = person.get('name', '').lower()
            if personnel_name.lower() in person_name_field:
                person_found = person
                break
        
        if not person_found:
            return {
                "function": "add_appointment",
                "success": False,
                "error": f"Could not find '{personnel_name}' in roster"
            }
        
        # Create appointment
        appointment_id = f"apt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{person_found.get('id', 'unknown')}"
        
        appointment = {
            'id': appointment_id,
            'personnel_name': person_found.get('name'),
            'personnel_rank': person_found.get('rank'),
            'absence_type': appointment_type,
            'appointment_date': appointment_date,
            'start_time': start_time,
            'end_time': end_time,
            'all_day': all_day,
            'notes': notes,
            'status': 'active',
            'created_timestamp': datetime.now().isoformat(),
            'created_by': 'vera_agent'
        }
        
        self.appointments.append(appointment)
        self._save_json_file(self.appointments_file, self.appointments)
        
        return {
            "function": "add_appointment",
            "success": True,
            "appointment_created": appointment,
            "message": f"Added {appointment_type} for {person_found.get('name')} on {appointment_date}"
        }
    
    def get_appointments(self, personnel_name=None, date=None):
        """Get appointments, optionally filtered by person or date"""
        filtered_appointments = []
        
        for apt in self.appointments:
            if apt.get('status') != 'active':
                continue
            
            # Filter by person if specified
            if personnel_name and personnel_name.lower() not in apt.get('personnel_name', '').lower():
                continue
            
            # Filter by date if specified
            if date and apt.get('appointment_date') != date:
                continue
            
            filtered_appointments.append(apt)
        
        return {
            "function": "get_appointments",
            "result": filtered_appointments,
            "count": len(filtered_appointments),
            "summary": f"Found {len(filtered_appointments)} appointments"
        }
    
    def undo_last_action(self):
        """Undo the last personnel status change"""
        # This is a simplified undo - in production you'd want a proper action history
        return {
            "function": "undo_last_action",
            "success": False,
            "message": "Undo functionality not fully implemented yet. Please specify what you want to change."
        }
    
    def _check_and_execute_simple_command(self, message):
        """Use full Claude intelligence to analyze and execute commands"""
        try:
            # Create comprehensive prompt for command analysis using your GPTParser logic
            status_prompt = f"""
            You are an AI assistant for an Air Force customer service section. Analyze this text message to determine if it's a personnel status update command.

            Valid personnel statuses: front_desk, admin_room, terminal, float, leave, appointment
            Valid appointment types: medical, dental, personal_business, leave, other
            
            IMPORTANT STATUS INTERPRETATION RULES:
            - When someone is "on front desk" or "on floor" → status should be "front_desk"
            - When someone is "on terminals" or "at terminals" → status should be "terminal" 
            - When someone is "in admin room" or "to admin room" → status should be "admin_room"
            - When someone is "float" or "floating" → status should be "float"
            - When someone is "on leave" or "out" → status should be "leave"
            - When someone is "at appointment" or "has appointment" → status should be "appointment"
            
            NEW PERSONNEL ADDITION RULES:
            - Commands like "We got a new airman", "Add new person", "New member" → is_add_personnel_command: true
            - Extract rank, name, status location, and any additional details
            - Default status for new personnel should be "front_desk"
            
            PERSONNEL NAME EXTRACTION RULES:
            - Personnel names often appear at the beginning of commands: "smith will be on leave", "Brown is on terminals"
            - Look for names before verbs like "will be", "is", "goes", "moving to"
            - Names can be first names only (smith, brown) or include ranks (A1C Smith, TSgt Johnson)
            - ALWAYS extract the personnel name even for leave/appointment commands
            
            Examples:
            - "Brown is on terminals" → new_status: terminal
            - "Davis back and on front desk" → new_status: front_desk  
            - "Wilson to admin room" → new_status: admin_room
            - "Martinez is float" → new_status: float
            - "Johnson on leave" → is_appointment_command: true, personnel_name: "Johnson", appointment_type: "leave", needs_clarification: true, clarification_question: "What are the start and end dates for Johnson's leave?"
            - "smith will be on leave starting tomorrow and will return 1 aug" → is_appointment_command: true, personnel_name: "smith", appointment_type: "leave", appointment_date: "2025-08-01"
            - "We got a new airman who will be in the Terminal the name is Dufus and the Rank is A1C add them to our roster" → is_add_personnel_command: true, personnel_name: "Dufus", personnel_rank: "A1C", new_status: "terminal"
            - "smith is moving to the admin room and ali is moving to the front desk" → is_multi_personnel: true, personnel_updates: [{{"personnel_name": "smith", "new_status": "admin_room"}}, {{"personnel_name": "ali", "new_status": "front_desk"}}]
            
            Extract information if this is a command:
            1. Is this a status update command?
            2. Is this an appointment scheduling command?
            3. Is this an add new personnel command?
            4. Does this command affect multiple personnel?
            5. Personnel details (name, rank, status for each person)
            6. Appointment details (date, time, type, duration)
            7. Any additional context or notes
            
            For commands affecting multiple people (like "smith is moving to the admin room and ali is moving to the floor"), 
            extract each person's information separately in the personnel_updates array.
            
            CALENDAR ENTRY CLARIFICATION RULES:
            Ask for clarification when:
            1. APPOINTMENTS: Missing specific date ("next week", "tomorrow" without exact date) or missing start/end times
            2. LEAVE: ANY leave mention without specific start/end dates (even "simon is on leave" requires clarification)
            3. VAGUE TIMING: Commands with "later", "soon", "next week" without specific dates
            4. INCOMPLETE TIMES: Commands with only start time but no duration or end time for appointments
            
            IMPORTANT: For leave commands without dates, treat as appointment_command with needs_clarification=true
            
            Example clarification questions:
            - "I need a specific date for that appointment. What exact date did you need?"
            - "What time does that appointment start and end?"
            - "How many days will you be on leave? What are the start and end dates?"
            
            If you need clarification about the person or command, set needs_clarification to true and provide a question.
            
            Respond in JSON format:
            {{
                "is_status_command": boolean,
                "is_appointment_command": boolean,
                "is_add_personnel_command": boolean,
                "is_multi_personnel": boolean,
                "personnel_updates": [
                    {{
                        "personnel_name": "string",
                        "personnel_rank": "string or null",
                        "new_status": "string or null"
                    }}
                ],
                "appointment_type": "medical/dental/personal_business/leave/other or null",
                "appointment_date": "YYYY-MM-DD or null",
                "start_time": "HHMM or null",
                "end_time": "HHMM or null",
                "duration_hours": "number or null",
                "all_day": "boolean",
                "notes": "string or null",
                "needs_clarification": boolean,
                "clarification_question": "string or null",
                "confidence": "high/medium/low"
            }}
            
            Current date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            Message: {message}
            """
            
            # Call Claude API
            response = self.client.create_message(
                model="claude-3-5-sonnet-20241022",
                max_tokens=400,
                temperature=0.2,
                system="You are an AI assistant for military personnel management. Respond only in valid JSON format.",
                messages=[
                    {"role": "user", "content": status_prompt}
                ]
            )
            
            # Parse response
            gpt_response = response.content[0].text.strip()
            
            # Try to extract JSON from the response
            if '{' in gpt_response and '}' in gpt_response:
                start = gpt_response.find('{')
                end = gpt_response.rfind('}') + 1
                json_text = gpt_response[start:end]
                parsed_command = json.loads(json_text)
                
                # Handle clarification requests
                if parsed_command.get('needs_clarification', False):
                    clarification_question = parsed_command.get('clarification_question')
                    return f"{clarification_question}"
                
                # Handle status commands
                if parsed_command.get('is_status_command', False):
                    return self._execute_status_command(parsed_command)
                
                # Handle appointment commands  
                if parsed_command.get('is_appointment_command', False):
                    # Extract personnel name from personnel_updates if not directly available
                    personnel_name = parsed_command.get('personnel_name')
                    if not personnel_name and parsed_command.get('personnel_updates'):
                        personnel_updates = parsed_command.get('personnel_updates', [])
                        if personnel_updates:
                            personnel_name = personnel_updates[0].get('personnel_name')
                            parsed_command['personnel_name'] = personnel_name
                    
                    return self._execute_appointment_command_simple(parsed_command)
                
                # Handle add personnel commands
                if parsed_command.get('is_add_personnel_command', False):
                    return self._execute_add_personnel_command_simple(parsed_command)
            
            # Not a recognized command
            return None
            
        except Exception as e:
            print(f"Error in command analysis: {e}")
            return None
    
    def _execute_status_command(self, parsed_command):
        """Execute status update commands"""
        personnel_updates = parsed_command.get('personnel_updates', [])
        
        if not personnel_updates:
            # Single person command - convert to new format
            if parsed_command.get('personnel_name'):
                personnel_updates = [{
                    'personnel_name': parsed_command.get('personnel_name'),
                    'personnel_rank': parsed_command.get('personnel_rank'),
                    'new_status': parsed_command.get('new_status')
                }]
        
        successful_updates = []
        failed_updates = []
        
        for update in personnel_updates:
            personnel_name = update.get('personnel_name')
            new_status = update.get('new_status')
            
            if personnel_name and new_status:
                result = self.update_personnel_status(personnel_name, new_status)
                
                if result['success']:
                    successful_updates.append(f"Updated {result['person_updated']} to {new_status}")
                else:
                    available = result.get('available_personnel', [])
                    if available:
                        failed_updates.append(f"Couldn't find '{personnel_name}' - did you mean: {', '.join(available[:3])}?")
                    else:
                        failed_updates.append(f"Couldn't find '{personnel_name}' in roster")
        
        if successful_updates and not failed_updates:
            return "; ".join(successful_updates) + "."
        elif successful_updates and failed_updates:
            return "; ".join(successful_updates) + ". " + " ".join(failed_updates)
        elif failed_updates:
            return " ".join(failed_updates)
        else:
            return "I couldn't process that status update."
    
    def _execute_appointment_command_simple(self, parsed_command):
        """Execute appointment commands"""
        personnel_name = parsed_command.get('personnel_name')
        appointment_type = parsed_command.get('appointment_type', 'other')
        appointment_date = parsed_command.get('appointment_date')
        start_time = parsed_command.get('start_time')
        end_time = parsed_command.get('end_time')
        all_day = parsed_command.get('all_day', False)
        notes = parsed_command.get('notes')
        
        if not personnel_name:
            return "I need to know who the appointment is for."
        
        # For leave appointments, also update their status
        if appointment_type == 'leave':
            # Update status to leave
            status_result = self.update_personnel_status(personnel_name, 'leave')
            
            if appointment_date:
                # Also create appointment entry
                result = self.add_appointment(
                    personnel_name=personnel_name,
                    appointment_type=appointment_type,
                    appointment_date=appointment_date,
                    start_time=start_time,
                    end_time=end_time,
                    all_day=all_day,
                    notes=notes
                )
                
                if status_result['success']:
                    person_name = status_result['person_updated']
                    if result['success']:
                        return f"Updated {person_name} to leave status and added leave appointment."
                    else:
                        return f"Updated {person_name} to leave status."
                else:
                    available = status_result.get('available_personnel', [])
                    if available:
                        return f"I couldn't find '{personnel_name}' in our roster. Did you mean one of these: {', '.join(available[:3])}?"
                    else:
                        return f"I couldn't find '{personnel_name}' in our roster."
            else:
                # No date provided, just update status
                if status_result['success']:
                    return f"Updated {status_result['person_updated']} to leave status."
                else:
                    available = status_result.get('available_personnel', [])
                    if available:
                        return f"I couldn't find '{personnel_name}' in our roster. Did you mean one of these: {', '.join(available[:3])}?"
                    else:
                        return f"I couldn't find '{personnel_name}' in our roster."
        else:
            # Regular appointment
            if not appointment_date:
                return "I need to know what date the appointment is for."
            
            result = self.add_appointment(
                personnel_name=personnel_name,
                appointment_type=appointment_type,
                appointment_date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                all_day=all_day,
                notes=notes
            )
            
            if result['success']:
                return result['message']
            else:
                return f"Couldn't create appointment: {result.get('error', 'Unknown error')}"
    
    def _execute_add_personnel_command_simple(self, parsed_command):
        """Execute add personnel commands"""
        personnel_name = parsed_command.get('personnel_name')
        personnel_rank = parsed_command.get('personnel_rank')
        new_status = parsed_command.get('new_status', 'front_desk')
        
        if not personnel_name:
            return "I need the person's name to add them to the roster."
        
        if not personnel_rank:
            return "I need the person's rank to add them to the roster."
        
        # Check if person already exists
        for person in self.personnel_assignments:
            if person.get('name', '').lower() == f"{personnel_rank} {personnel_name}".lower():
                return f"{personnel_rank} {personnel_name} is already in our roster."
        
        # Generate new ID
        existing_ids = [p.get('id', '') for p in self.personnel_assignments]
        id_numbers = []
        for existing_id in existing_ids:
            if existing_id.startswith('pers_'):
                try:
                    id_numbers.append(int(existing_id.split('_')[1]))
                except (IndexError, ValueError):
                    continue
        
        next_id_number = max(id_numbers) + 1 if id_numbers else 1
        new_id = f"pers_{next_id_number:03d}"
        
        # Create new personnel entry
        new_person = {
            'id': new_id,
            'name': f"{personnel_rank} {personnel_name}",
            'rank': personnel_rank,
            'type': 'military',
            'position': 'Airman',
            'status': new_status,
            'phone': f"(555) 123-{4500 + next_id_number}",
            'email': f"{personnel_name.lower()}.{personnel_rank.lower()}@us.af.mil",
            'last_updated': datetime.now().isoformat()
        }
        
        # Add to personnel list
        self.personnel_assignments.append(new_person)
        self._save_json_file(self.personnel_assignments_file, self.personnel_assignments)
        
        return f"Successfully added {personnel_rank} {personnel_name} to the roster with status {new_status}."
    
    def chat(self, message, conversation_history=None):
        """Main chat function with full Claude intelligence and function calling"""
        
        if conversation_history is None:
            conversation_history = []
        
        # First check if this is a simple status command that should be executed immediately
        status_result = self._check_and_execute_simple_command(message)
        if status_result:
            return status_result
        
        # Create system prompt with function definitions
        system_prompt = """You are Vera, an AI assistant for an Air Force customer service section. You have full conversational intelligence and access to personnel management functions.

You are having a natural conversation. When you need to use functions, just say what you want to do and I'll handle the function calls.

CONVERSATION STYLE:
- Be natural and conversational like a real person
- When someone says just a name like "simon", ask what they want to know or do about Simon
- When someone says "no", acknowledge they're correcting you and ask how to help
- ALWAYS remember and reference the conversation context and history
- Be helpful and understand natural language
- If someone refers to previous information (like "he" or "patel" from earlier), use that context

EXAMPLES:
User: "simon"
You: "What would you like to know or do regarding Simon?"

User: "no" (after you did something wrong)
You: "I understand you want to correct that. What should I do instead?"

User: "simon is on leave"
You: "I can help set Simon on leave status. What are the start and end dates for his leave?"

You have access to personnel management functions but focus on natural conversation first."""

        # Build conversation context
        messages = []
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Last 10 messages
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })
        
        try:
            # First, let Claude respond naturally
            response = self.client.create_message(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.7,
                system=system_prompt,
                messages=messages
            )
            
            response_text = response.content[0].text.strip()
            
            # Check if we need to automatically perform actions based on context
            function_executed = False
            
            # Simple pattern matching for common actions
            # Look at conversation history to understand context
            recent_context = " ".join([msg.get("content", "") for msg in conversation_history[-4:]])
            current_conversation = recent_context + " " + message
            
            # Auto-execute functions based on natural conversation flow
            if any(word in message.lower() for word in ["roster", "who is", "personnel", "everyone"]):
                roster = self.get_personnel_roster()
                # Give Claude the roster data for a natural response
                enhanced_prompt = f"""Based on this personnel roster data:
{json.dumps(roster['result'], indent=2)}

Previous conversation: {recent_context}
User just said: {message}

Respond naturally about the personnel status."""
                
                enhanced_response = self.client.create_message(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=400,
                    temperature=0.7,
                    system="You are Vera. Respond naturally based on the personnel data provided.",
                    messages=[{"role": "user", "content": enhanced_prompt}]
                )
                
                return enhanced_response.content[0].text.strip()
            
            return response_text
            
        except Exception as e:
            return f"I'm having trouble processing that. Error: {str(e)}"

# Simple function calling - this could be enhanced with Claude's native function calling
def extract_function_call(text):
    """Extract function calls from Claude's response (simplified)"""
    # This would be replaced with proper function calling in production
    pass

if __name__ == "__main__":
    # Test the agent
    vera = VeraAgent()
    print("Vera Agent initialized!")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        response = vera.chat(user_input)
        print(f"Vera: {response}")