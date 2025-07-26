import anthropic
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load .env file only if it exists (for local development)
if os.path.exists('.env'):
    load_dotenv()

class GPTParser:
    def __init__(self, api_key=None):
        # Try to get API key from multiple sources
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        
        # Debug logging for production
        print(f"API Key loaded: {'Yes' if self.api_key else 'No'}")
        print(f"API Key length: {len(self.api_key) if self.api_key else 0}")
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize Anthropic client without any extra parameters
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except TypeError:
            # Fallback for older versions
            self.client = anthropic.Client(api_key=self.api_key)
        self.appointments_file = 'appointments.json'
        self.contacts_file = 'contacts.json'
        self.personnel_file = 'personnel.json'
        self.personnel_assignments_file = 'personnel_assignments.json'
        
        # Load existing data
        self.appointments = self._load_json_file(self.appointments_file, [])
        self.contacts = self._load_json_file(self.contacts_file, [])
        self.personnel = self._load_json_file(self.personnel_file, [])
        self.personnel_assignments = self._load_json_file(self.personnel_assignments_file, [])
        
        # Load GPT prompt template
        self.prompt_template = self._load_prompt_template()
    
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
    
    def _load_prompt_template(self):
        """Load GPT prompt template from file"""
        try:
            with open('templates/gpt_prompt.txt', 'r') as f:
                return f.read()
        except FileNotFoundError:
            # Default prompt if template file doesn't exist
            return """
            You are an AI assistant for an Air Force customer service section. 
            Analyze the following text message and extract relevant information for appointment scheduling or customer service inquiries.
            
            Extract the following information if available:
            1. Appointment request (yes/no)
            2. Preferred date/time
            3. Service type requested
            4. Urgency level (low/medium/high)
            5. Contact information
            6. Any specific requirements or notes
            
            Respond in JSON format with these fields:
            {
                "is_appointment_request": boolean,
                "service_type": "string or null",
                "preferred_datetime": "string or null",
                "urgency": "low/medium/high",
                "contact_info": "string or null",
                "notes": "string or null",
                "requires_followup": boolean,
                "category": "appointment/inquiry/complaint/other"
            }
            
            Text message to analyze:
            """
    
    def process_message(self, message_data):
        """Process a message using GPT and extract relevant information"""
        try:
            message_text = message_data.get('message_text', '')
            phone_number = message_data.get('phone_number', '')
            
            # Get current date for context
            current_date = datetime.now().strftime('%A, %B %d, %Y')
            current_date_iso = datetime.now().strftime('%Y-%m-%d')
            
            # Create the full prompt with date context
            full_prompt = self.prompt_template + f"\n\nCURRENT DATE: {current_date} ({current_date_iso})\nPhone: {phone_number}\nMessage: {message_text}"
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                temperature=0.3,
                system="You are an AI assistant for military customer service. Respond only in valid JSON format.",
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            # Parse Claude response
            gpt_response = response.content[0].text.strip()
            parsed_data = json.loads(gpt_response)
            
            # Add metadata
            processed_message = {
                'original_message': message_data,
                'processed_timestamp': datetime.now().isoformat(),
                'gpt_analysis': parsed_data,
                'status': 'processed'
            }
            
            # Handle the processed message based on type
            if parsed_data.get('is_absence_report', False):
                self._handle_absence_report(processed_message)
            
            # Check if this might be a status command first
            status_result = self.process_status_command(message_data, phone_number)
            if status_result.get('success', False) or status_result.get('needs_clarification', False):
                # This was a status command, add the result to the processed message
                processed_message['status_command_result'] = status_result
            
            # Update contact information
            self._update_contact_info(phone_number, message_data, parsed_data)
            
            return processed_message
            
        except json.JSONDecodeError as e:
            print(f"Error parsing Claude response as JSON: {e}")
            return self._create_error_response(message_data, "Claude response parsing error")
        
        except Exception as e:
            print(f"Error processing message: {e}")
            return self._create_error_response(message_data, str(e))
    
    def _handle_absence_report(self, processed_message):
        """Handle absence reports by adding to appointments list"""
        gpt_analysis = processed_message['gpt_analysis']
        original_message = processed_message['original_message']
        phone_number = original_message.get('phone_number', '')
        
        # Get personnel info if available
        personnel_info = self.get_personnel_by_phone(phone_number)
        
        appointment = {
            'id': f"abs_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{original_message.get('id', '')}",
            'phone_number': phone_number,
            'personnel_name': personnel_info.get('full_name') if personnel_info else 'Unknown',
            'personnel_rank': personnel_info.get('rank') if personnel_info else None,
            'absence_type': gpt_analysis.get('absence_type'),
            'appointment_date': gpt_analysis.get('appointment_date'),
            'start_time': gpt_analysis.get('start_time'),
            'end_time': gpt_analysis.get('end_time'),
            'duration_hours': gpt_analysis.get('duration_hours'),
            'all_day': gpt_analysis.get('all_day', False),
            'original_text': gpt_analysis.get('original_text'),
            'notes': gpt_analysis.get('notes'),
            'affects_manning': gpt_analysis.get('affects_current_manning', False),
            'status': 'active',
            'created_timestamp': processed_message['processed_timestamp'],
            'original_message_id': original_message.get('id')
        }
        
        self.appointments.append(appointment)
        self._save_json_file(self.appointments_file, self.appointments)
        
        name_display = personnel_info.get('full_name') if personnel_info else phone_number
        print(f"New absence report added for {name_display}: {appointment['id']}")
    
    def _update_contact_info(self, phone_number, message_data, parsed_data):
        """Update contact information"""
        # Find existing contact or create new one
        existing_contact = None
        for contact in self.contacts:
            if contact.get('phone_number') == phone_number:
                existing_contact = contact
                break
        
        if existing_contact:
            # Update last contact and message history
            existing_contact['last_contact'] = datetime.now().isoformat()
            existing_contact['message_count'] = existing_contact.get('message_count', 0) + 1
            if 'message_history' not in existing_contact:
                existing_contact['message_history'] = []
            existing_contact['message_history'].append({
                'timestamp': datetime.now().isoformat(),
                'message': message_data.get('message_text', ''),
                'category': parsed_data.get('category', 'other')
            })
        else:
            # Create new contact
            new_contact = {
                'phone_number': phone_number,
                'first_contact': datetime.now().isoformat(),
                'last_contact': datetime.now().isoformat(),
                'message_count': 1,
                'message_history': [{
                    'timestamp': datetime.now().isoformat(),
                    'message': message_data.get('message_text', ''),
                    'category': parsed_data.get('category', 'other')
                }]
            }
            self.contacts.append(new_contact)
        
        self._save_json_file(self.contacts_file, self.contacts)
    
    def _create_error_response(self, message_data, error_message):
        """Create error response for failed processing"""
        return {
            'original_message': message_data,
            'processed_timestamp': datetime.now().isoformat(),
            'status': 'error',
            'error': error_message,
            'gpt_analysis': None
        }
    
    def get_pending_appointments(self):
        """Get all active appointments/absences"""
        return [apt for apt in self.appointments if apt.get('status') == 'active']
    
    def get_contact_by_phone(self, phone_number):
        """Get contact information by phone number"""
        for contact in self.contacts:
            if contact.get('phone_number') == phone_number:
                return contact
        return None
    
    def get_personnel_by_phone(self, phone_number):
        """Get personnel information by phone number"""
        for person in self.personnel:
            if person.get('phone_number') == phone_number:
                return person
        return None
    
    def update_appointment_status(self, appointment_id, new_status, notes=None):
        """Update appointment status"""
        for apt in self.appointments:
            if apt.get('id') == appointment_id:
                apt['status'] = new_status
                apt['last_updated'] = datetime.now().isoformat()
                if notes:
                    apt['admin_notes'] = notes
                self._save_json_file(self.appointments_file, self.appointments)
                return True
        return False
    
    def get_manning_status(self, total_personnel=None):
        """Calculate current manning status"""
        from datetime import date, time as dt_time
        
        active_absences = self.get_pending_appointments()
        today = date.today()
        current_time = datetime.now().time()
        
        # Count people currently out
        currently_out = 0
        out_details = []
        
        for absence in active_absences:
            # Check if absence affects current manning
            if not absence.get('affects_manning', True):
                continue
                
            # Parse appointment date
            apt_date_str = absence.get('appointment_date')
            if apt_date_str:
                try:
                    apt_date = datetime.fromisoformat(apt_date_str).date()
                    if apt_date != today:
                        continue  # Not today
                except:
                    continue
            
            # Check if currently out based on time
            if absence.get('all_day', False):
                currently_out += 1
                out_details.append({
                    'phone': absence.get('phone_number', 'Unknown'),
                    'type': absence.get('absence_type', 'unknown'),
                    'time': 'All Day',
                    'id': absence.get('id')
                })
            else:
                start_time = absence.get('start_time')
                end_time = absence.get('end_time')
                
                if start_time:
                    try:
                        # Convert military time to time object
                        start_hour = int(start_time[:2])
                        start_min = int(start_time[2:]) if len(start_time) > 2 else 0
                        start_dt = dt_time(start_hour, start_min)
                        
                        # Check if currently in appointment window
                        if current_time >= start_dt:
                            if end_time:
                                end_hour = int(end_time[:2])
                                end_min = int(end_time[2:]) if len(end_time) > 2 else 0
                                end_dt = dt_time(end_hour, end_min)
                                if current_time <= end_dt:
                                    currently_out += 1
                                    out_details.append({
                                        'phone': absence.get('phone_number', 'Unknown'),
                                        'type': absence.get('absence_type', 'unknown'),
                                        'time': f"{start_time}-{end_time}",
                                        'id': absence.get('id')
                                    })
                            else:
                                # No end time specified, assume out for rest of day
                                currently_out += 1
                                out_details.append({
                                    'phone': absence.get('phone_number', 'Unknown'),
                                    'type': absence.get('absence_type', 'unknown'),
                                    'time': f"{start_time}+",
                                    'id': absence.get('id')
                                })
                    except:
                        continue
        
        # Calculate availability
        if total_personnel:
            available = total_personnel - currently_out
            availability_pct = (available / total_personnel) * 100
        else:
            available = None
            availability_pct = None
        
        return {
            'total_personnel': total_personnel,
            'currently_out': currently_out,
            'available': available,
            'availability_percentage': availability_pct,
            'out_details': out_details,
            'timestamp': datetime.now().isoformat()
        }
    
    def process_status_command(self, message_data, sender_phone):
        """Process status update commands like 'Airman Patel moved to terminal'"""
        try:
            message_text = message_data.get('message_text', '').strip()
            
            # Create prompt for status command analysis
            status_prompt = f"""
            You are an AI assistant for an Air Force customer service section. Analyze this text message to determine if it's a personnel status update command.

            Valid personnel assignments: terminal, admin_room, floor, section_leads
            Valid personnel statuses: available, working, on_appointment, on_leave
            Valid appointment types: medical, dental, personal_business, leave, other
            
            IMPORTANT STATUS INTERPRETATION RULES:
            - When someone is "on [location]" or "at [location]" or "working [location]" → status should be "working"
            - When someone is "back" and assigned to a location → status should be "working"
            - When someone is "moved to [location]" or "assigned to [location]" → status should be "working"
            - When someone is explicitly "available" → status should be "available"
            - When someone is "on leave" or "out" → status should be "on_leave"
            - When someone is "at appointment" or "has appointment" → status should be "on_appointment"
            
            NEW PERSONNEL ADDITION RULES:
            - Commands like "We got a new airman", "Add new person", "New member" → is_add_personnel_command: true
            - Extract rank, name, assignment location, and any additional details
            - Default status for new personnel should be "working" if assigned to a location
            
            PERSONNEL NAME EXTRACTION RULES:
            - Personnel names often appear at the beginning of commands: "smith will be on leave", "Brown is on terminals"
            - Look for names before verbs like "will be", "is", "goes", "moving to"
            - Names can be first names only (smith, brown) or include ranks (A1C Smith, TSgt Johnson)
            - ALWAYS extract the personnel name even for leave/appointment commands
            
            Examples:
            - "Brown is on terminals" → assignment: terminal, status: working
            - "Davis back and on floor" → assignment: floor, status: working  
            - "Wilson to admin room" → assignment: admin_room, status: working
            - "Martinez is available" → status: available (no assignment change)
            - "Johnson on leave" → personnel_name: "Johnson", status: on_leave (no assignment change)
            - "smith will be on leave starting tomorrow and will return 1 aug" → is_appointment_command: true, personnel_name: "smith", appointment_type: "leave", appointment_date: "2025-08-01"
            - "We got a new airman who will be in the Terminal the name is Dufus and the Rank is A1C add them to our roster" → is_add_personnel_command: true, personnel_name: "Dufus", personnel_rank: "A1C", new_assignment: "terminal"
            - "smith is moving to the admin room and ali is moving to the floor" → is_multi_personnel: true, personnel_updates: [{{"personnel_name": "smith", "new_assignment": "admin_room", "new_status": "working"}}, {{"personnel_name": "ali", "new_assignment": "floor", "new_status": "working"}}]
            
            Extract information if this is a command:
            1. Is this a status/assignment update command?
            2. Is this an appointment scheduling command?
            3. Is this an add new personnel command?
            4. Does this command affect multiple personnel?
            5. Personnel details (name, rank, assignment, status for each person)
            6. Appointment details (date, time, type, duration)
            7. Any additional context or notes
            
            For commands affecting multiple people (like "smith is moving to the admin room and ali is moving to the floor"), 
            extract each person's information separately in the personnel_updates array.
            
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
                        "new_assignment": "string or null",
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
            Message: {message_text}
            """
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=400,
                temperature=0.2,
                system="You are an AI assistant for military personnel management. Respond only in valid JSON format.",
                messages=[
                    {"role": "user", "content": status_prompt}
                ]
            )
            
            # Parse response
            gpt_response = response.content[0].text.strip()
            print(f"Claude status command response: {gpt_response}")
            
            # Try to extract JSON from the response
            try:
                if '{' in gpt_response and '}' in gpt_response:
                    start = gpt_response.find('{')
                    end = gpt_response.rfind('}') + 1
                    json_text = gpt_response[start:end]
                    parsed_command = json.loads(json_text)
                    print(f"Parsed status command: {parsed_command}")
                else:
                    print("No JSON found in Claude response")
                    # No JSON found, assume not a status command
                    return {
                        'success': False,
                        'message': 'Not recognized as a status command',
                        'requires_response': False
                    }
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                # JSON parsing failed
                return {
                    'success': False,
                    'message': 'Could not understand the command format',
                    'requires_response': True,
                    'response_message': 'I had trouble understanding that command. Please try rephrasing it.'
                }
            
            if parsed_command.get('needs_clarification', False):
                # Send clarification question back
                return self._send_clarification_question(sender_phone, parsed_command.get('clarification_question'))
            elif parsed_command.get('is_multi_personnel', False):
                # Process multiple personnel updates
                return self._execute_multi_personnel_command(parsed_command, sender_phone, message_text)
            elif parsed_command.get('is_status_command', False) and parsed_command.get('is_appointment_command', False):
                # Convert combined command to new format if needed
                if not parsed_command.get('personnel_updates') and parsed_command.get('personnel_name'):
                    # Convert old format to new format for combined commands
                    personnel_update = {
                        'personnel_name': parsed_command.get('personnel_name'),
                        'personnel_rank': parsed_command.get('personnel_rank'),
                        'new_assignment': parsed_command.get('new_assignment'),
                        'new_status': parsed_command.get('new_status')
                    }
                    parsed_command['personnel_updates'] = [personnel_update]
                
                # Process both status update and appointment creation
                return self._execute_combined_command(parsed_command, sender_phone, message_text)
            elif parsed_command.get('is_status_command', False):
                # Convert single personnel command to multi-personnel format for consistency
                if not parsed_command.get('personnel_updates'):
                    # Convert old format to new format
                    personnel_update = {
                        'personnel_name': parsed_command.get('personnel_name'),
                        'personnel_rank': parsed_command.get('personnel_rank'),
                        'new_assignment': parsed_command.get('new_assignment'),
                        'new_status': parsed_command.get('new_status')
                    }
                    parsed_command['personnel_updates'] = [personnel_update]
                    parsed_command['is_multi_personnel'] = True
                
                # Process as multi-personnel command
                return self._execute_multi_personnel_command(parsed_command, sender_phone, message_text)
            elif parsed_command.get('is_appointment_command', False):
                # Process the appointment command only
                return self._execute_appointment_command(parsed_command, sender_phone, message_text)
            elif parsed_command.get('is_add_personnel_command', False):
                # Process the add new personnel command
                return self._execute_add_personnel_command(parsed_command, sender_phone, message_text)
            else:
                return {
                    'success': False,
                    'message': 'Not recognized as a status, appointment, or personnel addition command',
                    'requires_response': False
                }
                
        except Exception as e:
            print(f"Error processing status command: {e}")
            return {
                'success': False,
                'error': str(e),
                'requires_response': True,
                'response_message': f"Sorry, I had trouble processing that command. Please try again or be more specific."
            }
    
    def _execute_combined_command(self, parsed_command, sender_phone, original_message):
        """Execute both status update and appointment creation for commands like leave requests"""
        try:
            # First execute the status update using multi-personnel command
            status_result = self._execute_multi_personnel_command(parsed_command, sender_phone, original_message)
            
            if not status_result.get('success'):
                # If status update failed, don't try appointment creation
                return status_result
            
            # Then execute the appointment creation
            appointment_result = self._execute_appointment_command(parsed_command, sender_phone, original_message)
            
            if not appointment_result.get('success'):
                # If appointment creation failed, return status result with note
                status_result['appointment_error'] = appointment_result.get('error', 'Failed to create appointment')
                status_result['response_message'] += " Note: Could not create calendar appointment."
                return status_result
            
            # Both succeeded - combine the results
            combined_response = status_result.get('response_message', '') + " " + appointment_result.get('response_message', '')
            
            return {
                'success': True,
                'person_updated': status_result.get('person_updated'),
                'appointment_created': appointment_result.get('appointment_created'),
                'updates_made': status_result.get('updates_made', []),
                'requires_response': True,
                'response_message': combined_response.strip()
            }
            
        except Exception as e:
            print(f"Error executing combined command: {e}")
            return {
                'success': False,
                'error': str(e),
                'requires_response': True,
                'response_message': "Sorry, I couldn't complete that command. Please try again."
            }
    
    def _execute_status_update(self, parsed_command, sender_phone, original_message):
        """Execute the parsed status update command"""
        try:
            personnel_name = parsed_command.get('personnel_name')
            new_assignment = parsed_command.get('new_assignment')
            new_status = parsed_command.get('new_status')
            
            # Find the person in personnel assignments with improved matching
            person_found = None
            potential_matches = []
            
            if personnel_name:
                # Extract just the last name if it's provided
                name_parts = personnel_name.strip().split()
                search_name = name_parts[-1].lower()  # Get the last word as surname
                
                # Find all people with matching last names
                for person in self.personnel_assignments:
                    person_name_field = person.get('name', '')
                    person_name_parts = person_name_field.split()
                    
                    if len(person_name_parts) >= 2:
                        person_last_name = person_name_parts[-1].lower()  # Get last name
                        
                        # Check for exact last name match
                        if search_name == person_last_name:
                            potential_matches.append(person)
                        # Also check if the full search term matches any part of the name
                        elif personnel_name.lower() in person_name_field.lower():
                            potential_matches.append(person)
                
                # Determine the best match
                if len(potential_matches) == 1:
                    # Unique match found
                    person_found = potential_matches[0]
                elif len(potential_matches) > 1:
                    # Multiple matches - check if one is an exact full name match
                    exact_matches = [p for p in potential_matches if personnel_name.lower() in p.get('name', '').lower()]
                    if len(exact_matches) == 1:
                        person_found = exact_matches[0]
                    else:
                        # Multiple people with same last name - ask for clarification
                        match_names = [p.get('name', 'Unknown') for p in potential_matches]
                        question = f"I found multiple people with the name '{personnel_name}'. Which one do you mean?\n" + "\n".join(match_names)
                        return self._send_clarification_question(sender_phone, question)
                        
            print(f"Looking for: '{personnel_name}', Found: {person_found.get('name') if person_found else 'None'}")
            
            if not person_found:
                # Ask for clarification about which person
                available_personnel = [p.get('name', 'Unknown') for p in self.personnel_assignments]
                question = f"I couldn't find '{personnel_name}' in our roster. Did you mean one of these people?\n" + "\n".join(available_personnel[:5])
                
                return self._send_clarification_question(sender_phone, question)
            
            # Update the person's status/assignment
            updates_made = []
            if new_assignment:
                person_found['assignment'] = new_assignment
                updates_made.append(f"assignment to {new_assignment}")
                
                # If assigning to a work location, automatically set status to 'working'
                # unless a specific status was provided
                if not new_status and new_assignment in ['terminal', 'admin_room', 'floor']:
                    person_found['status'] = 'working'
                    updates_made.append(f"status to working")
            
            if new_status:
                person_found['status'] = new_status
                updates_made.append(f"status to {new_status}")
            
            person_found['last_updated'] = datetime.now().isoformat()
            
            # Save updated data
            self._save_json_file(self.personnel_assignments_file, self.personnel_assignments)
            
            # Create confirmation message
            person_display = person_found.get('name', 'Unknown person')
            updates_text = " and ".join(updates_made)
            confirmation_message = f"Updated {person_display}'s {updates_text} successfully."
            
            # Log the update
            print(f"Status update from {sender_phone}: {person_display} - {updates_text}")
            
            return {
                'success': True,
                'person_updated': person_found,
                'updates_made': updates_made,
                'requires_response': True,
                'response_message': confirmation_message
            }
            
        except Exception as e:
            print(f"Error executing status update: {e}")
            return {
                'success': False,
                'error': str(e),
                'requires_response': True,
                'response_message': "Sorry, I couldn't complete that update. Please try again."
            }
    
    def _execute_add_personnel_command(self, parsed_command, sender_phone, original_message):
        """Execute command to add new personnel to the roster"""
        try:
            personnel_name = parsed_command.get('personnel_name')
            personnel_rank = parsed_command.get('personnel_rank')
            new_assignment = parsed_command.get('new_assignment')
            new_status = parsed_command.get('new_status', 'working')  # Default to working
            
            # Validate required fields
            if not personnel_name:
                return {
                    'success': False,
                    'error': 'Personnel name is required',
                    'requires_response': True,
                    'response_message': 'I need the person\'s name to add them to the roster. Please provide their name.'
                }
            
            if not personnel_rank:
                return {
                    'success': False,
                    'error': 'Personnel rank is required', 
                    'requires_response': True,
                    'response_message': 'I need the person\'s rank to add them to the roster. Please provide their rank.'
                }
            
            if not new_assignment:
                return {
                    'success': False,
                    'error': 'Assignment is required',
                    'requires_response': True,
                    'response_message': 'I need to know where to assign them (terminal, admin_room, floor, or section_leads).'
                }
            
            # Check if person already exists
            existing_person = None
            for person in self.personnel_assignments:
                if person.get('name', '').lower() == f"{personnel_rank} {personnel_name}".lower():
                    existing_person = person
                    break
            
            if existing_person:
                return {
                    'success': False,
                    'error': 'Person already exists',
                    'requires_response': True,
                    'response_message': f'{personnel_rank} {personnel_name} is already in our roster. Did you mean to update their assignment instead?'
                }
            
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
                'type': 'military',  # Default to military for now
                'position': 'Airman',  # Default position
                'assignment': new_assignment,
                'phone': f"(555) 123-{4500 + next_id_number}",  # Generate placeholder phone
                'email': f"{personnel_name.lower()}.{personnel_rank.lower()}@us.af.mil",
                'status': new_status,
                'last_updated': datetime.now().isoformat()
            }
            
            # Add to personnel list
            self.personnel_assignments.append(new_person)
            
            # Save updated data
            self._save_json_file(self.personnel_assignments_file, self.personnel_assignments)
            
            # Create confirmation message
            confirmation_message = f"Successfully added {personnel_rank} {personnel_name} to the roster with assignment to {new_assignment} and status {new_status}."
            
            # Log the addition
            print(f"New personnel added by {sender_phone}: {personnel_rank} {personnel_name} - {new_assignment}")
            
            return {
                'success': True,
                'person_updated': new_person,
                'updates_made': [f"added to roster with assignment {new_assignment}"],
                'requires_response': True,
                'response_message': confirmation_message
            }
            
        except Exception as e:
            print(f"Error executing add personnel command: {e}")
            return {
                'success': False,
                'error': str(e),
                'requires_response': True,
                'response_message': "Sorry, I couldn't add the new person to the roster. Please try again."
            }
    
    def _execute_multi_personnel_command(self, parsed_command, sender_phone, original_message):
        """Execute command affecting multiple personnel"""
        try:
            personnel_updates = parsed_command.get('personnel_updates', [])
            
            if not personnel_updates:
                return {
                    'success': False,
                    'error': 'No personnel updates found',
                    'requires_response': True,
                    'response_message': 'I couldn\'t find any personnel to update in that command.'
                }
            
            successful_updates = []
            failed_updates = []
            all_updated_personnel = []
            
            # Process each personnel update
            for update in personnel_updates:
                personnel_name = update.get('personnel_name')
                new_assignment = update.get('new_assignment')
                new_status = update.get('new_status', 'working')  # Default to working
                
                if not personnel_name:
                    failed_updates.append("Missing personnel name")
                    continue
                
                # Find the person using the existing logic from _execute_status_update
                person_found = None
                potential_matches = []
                
                # Extract just the last name if it's provided
                name_parts = personnel_name.strip().split()
                search_name = name_parts[-1].lower()  # Get the last word as surname
                
                # Find all people with matching last names
                for person in self.personnel_assignments:
                    person_name_field = person.get('name', '')
                    person_name_parts = person_name_field.split()
                    
                    if len(person_name_parts) >= 2:
                        person_last_name = person_name_parts[-1].lower()  # Get last name
                        
                        # Check for exact last name match
                        if search_name == person_last_name:
                            potential_matches.append(person)
                        # Also check if the full search term matches any part of the name
                        elif personnel_name.lower() in person_name_field.lower():
                            potential_matches.append(person)
                
                # Determine the best match
                if len(potential_matches) == 1:
                    person_found = potential_matches[0]
                elif len(potential_matches) > 1:
                    # Multiple matches - check if one is an exact full name match
                    exact_matches = [p for p in potential_matches if personnel_name.lower() in p.get('name', '').lower()]
                    if len(exact_matches) == 1:
                        person_found = exact_matches[0]
                
                if not person_found:
                    failed_updates.append(f"Could not find '{personnel_name}' in roster")
                    continue
                
                # Update the person's status/assignment
                updates_made = []
                if new_assignment:
                    person_found['assignment'] = new_assignment
                    updates_made.append(f"assignment to {new_assignment}")
                    
                    # If assigning to a work location, automatically set status to 'working'
                    # unless a specific status was provided
                    if new_assignment in ['terminal', 'admin_room', 'floor'] and not update.get('new_status'):
                        person_found['status'] = 'working'
                        updates_made.append(f"status to working")
                
                if new_status:
                    person_found['status'] = new_status
                    updates_made.append(f"status to {new_status}")
                
                person_found['last_updated'] = datetime.now().isoformat()
                
                successful_updates.append({
                    'person': person_found.get('name'),
                    'updates': updates_made
                })
                all_updated_personnel.append(person_found)
            
            # Save updated data if any updates were successful
            if successful_updates:
                self._save_json_file(self.personnel_assignments_file, self.personnel_assignments)
            
            # Create response message
            if successful_updates and not failed_updates:
                # All updates successful
                update_descriptions = []
                for update in successful_updates:
                    updates_text = " and ".join(update['updates'])
                    update_descriptions.append(f"{update['person']}'s {updates_text}")
                
                confirmation_message = f"Successfully updated: {'; '.join(update_descriptions)}."
                
                return {
                    'success': True,
                    'people_updated': all_updated_personnel,
                    'updates_made': successful_updates,
                    'requires_response': True,
                    'response_message': confirmation_message
                }
            elif successful_updates and failed_updates:
                # Partial success
                update_descriptions = []
                for update in successful_updates:
                    updates_text = " and ".join(update['updates'])
                    update_descriptions.append(f"{update['person']}'s {updates_text}")
                
                success_part = f"Successfully updated: {'; '.join(update_descriptions)}."
                failed_part = f"Failed to update: {'; '.join(failed_updates)}."
                
                return {
                    'success': True,
                    'people_updated': all_updated_personnel,
                    'updates_made': successful_updates,
                    'partial_failure': True,
                    'failed_updates': failed_updates,
                    'requires_response': True,
                    'response_message': f"{success_part} {failed_part}"
                }
            else:
                # All updates failed
                return {
                    'success': False,
                    'error': 'All updates failed',
                    'failed_updates': failed_updates,
                    'requires_response': True,
                    'response_message': f"Failed to update personnel: {'; '.join(failed_updates)}."
                }
                
        except Exception as e:
            print(f"Error executing multi-personnel command: {e}")
            return {
                'success': False,
                'error': str(e),
                'requires_response': True,
                'response_message': "Sorry, I couldn't complete those updates. Please try again."
            }
    
    def _send_clarification_question(self, recipient_phone, question):
        """Send a clarification question back to the sender"""
        try:
            # For now, we'll return the response to be sent
            # In a full implementation, this would integrate with Gmail/Google Voice API
            clarification_response = f"FSS AI Agent: {question}\n\nPlease reply with more details."
            
            print(f"Clarification needed for {recipient_phone}: {question}")
            
            return {
                'success': True,
                'needs_clarification': True,
                'requires_response': True,
                'response_message': clarification_response,
                'question': question
            }
            
        except Exception as e:
            print(f"Error sending clarification: {e}")
            return {
                'success': False,
                'error': str(e),
                'requires_response': False
            }
    
    def get_personnel_assignments(self):
        """Get current personnel assignments and statuses"""
        return self.personnel_assignments
    
    def update_personnel_assignment(self, person_id, new_assignment, new_status=None):
        """Manually update a person's assignment and/or status"""
        try:
            for person in self.personnel_assignments:
                if person.get('id') == person_id:
                    if new_assignment:
                        person['assignment'] = new_assignment
                    if new_status:
                        person['status'] = new_status
                    person['last_updated'] = datetime.now().isoformat()
                    
                    self._save_json_file(self.personnel_assignments_file, self.personnel_assignments)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error updating personnel assignment: {e}")
            return False
    
    def _execute_appointment_command(self, parsed_command, sender_phone, original_message):
        """Execute the parsed appointment command"""
        try:
            # Get personnel name from either old format or new format
            personnel_name = parsed_command.get('personnel_name')
            if not personnel_name and parsed_command.get('personnel_updates'):
                # Try to get from new format
                personnel_updates = parsed_command.get('personnel_updates', [])
                if personnel_updates:
                    personnel_name = personnel_updates[0].get('personnel_name')
            
            appointment_type = parsed_command.get('appointment_type')
            appointment_date = parsed_command.get('appointment_date')
            start_time = parsed_command.get('start_time')
            end_time = parsed_command.get('end_time')
            duration_hours = parsed_command.get('duration_hours')
            all_day = parsed_command.get('all_day', False)
            notes = parsed_command.get('notes')
            
            print(f"Appointment command - Looking for: '{personnel_name}', Found: {personnel_name is not None}")
            
            # Find the person in personnel assignments with improved matching
            person_found = None
            potential_matches = []
            
            if personnel_name:
                # Extract just the last name if it's provided
                name_parts = personnel_name.strip().split()
                search_name = name_parts[-1].lower()  # Get the last word as surname
                
                # Find all people with matching last names
                for person in self.personnel_assignments:
                    person_name_field = person.get('name', '')
                    person_name_parts = person_name_field.split()
                    
                    if len(person_name_parts) >= 2:
                        person_last_name = person_name_parts[-1].lower()  # Get last name
                        
                        # Check for exact last name match
                        if search_name == person_last_name:
                            potential_matches.append(person)
                        # Also check if the full search term matches any part of the name
                        elif personnel_name.lower() in person_name_field.lower():
                            potential_matches.append(person)
                
                # Determine the best match
                if len(potential_matches) == 1:
                    # Unique match found
                    person_found = potential_matches[0]
                elif len(potential_matches) > 1:
                    # Multiple matches - check if one is an exact full name match
                    exact_matches = [p for p in potential_matches if personnel_name.lower() in p.get('name', '').lower()]
                    if len(exact_matches) == 1:
                        person_found = exact_matches[0]
                    else:
                        # Multiple people with same last name - ask for clarification
                        match_names = [p.get('name', 'Unknown') for p in potential_matches]
                        question = f"I found multiple people with the name '{personnel_name}'. Which one do you mean?\n" + "\n".join(match_names)
                        return self._send_clarification_question(sender_phone, question)
            
            print(f"Appointment command - Looking for: '{personnel_name}', Found: {person_found.get('name') if person_found else 'None'}")
            
            if not person_found:
                # Ask for clarification about which person
                available_personnel = [p.get('name', 'Unknown') for p in self.personnel_assignments]
                question = f"I couldn't find '{personnel_name}' in our roster. Did you mean one of these people?\n" + "\n".join(available_personnel[:5])
                
                return self._send_clarification_question(sender_phone, question)
            
            # Create the appointment entry
            appointment_id = f"apt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{person_found.get('id', 'unknown')}"
            
            # Handle multi-day appointments (like leave periods)
            end_date = None
            if end_time and len(str(end_time)) >= 8:  # Looks like a date (YYYY-MM-DD format)
                end_date = end_time
                end_time = None  # Clear end_time since it's actually an end date
            
            appointment = {
                'id': appointment_id,
                'personnel_name': person_found.get('name'),
                'personnel_rank': person_found.get('rank'),  
                'personnel_type': person_found.get('type'),
                'assignment': person_found.get('assignment'),
                'absence_type': appointment_type,
                'appointment_date': appointment_date,
                'start_time': start_time,
                'end_time': end_time,
                'end_date': end_date,  # For multi-day appointments
                'duration_hours': duration_hours,
                'all_day': all_day,
                'original_text': original_message,
                'notes': notes,
                'status': 'active',
                'created_timestamp': datetime.now().isoformat(),
                'created_by': 'web_interface'
            }
            
            # Add to appointments list
            self.appointments.append(appointment)
            self._save_json_file(self.appointments_file, self.appointments)
            
            # Update person's status if appointment is today or ongoing
            today = datetime.now().strftime('%Y-%m-%d')
            if appointment_date == today:
                person_found['status'] = 'on_appointment'
                person_found['last_updated'] = datetime.now().isoformat()
                self._save_json_file(self.personnel_assignments_file, self.personnel_assignments)
            
            # Create confirmation message
            person_display = person_found.get('name', 'Unknown person')
            apt_type_display = appointment_type.replace('_', ' ').title()
            
            if end_date:
                # Multi-day appointment (like leave)
                start_date_display = self._format_date_for_display(appointment_date)
                end_date_display = self._format_date_for_display(end_date)
                confirmation_message = f"Added {apt_type_display} for {person_display} from {start_date_display} to {end_date_display}."
            elif appointment_date and start_time:
                date_display = self._format_date_for_display(appointment_date)
                time_display = self._format_time_for_display(start_time, end_time, all_day)
                confirmation_message = f"Added {apt_type_display} appointment for {person_display} on {date_display} at {time_display}."
            else:
                confirmation_message = f"Added {apt_type_display} appointment for {person_display}."
            
            if appointment_date == today:
                confirmation_message += f" Status updated to 'on appointment'."
            
            # Log the appointment creation
            print(f"Appointment created by {sender_phone}: {person_display} - {apt_type_display} on {appointment_date}")
            
            return {
                'success': True,
                'appointment_created': appointment,
                'person_updated': person_found if appointment_date == today else None,
                'requires_response': True,
                'response_message': confirmation_message
            }
            
        except Exception as e:
            print(f"Error executing appointment command: {e}")
            return {
                'success': False,
                'error': str(e),
                'requires_response': True,
                'response_message': "Sorry, I couldn't create that appointment. Please try again with more details."
            }
    
    def _format_date_for_display(self, date_str):
        """Format date string for display"""
        try:
            date_obj = datetime.fromisoformat(date_str)
            today = datetime.now().date()
            tomorrow = datetime.now().date().replace(day=today.day + 1)
            
            if date_obj.date() == today:
                return "today"
            elif date_obj.date() == tomorrow:
                return "tomorrow"
            else:
                return date_obj.strftime('%A, %B %d')
        except:
            return date_str
    
    def _format_time_for_display(self, start_time, end_time=None, all_day=False):
        """Format time for display"""
        if all_day:
            return "all day"
        
        if not start_time:
            return "time TBD"
        
        try:
            # Convert HHMM to display format
            hours = int(start_time[:2])
            minutes = start_time[2:4] if len(start_time) > 2 else "00"
            ampm = "PM" if hours >= 12 else "AM"
            display_hours = hours if hours <= 12 else hours - 12
            if display_hours == 0:
                display_hours = 12
            
            start_display = f"{display_hours}:{minutes} {ampm}"
            
            if end_time:
                end_hours = int(end_time[:2])
                end_minutes = end_time[2:4] if len(end_time) > 2 else "00"
                end_ampm = "PM" if end_hours >= 12 else "AM"
                end_display_hours = end_hours if end_hours <= 12 else end_hours - 12
                if end_display_hours == 0:
                    end_display_hours = 12
                
                end_display = f"{end_display_hours}:{end_minutes} {end_ampm}"
                return f"{start_display} - {end_display}"
            else:
                return start_display
                
        except:
            return start_time
