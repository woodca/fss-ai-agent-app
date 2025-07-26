#!/usr/bin/env python3

import os
import time
import argparse
from datetime import datetime
from email_parser import EmailParser
from gpt_parser import GPTParser
from google_voice_responder import GoogleVoiceResponder

def main():
    parser = argparse.ArgumentParser(description='NCOIC Agent - Process Google Voice messages for appointment scheduling')
    parser.add_argument('--interval', '-i', type=int, default=300, help='Check interval in seconds (default: 300)')
    parser.add_argument('--max-messages', '-m', type=int, default=10, help='Maximum messages to process per check (default: 10)')
    parser.add_argument('--once', action='store_true', help='Run once and exit (don\'t loop)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("Starting NCOIC Agent...")
    print(f"Check interval: {args.interval} seconds")
    print(f"Max messages per check: {args.max_messages}")
    
    # Initialize components
    try:
        email_parser = EmailParser()
        gpt_parser = GPTParser()
        voice_responder = GoogleVoiceResponder()
        
        if args.verbose:
            print("Email parser initialized")
            print("GPT parser initialized")
            print("Voice responder initialized")
        
    except Exception as e:
        print(f"Error initializing components: {e}")
        return 1
    
    # Main processing loop
    run_count = 0
    
    while True:
        run_count += 1
        print(f"\nCheck #{run_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Get new Google Voice messages
            messages = email_parser.get_google_voice_messages(max_results=args.max_messages)
            
            if not messages:
                print("No new messages found")
            else:
                print(f"Found {len(messages)} new messages")
                
                # Process each message with GPT
                for i, message in enumerate(messages, 1):
                    if args.verbose:
                        print(f"\nProcessing message {i}/{len(messages)}")
                        print(f"   From: {message.get('phone_number', 'Unknown')}")
                        print(f"   Text: {message.get('message_text', '')[:100]}...")
                    
                    try:
                        # Process with GPT
                        result = gpt_parser.process_message(message)
                        
                        if result.get('status') == 'processed':
                            gpt_analysis = result.get('gpt_analysis', {})
                            
                            if args.verbose:
                                print(f"   Processed successfully")
                                print(f"   Category: {gpt_analysis.get('category', 'Unknown')}")
                                print(f"   Absence report: {gpt_analysis.get('is_absence_report', False)}")
                            
                            # Handle status command results
                            if 'status_command_result' in result:
                                status_result = result['status_command_result']
                                phone = message.get('phone_number', 'Unknown')
                                
                                if status_result.get('success'):
                                    print(f"   ✅ Status command processed successfully")
                                    person_updated = status_result.get('person_updated', {})
                                    if person_updated:
                                        person_name = f"{person_updated.get('rank', '')} {person_updated.get('name', '')}"
                                        print(f"   Updated: {person_name}")
                                        print(f"   Assignment: {person_updated.get('assignment')}")
                                        print(f"   Status: {person_updated.get('status')}")
                                    
                                    # Send confirmation response
                                    if status_result.get('requires_response'):
                                        response_msg = status_result.get('response_message')
                                        voice_responder.send_response(phone, response_msg)
                                        
                                elif status_result.get('needs_clarification'):
                                    print(f"   ❓ Clarification needed for status command")
                                    question = status_result.get('question', '')
                                    print(f"   Question: {question}")
                                    
                                    # Send clarification question
                                    if status_result.get('requires_response'):
                                        response_msg = status_result.get('response_message')
                                        voice_responder.send_response(phone, response_msg)
                            
                            # Summary for absence reports  
                            if gpt_analysis.get('is_absence_report', False):
                                phone = message.get('phone_number', 'Unknown')
                                personnel = gpt_parser.get_personnel_by_phone(phone)
                                name = personnel.get('full_name') if personnel else phone
                                print(f"   New absence report from {name}")
                                absence_type = gpt_analysis.get('absence_type', 'unknown')
                                apt_date = gpt_analysis.get('appointment_date', 'TBD')
                                print(f"   Type: {absence_type}, Date: {apt_date}")
                        
                        else:
                            print(f"   Processing failed: {result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        print(f"   Error processing message: {e}")
                        continue
            
            # Show summary statistics
            pending_appointments = gpt_parser.get_pending_appointments()
            total_contacts = len(gpt_parser.contacts)
            
            print(f"Status: {len(pending_appointments)} active appointments, {total_contacts} total contacts")
            
        except Exception as e:
            print(f"Error during processing cycle: {e}")
        
        # Exit if running once
        if args.once:
            print("Single run completed")
            break
        
        # Wait for next check
        print(f"Waiting {args.interval} seconds until next check...")
        time.sleep(args.interval)

def show_status():
    """Show current status of appointments and contacts"""
    try:
        gpt_parser = GPTParser()
        
        print("\nNCOIC Agent Status Report")
        print("=" * 50)
        
        # Pending appointments
        pending = gpt_parser.get_pending_appointments()
        print(f"\nActive Appointments: {len(pending)}")
        
        for apt in pending[-5:]:  # Show last 5
            name = apt.get('personnel_name', 'Unknown')
            absence_type = apt.get('absence_type', apt.get('service_type', 'General'))
            apt_date = apt.get('appointment_date', 'Unknown')
            start_time = apt.get('start_time', 'TBD')
            
            print(f"  - {name} ({absence_type}) on {apt_date} at {start_time}")
            print(f"    ID: {apt.get('id', 'Unknown')}")
            print()
        
        # Recent contacts
        print(f"Total Contacts: {len(gpt_parser.contacts)}")
        
        recent_contacts = sorted(gpt_parser.contacts, 
                               key=lambda x: x.get('last_contact', ''), 
                               reverse=True)[:5]
        
        print("Recent contacts:")
        for contact in recent_contacts:
            print(f"  - {contact.get('phone_number', 'Unknown')}")
            print(f"    Messages: {contact.get('message_count', 0)}")
            print(f"    Last contact: {contact.get('last_contact', 'Unknown')}")
            print()
    
    except Exception as e:
        print(f"Error showing status: {e}")

def show_menu():
    """Show interactive menu after email processing"""
    while True:
        print("\n" + "="*50)
        print("NCOIC AGENT - Main Menu")
        print("="*50)
        print("1. View Appointment Calendar")
        print("2. Show Status Summary") 
        print("3. Run Email Check Again")
        print("4. Exit")
        print("-"*50)
        
        try:
            choice = input("Select an option (1-4): ").strip()
            
            if choice == '1':
                from view_appointments import view_appointments
                view_appointments()
            elif choice == '2':
                show_status()
            elif choice == '3':
                print("\nRunning email check...")
                break  # Exit menu to run email check again
            elif choice == '4':
                print("Goodbye!")
                exit(0)
            else:
                print("Invalid choice. Please enter 1-4.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            exit(0)

if __name__ == "__main__":
    # Check for special commands (single word commands without dashes)
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1]
        if command == 'status':
            show_status()
            exit(0)
        elif command == 'appointments' or command == 'calendar':
            from view_appointments import view_appointments
            view_appointments()
            exit(0)
        elif command.startswith('-'):
            # This is a flag, not a command - let argparse handle it
            pass
        else:
            print(f"Unknown command: {command}")
            print("Available commands:")
            print("  status      - Show current status")
            print("  appointments - Show appointment calendar") 
            print("  calendar    - Show appointment calendar")
            print("\nOr use flags like --once --verbose for email processing")
            exit(1)
    
    # Run main email processing
    while True:
        exit_code = main()
        if exit_code and exit_code != 0:
            exit(exit_code)
        
        # Show menu after email processing completes
        show_menu()
