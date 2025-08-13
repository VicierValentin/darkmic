#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import re
from datetime import datetime

class BluetoothCommandMonitor:
    def __init__(self, device_path="/dev/rfcomm0"):
        self.device_path = device_path
        self.running = True
        
        # Define command patterns and their corresponding actions
        self.commands = {
            "mimifr": self.mimifr_command,
            "mimien": self.mimien_command,
            "mimiwin": self.mimiwin_command,
            "shutdown": self.shutdown_command,
            "reboot": self.reboot_command,
            "hello": self.hello_command,
            "status": self.status_command,
            "time": self.time_command,
            "help": self.help_command,
            "exit": self.exit_command
        }
        
        print(f"Starting Bluetooth Command Monitor on {device_path}")
        print("Supported commands:", ", ".join(self.commands.keys()))
        print("Ctrl+C to stop\n")

    def log_message(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def mimifr_command(self, full_message):
        """Custom mimifr command - you can customize this"""
        self.log_message("MimiFR command received!")
        # Example: play a sound, flash LED, etc.
        try:
            # Example: execute script at /home/debian/sendmimifr.sh
            subprocess.run(["bash", "/home/debian/sendmimifr.sh"], check=True)
            return "MimiFR command executed successfully"
        except Exception as e:
            self.log_message(f"MimiFR command failed: {e}")
            return f"MimiFR command failed: {e}"

    def mimien_command(self, full_message):
        """Custom mimien command - you can customize this"""
        self.log_message("MimiEN command received!")
        # Example: play a sound, flash LED, etc.
        try:
            # Example: execute script at /home/debian/sendmimien.sh
            subprocess.run(["bash", "/home/debian/sendmimien.sh"], check=True)
            return "MimiEN command executed successfully"
        except Exception as e:
            self.log_message(f"MimiEN command failed: {e}")
            return f"MimiEN command failed: {e}"
    
    def mimiwin_command(self, full_message):
        """Custom mimiwin command - you can customize this"""
        self.log_message("MimiWIN command received!")
        # Example: play a sound, flash LED, etc.
        try:
            # Example: execute bash script at /home/debian/sendmimiwin.sh
            subprocess.run(["bash", "/home/debian/sendmimiwin.sh"], check=True)
            return "MimiWIN command executed successfully"
        except Exception as e:
            self.log_message(f"MimiWIN command failed: {e}")
            return f"MimiWIN command failed: {e}"

    def shutdown_command(self, full_message):
        """Shutdown the system"""
        self.log_message("SHUTDOWN command received!")
        try:
            # Add a delay and confirmation
            self.log_message("System will shutdown in 5 seconds...")
            time.sleep(5)
            subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
            return "Shutdown initiated"
        except subprocess.CalledProcessError as e:
            self.log_message(f"Shutdown failed: {e}")
            return f"Shutdown failed: {e}"
        except Exception as e:
            self.log_message(f"Shutdown error: {e}")
            return f"Shutdown error: {e}"

    def reboot_command(self, full_message):
        """Reboot the system"""
        self.log_message("REBOOT command received!")
        try:
            self.log_message("System will reboot in 5 seconds...")
            time.sleep(5)
            subprocess.run(["sudo", "reboot"], check=True)
            return "Reboot initiated"
        except subprocess.CalledProcessError as e:
            self.log_message(f"Reboot failed: {e}")
            return f"Reboot failed: {e}"

    def hello_command(self, full_message):
        """Simple hello response"""
        response = "Hello from BeagleBone Black!"
        self.log_message(f"Responding: {response}")
        return response

    def status_command(self, full_message):
        """Get system status"""
        try:
            # Get uptime
            uptime = subprocess.check_output(["uptime"], text=True).strip()
            # Get memory usage
            memory = subprocess.check_output(["free", "-h"], text=True).strip()
            response = f"System Status:\nUptime: {uptime}\nMemory: {memory.split()[1]}"
            self.log_message("Status command executed")
            return response
        except Exception as e:
            return f"Status check failed: {e}"

    def time_command(self, full_message):
        """Get current time"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = f"Current time: {current_time}"
        self.log_message(f"Time requested: {current_time}")
        return response

    def help_command(self, full_message):
        """Show available commands"""
        commands_list = "\n".join([f"- {cmd}" for cmd in self.commands.keys()])
        response = f"Available commands:\n{commands_list}"
        self.log_message("Help requested")
        return response

    def exit_command(self, full_message):
        """Exit the monitor"""
        self.log_message("Exit command received")
        self.running = False
        return "Monitor stopping..."

    def execute_command(self, command_word, full_message):
        """Execute the command and return response"""
        if command_word in self.commands:
            try:
                response = self.commands[command_word](full_message)
                return response
            except Exception as e:
                error_msg = f"Error executing {command_word}: {e}"
                self.log_message(error_msg)
                return error_msg
        else:
            return f"Unknown command: {command_word}"

    def send_response(self, response):
        return None, None
        """Send response back through Bluetooth if possible"""
        try:
            if os.path.exists(self.device_path):
                with open(self.device_path, 'w') as f:
                    f.write(f"{response}\n")
                    f.flush()
        except Exception as e:
            self.log_message(f"Failed to send response: {e}")

    def parse_message(self, message):
        """Parse incoming message for commands"""
        # Clean the message
        message = message.strip().lower()
        
        if not message:
            return None, message
            
        # Extract the first word as potential command
        words = message.split()
        if words:
            command_word = words[0]
            # Check if it matches any of our commands
            if command_word in self.commands:
                return command_word, message
                
        # Also check if command is anywhere in the message (more flexible)
        for command in self.commands:
            if command in message:
                return command, message
                
        return None, message

    def monitor_device(self):
        """Main monitoring loop"""
        buffer = ""
        
        while self.running:
            try:
                # Check if device exists
                if not os.path.exists(self.device_path):
                    self.log_message(f"Waiting for {self.device_path} to become available...")
                    time.sleep(2)
                    continue
                
                # Try to open and read from device
                try:
                    with open(self.device_path, 'r') as device:
                        # Set non-blocking mode
                        import fcntl
                        fd = device.fileno()
                        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                        
                        while self.running:
                            try:
                                data = device.read(1024)
                                if data:
                                    buffer += data
                                    
                                    # Process complete lines
                                    while '\n' in buffer:
                                        line, buffer = buffer.split('\n', 1)
                                        line = line.strip()
                                        
                                        if line:
                                            self.log_message(f"Received: '{line}'")
                                            
                                            # Parse for commands
                                            command, full_message = self.parse_message(line)
                                            
                                            if command:
                                                self.log_message(f"Executing command: {command}")
                                                response = self.execute_command(command, full_message)
                                                self.send_response(response)
                                            else:
                                                self.log_message("No recognized command found")
                                
                                else:
                                    time.sleep(0.1)  # Short sleep to prevent busy waiting
                                    
                            except IOError:
                                # No data available (non-blocking mode)
                                time.sleep(0.1)
                            except Exception as e:
                                self.log_message(f"Read error: {e}")
                                break
                                
                except FileNotFoundError:
                    self.log_message(f"Device {self.device_path} not found")
                    time.sleep(2)
                except PermissionError:
                    self.log_message(f"Permission denied accessing {self.device_path}")
                    self.log_message("Try running with sudo or check device permissions")
                    time.sleep(5)
                except Exception as e:
                    self.log_message(f"Device error: {e}")
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                self.log_message("Received interrupt signal")
                self.running = False
            except Exception as e:
                self.log_message(f"Unexpected error: {e}")
                time.sleep(1)

    def start(self):
        """Start the monitoring process"""
        try:
            self.monitor_device()
        except KeyboardInterrupt:
            pass
        finally:
            self.log_message("Bluetooth Command Monitor stopped")

def main():
    # Allow custom device path as command line argument
    device_path = sys.argv[1] if len(sys.argv) > 1 else "/dev/rfcomm0"
    
    # Create and start monitor
    monitor = BluetoothCommandMonitor(device_path)
    monitor.start()

if __name__ == "__main__":
    main()