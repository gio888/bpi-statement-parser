#!/usr/bin/env python3
"""
BPI Statement Parser - Web Interface Launcher
Quick launcher script that starts the Flask server and opens the browser
"""

import os
import sys
import time
import webbrowser
import subprocess
import signal
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_cors
        return True
    except ImportError:
        print("\n❌ Missing required dependencies!")
        print("Please run: pip install flask flask-cors")
        print("\nOr activate your virtual environment first:")
        print("  source venv/bin/activate  # On macOS/Linux")
        print("  venv\\Scripts\\activate    # On Windows")
        return False

def start_server():
    """Start the Flask server"""
    print("\n" + "="*60)
    print("🚀 Starting BPI Statement Parser Web Interface")
    print("="*60)
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # Get the project root directory
    project_root = Path(__file__).parent
    web_app_path = project_root / "src" / "web_app.py"
    
    if not web_app_path.exists():
        print(f"❌ Error: web_app.py not found at {web_app_path}")
        sys.exit(1)
    
    # Start the Flask server
    print("📦 Starting Flask server...")
    
    try:
        # Run the Flask app
        server_process = subprocess.Popen(
            [sys.executable, str(web_app_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Check if server started successfully
        if server_process.poll() is not None:
            # Server exited, something went wrong
            stdout, stderr = server_process.communicate()
            print(f"❌ Server failed to start:")
            if stderr:
                print(stderr)
            if stdout:
                print(stdout)
            sys.exit(1)
        
        # Open browser
        url = "http://localhost:8080"
        print(f"🌐 Opening browser to {url}")
        print("-"*60)
        print("✅ Server is running!")
        print("\n📌 Leave this terminal open while using the app")
        print("📌 Press Ctrl+C to stop the server\n")
        print("-"*60)
        
        # Open the browser
        webbrowser.open(url)
        
        # Keep the script running and handle Ctrl+C gracefully
        try:
            # Read server output
            while True:
                output = server_process.stdout.readline()
                if output:
                    print(output.strip())
                # Check if process is still running
                if server_process.poll() is not None:
                    break
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("✅ Server stopped. Goodbye!")
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║            BPI STATEMENT PARSER - WEB INTERFACE              ║
╠══════════════════════════════════════════════════════════════╣
║  Upload your BPI credit card PDFs through a simple           ║
║  web interface and get accounting-ready CSV files!           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check if running in virtual environment (recommended)
    if not hasattr(sys, 'prefix'):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Recommended: source venv/bin/activate\n")
    
    start_server()

if __name__ == "__main__":
    main()