#!/usr/bin/env python3
"""
Start both Flask backend and React frontend with one command
"""

import subprocess
import os
import sys
import time
import webbrowser
from threading import Thread

def start_flask():
    """Start the Flask backend server"""
    print("🚀 Starting Flask backend on http://localhost:5000...")
    subprocess.run([sys.executable, "start_website.py"])

def start_react():
    """Start the React frontend dev server"""
    print("⚛️  Starting React frontend on http://localhost:5173...")
    os.chdir("frontend")
    subprocess.run(["npm", "run", "dev"], shell=True)

def open_browser():
    """Open the React app in browser after a delay"""
    time.sleep(3)  # Wait for servers to start
    webbrowser.open("http://localhost:5173")

if __name__ == "__main__":
    print("🎯 Starting Vera Full Stack Application")
    print("=" * 50)
    
    # Check if npm is installed
    try:
        subprocess.run(["npm", "--version"], capture_output=True, shell=True, check=True)
    except:
        print("❌ Error: npm is not installed. Please install Node.js first.")
        sys.exit(1)
    
    # Check if frontend dependencies are installed
    if not os.path.exists("frontend/node_modules"):
        print("📦 Installing React dependencies...")
        os.chdir("frontend")
        subprocess.run(["npm", "install"], shell=True)
        os.chdir("..")
    
    # Start both servers in separate threads
    flask_thread = Thread(target=start_flask, daemon=True)
    react_thread = Thread(target=start_react, daemon=True)
    
    flask_thread.start()
    time.sleep(2)  # Give Flask a head start
    react_thread.start()
    
    # Open browser
    browser_thread = Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    print("\n✅ Both servers are running!")
    print("📍 Flask API: http://localhost:5000")
    print("📍 React App: http://localhost:5173")
    print("\nPress Ctrl+C to stop all servers")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down servers...")
        sys.exit(0)