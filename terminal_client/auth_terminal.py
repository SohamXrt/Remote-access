#!/usr/bin/env python3
"""
Hacker-style terminal interface for biometric authentication
Green text on black background with cool terminal effects
"""
import os
import sys
import time
import threading
import subprocess
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align
import qrcode
from io import StringIO
import requests
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.crypto_utils import CryptoManager

class HackerTerminal:
    def __init__(self):
        self.console = Console(
            color_system="256", 
            force_terminal=True,
            width=80,
            height=24
        )
        self.crypto_manager = CryptoManager(config_dir="../configs")
        self.server_url = "http://localhost:8000"
        self.authenticated = False
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear')
        
    def print_banner(self):
        """Print the hacker-style banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        🔒 SECURE ACCESS TERMINAL 🔒                        ║
║                              [UBUNTU SECURE]                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        text = Text(banner, style="bold green")
        self.console.print(text)
        
    def print_status(self, message, status_type="info"):
        """Print status message with appropriate styling"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if status_type == "info":
            style = "cyan"
            prefix = "[INFO]"
        elif status_type == "warning":
            style = "yellow"
            prefix = "[WARN]"
        elif status_type == "error":
            style = "red"
            prefix = "[ERROR]"
        elif status_type == "success":
            style = "bright_green"
            prefix = "[SUCCESS]"
        else:
            style = "white"
            prefix = "[SYSTEM]"
            
        text = Text(f"{timestamp} {prefix} {message}", style=style)
        self.console.print(text)
        
    def print_hacker_text(self, text, delay=0.03):
        """Print text with hacker-style typing effect"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()
        
    def show_pairing_process(self):
        """Show the initial device pairing process"""
        self.clear_screen()
        self.print_banner()
        
        self.print_status("Initializing secure pairing protocol...", "info")
        time.sleep(1)
        
        # Generate pairing code
        pairing_code = self.crypto_manager.generate_pairing_code()
        self.print_status(f"Generated pairing code: {pairing_code}", "success")
        
        # Create QR code for easier pairing
        qr_data = json.dumps({
            "pairing_code": pairing_code,
            "device_id": self.crypto_manager.device_id,
            "device_name": f"Ubuntu-{os.getlogin()}",
            "server_url": self.server_url
        })
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Print QR code to terminal
        f = StringIO()
        qr.print_ascii(out=f)
        f.seek(0)
        qr_ascii = f.read()
        
        self.console.print(Panel(
            qr_ascii,
            title="[bold green]Scan QR Code with Mobile App[/bold green]",
            border_style="green"
        ))
        
        self.console.print(f"[bold cyan]Manual Pairing Code: {pairing_code}[/bold cyan]")
        self.console.print("[yellow]Waiting for mobile device to pair...[/yellow]")
        
        # Wait for pairing (simulate for now)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Waiting for pairing...", total=None)
            
            # Simulate pairing process
            time.sleep(5)
            progress.update(task, description="Pairing successful!")
            
        self.print_status("Device paired successfully!", "success")
        time.sleep(1)
        
    def show_authentication_request(self):
        """Show biometric authentication request"""
        self.clear_screen()
        self.print_banner()
        
        self.print_status("User authentication required", "warning")
        self.print_status("Requesting biometric verification...", "info")
        
        # Show cool loading animation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("📱 Thumb Authentication Required", total=None)
            time.sleep(2)
            
            progress.update(task, description="📤 Sending request to mobile device...")
            time.sleep(2)
            
            progress.update(task, description="👆 Waiting for biometric scan...")
            time.sleep(3)
            
            progress.update(task, description="🔍 Scanning...")
            time.sleep(2)
            
            progress.update(task, description="✅ Biometric verified!")
            time.sleep(1)
        
        self.print_status("Biometric authentication successful!", "success")
        self.print_status("Access granted. Welcome back!", "success")
        self.authenticated = True
        
    def show_system_access(self):
        """Show system access granted screen"""
        self.clear_screen()
        self.print_banner()
        
        self.console.print(Panel(
            "[bold green]🔓 SYSTEM ACCESS GRANTED 🔓[/bold green]\n\n"
            "[cyan]User authenticated successfully[/cyan]\n"
            "[cyan]Mobile device verified[/cyan]\n"
            "[cyan]Session established[/cyan]",
            title="[bold green]Authentication Complete[/bold green]",
            border_style="green"
        ))
        
        self.print_status("Launching desktop environment...", "info")
        time.sleep(2)
        
        # Launch actual desktop session (commented out for demo)
        # subprocess.run(["gnome-session", "--session=ubuntu"])
        
    def show_lock_screen(self):
        """Show the lock screen interface"""
        self.clear_screen()
        self.print_banner()
        
        self.console.print(Panel(
            "[bold red]🔒 SYSTEM LOCKED 🔒[/bold red]\n\n"
            "[yellow]This system is protected by biometric authentication[/yellow]\n"
            "[cyan]Use your registered mobile device to unlock[/cyan]",
            title="[bold red]Access Restricted[/bold red]",
            border_style="red"
        ))
        
        self.console.print("\n[dim]Authorized personnel only[/dim]")
        
    def monitor_system_events(self):
        """Monitor system events and show relevant messages"""
        events = [
            ("System boot detected", "info"),
            ("Network connection established", "success"),
            ("Secure tunnel activated", "success"),
            ("Mobile device connection verified", "success"),
            ("Biometric sensor ready", "info"),
            ("Waiting for authentication...", "warning")
        ]
        
        for event, status_type in events:
            self.print_status(event, status_type)
            time.sleep(0.5)
            
    def run_demo(self):
        """Run a demo of the terminal interface"""
        try:
            # Check if this is first run (pairing needed)
            paired_devices = self.crypto_manager.load_paired_devices()
            
            if not paired_devices:
                self.show_pairing_process()
                
            # Show authentication process
            self.show_authentication_request()
            
            if self.authenticated:
                self.show_system_access()
            else:
                self.show_lock_screen()
                
        except KeyboardInterrupt:
            self.console.print("\n[red]Authentication cancelled by user[/red]")
            sys.exit(1)
            
    def run_lock_mode(self):
        """Run in lock mode - show lock screen until authenticated"""
        while not self.authenticated:
            self.show_lock_screen()
            time.sleep(5)
            
            # Check for authentication (would be real check in production)
            # For demo, we'll simulate authentication after 10 seconds
            self.console.print("[yellow]Checking for authentication...[/yellow]")
            time.sleep(2)
            
            # Simulate authentication check
            if input("Press Enter to simulate biometric auth (or 'q' to quit): ").lower() != 'q':
                self.show_authentication_request()
                break

if __name__ == "__main__":
    terminal = HackerTerminal()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--lock":
        terminal.run_lock_mode()
    else:
        terminal.run_demo()