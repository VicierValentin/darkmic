#!/usr/bin/env python3
"""
Keyboard Logger using evtest
Reads keyboard input and writes to a text file
Enhanced with proper ALT_RIGHT functionality
"""

import subprocess
import sys
import os
import signal
import time
import threading
from datetime import datetime

class KeyboardLogger:
    def __init__(self, output_file="keyboard_log.txt", device_path=None):
        self.output_file = output_file
        self.device_path = device_path
        self.process = None
        self.running = False
        self.log_file = None
        
        # Key code to character mapping (US layout)
        self.key_map = {
            'KEY_A': 'a', 'KEY_B': 'b', 'KEY_C': 'c', 'KEY_D': 'd', 'KEY_E': 'e',
            'KEY_F': 'f', 'KEY_G': 'g', 'KEY_H': 'h', 'KEY_I': 'i', 'KEY_J': 'j',
            'KEY_K': 'k', 'KEY_L': 'l', 'KEY_M': 'm', 'KEY_N': 'n', 'KEY_O': 'o',
            'KEY_P': 'p', 'KEY_Q': 'q', 'KEY_R': 'r', 'KEY_S': 's', 'KEY_T': 't',
            'KEY_U': 'u', 'KEY_V': 'v', 'KEY_W': 'w', 'KEY_X': 'x', 'KEY_Y': 'y',
            'KEY_Z': 'z', 'KEY_1': '1', 'KEY_2': '2', 'KEY_3': '3', 'KEY_4': '4',
            'KEY_5': '5', 'KEY_6': '6', 'KEY_7': '7', 'KEY_8': '8', 'KEY_9': '9',
            'KEY_0': '0', 'KEY_SPACE': ' ', 'KEY_ENTER': '\n', 'KEY_TAB': '\t',
            'KEY_BACKSPACE': '[BACKSPACE]', 'KEY_DELETE': '[DELETE]',
            'KEY_LEFTSHIFT': '[SHIFT]', 'KEY_RIGHTSHIFT': '[SHIFT]',
            'KEY_LEFTCTRL': '[CTRL]', 'KEY_RIGHTCTRL': '[CTRL]',
            'KEY_LEFTALT': '[ALT]', 'KEY_RIGHTALT': '[ALT_RIGHT]',
            'KEY_ESC': '[ESC]', 'KEY_F1': '[F1]', 'KEY_F2': '[F2]', 'KEY_F3': '[F3]',
            'KEY_F4': '[F4]', 'KEY_F5': '[F5]', 'KEY_F6': '[F6]', 'KEY_F7': '[F7]',
            'KEY_F8': '[F8]', 'KEY_F9': '[F9]', 'KEY_F10': '[F10]', 'KEY_F11': '[F11]',
            'KEY_F12': '[F12]', 'KEY_UP': '[UP]', 'KEY_DOWN': '[DOWN]',
            'KEY_LEFT': '[LEFT]', 'KEY_RIGHT': '[RIGHT]', 'KEY_HOME': '[HOME]',
            'KEY_END': '[END]', 'KEY_PAGEUP': '[PAGEUP]', 'KEY_PAGEDOWN': '[PAGEDOWN]',
            'KEY_DOT': '.', 'KEY_COMMA': ',', 'KEY_SEMICOLON': ';',
            'KEY_APOSTROPHE': "'", 'KEY_GRAVE': '`', 'KEY_MINUS': '-',
            'KEY_EQUAL': '=', 'KEY_LEFTBRACE': '[LEFTBRACE]', 'KEY_RIGHTBRACE': ']',
            'KEY_BACKSLASH': '\\', 'KEY_SLASH': '/', 'KEY_102ND': '[<]',
            
            # Numpad keys
            'KEY_KP0': ')', 'KEY_KP1': '!', 'KEY_KP2': '@',
            'KEY_KP3': '#', 'KEY_KP4': '$', 'KEY_KP5': '%',
            'KEY_KP6': '^', 'KEY_KP7': '&', 'KEY_KP8': '*',
            'KEY_KP9': '(', 'KEY_KPDOT': '.', 'KEY_KPPLUS': '+',
            'KEY_KPMINUS': '6', 'KEY_KPASTERISK': '\\', 'KEY_KPSLASH': '>',
            'KEY_KPENTER': '\n', 'KEY_KPEQUAL': '[NUM=]',
            'KEY_NUMLOCK': '[NUMLOCK]', 'KEY_KPCOMMA': '[NUM,]',
            'KEY_KPLEFTPAREN': '[NUM(]', 'KEY_KPRIGHTPAREN': '[NUM)]'
        }
        
        # Shift key modifications
        self.shift_map = {
            '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
            '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
            '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
            ';': ':', "'": '"', '`': '~', ',': '<', '.': '>',
            '/': '?', '[<]': '[>]',
        }
        
        # ALT_RIGHT + key combinations (AltGr on many keyboards)
        self.altgr_map = {
            '2': '[~]',   '3': '[#]',   '4': '[{]',
            '5': '[[]',   '6': '[|]',   '7': '[`]',   '8': '[\\]',
            '9': '[^]',   '0': '[@]',   '-': '[BRACK]', '=': '[}]',
        }
        
        self.shift_pressed = False
        self.left_alt_pressed = False
        self.right_alt_pressed = False
        self.caps_lock = False
        self.num_lock = True  # Numpad usually starts with NumLock on

    def find_keyboard_device(self):
        """Find the keyboard device automatically"""
        try:
            # List input devices
            result = subprocess.run(['ls', '/dev/input/'], capture_output=True, text=True)
            devices = result.stdout.strip().split('\n')
            
            # Look for event devices
            event_devices = [d for d in devices if d.startswith('event')]
            
            for device in event_devices:
                device_path = f'/dev/input/{device}'
                try:
                    # Test if it's a keyboard by checking capabilities
                    result = subprocess.run(['evtest', device_path], 
                                          input='\n', capture_output=True, 
                                          text=True, timeout=2)
                    
                    if 'EV_KEY' in result.stdout and 'KEY_A' in result.stdout:
                        print(f"Found keyboard device: {device_path}")
                        return device_path
                except:
                    continue
                    
            return None
            
        except Exception as e:
            print(f"Error finding keyboard device: {e}")
            return None

    def list_input_devices(self):
        """List all available input devices"""
        try:
            print("Available input devices:")
            result = subprocess.run(['ls', '-la', '/dev/input/'], capture_output=True, text=True)
            print(result.stdout)
            
            # Try to get more info about event devices
            event_devices = subprocess.run(['ls', '/dev/input/event*'], 
                                         shell=True, capture_output=True, text=True)
            if event_devices.returncode == 0:
                print("\nEvent devices:")
                for device in event_devices.stdout.strip().split('\n'):
                    if device:
                        print(f"  {device}")
                        
        except Exception as e:
            print(f"Error listing devices: {e}")

    def start_logging(self):
        """Start the keyboard logging process"""
        if self.running:
            print("Logger is already running!")
            return
            
        # Find device if not specified
        if not self.device_path:
            self.device_path = self.find_keyboard_device()
            
        if not self.device_path:
            print("No keyboard device found!")
            self.list_input_devices()
            return
            
        # Check if device exists
        if not os.path.exists(self.device_path):
            print(f"Device {self.device_path} does not exist!")
            return
            
        # Check if evtest is available
        try:
            subprocess.run(['evtest', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("evtest is not installed. Install it with: sudo apt-get install evtest")
            return
            
        try:
            # Open output file
            self.log_file = open(self.output_file, 'a', encoding='utf-8')
            self.log_file.write(f"")
            self.log_file.flush()
            
            # Start evtest process
            print(f"Starting keyboard logging from {self.device_path}")
            print(f"Output file: {self.output_file}")
            print("Press Ctrl+C to stop logging")
            
            self.process = subprocess.Popen(
                ['evtest', self.device_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.running = True
            
            # Start reading thread
            self.read_thread = threading.Thread(target=self.read_events)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            # Wait for process to complete or be interrupted
            try:
                self.process.wait()
            except KeyboardInterrupt:
                self.stop_logging()
                
        except Exception as e:
            print(f"Error starting logger: {e}")
            self.stop_logging()

    def read_events(self):
        """Read events from evtest output"""
        try:
            while self.running and self.process:
                line = self.process.stdout.readline()
                if not line:
                    break
                    
                self.parse_event_line(line.strip())
                
        except Exception as e:
            print(f"Error reading events: {e}")

    def parse_event_line(self, line):
        """Parse a single event line from evtest"""
        try:
            # Look for key press events (value 1) and key release events (value 0)
            # Format: Event: time 1234567890.123456, type 1 (EV_KEY), code 30 (KEY_A), value 1
            if 'EV_KEY' in line:
                # Extract key name and value
                parts = line.split('(')
                if len(parts) >= 3:
                    key_part = parts[2].split(')')[0]
                    
                    # Check if it's a press (value 1) or release (value 0)
                    if 'value 1' in line and key_part in self.key_map:
                        self.handle_key_press(key_part)
                    elif 'value 0' in line:
                        self.handle_key_release(key_part)
                        
        except Exception as e:
            print(f"Error parsing line: {e}")

    def handle_key_press(self, key):
        """Handle a key press event"""
        try:
            # Handle modifier keys
            if key in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                self.shift_pressed = True
                print(f'[SHIFT_PRESS]', end='', flush=True)
                return
            elif key == 'KEY_LEFTALT':
                self.left_alt_pressed = True
                print(f'[ALT_PRESS]', end='', flush=True)
                return
            elif key == 'KEY_RIGHTALT':
                self.right_alt_pressed = True
                print(f'[ALT_RIGHT_PRESS]', end='', flush=True)
                return
            elif key == 'KEY_CAPSLOCK':
                self.caps_lock = not self.caps_lock
                return
            elif key == 'KEY_NUMLOCK':
                self.num_lock = not self.num_lock
                print(f'[NUMLOCK_{"ON" if self.num_lock else "OFF"}]', end='', flush=True)
                return
                
            # Handle numpad keys based on NumLock state
            if key.startswith('KEY_KP') and key not in ['KEY_KPENTER', 'KEY_KPPLUS', 'KEY_KPMINUS', 'KEY_KPASTERISK', 'KEY_KPSLASH']:
                char = self.handle_numpad_key(key)
            else:
                # Get character for regular keys
                char = self.key_map.get(key, f'[{key}]')
                
                # Apply ALT_RIGHT (AltGr) modifications first
                if self.right_alt_pressed and char.lower() in self.altgr_map:
                    char = self.altgr_map[char.lower()]
                # Apply shift/caps modifications for regular keys
                elif char.isalpha():
                    if self.shift_pressed or self.caps_lock:
                        char = char.upper()
                elif self.shift_pressed and char in self.shift_map:
                    char = self.shift_map[char]
                
            # Write to file
            self.log_file.write(char)
            self.log_file.flush()
            
            # Print to console (optional)
            print(char, end='', flush=True)
            
        except Exception as e:
            print(f"Error handling key press: {e}")

    def handle_numpad_key(self, key):
        """Handle numpad keys based on NumLock state"""
        if self.num_lock:
            # NumLock ON - return numbers/symbols
            numpad_numbers = {
                'KEY_KP0': ')', 'KEY_KP1': '!', 'KEY_KP2': '@',
                'KEY_KP3': '#', 'KEY_KP4': '$', 'KEY_KP5': '%',
                'KEY_KP6': '^', 'KEY_KP7': '&', 'KEY_KP8': '*',
                'KEY_KP9': '(', 'KEY_KPDOT': '<', 'KEY_KPPLUS': '+',
            }
            return numpad_numbers.get(key, self.key_map.get(key, f'[{key}]'))
        else:
            # NumLock OFF - return navigation keys
            numpad_nav = {
                'KEY_KP0': '0', 'KEY_KP1': '1', 'KEY_KP2': '2',
                'KEY_KP3': '3', 'KEY_KP4': '4', 'KEY_KP5': '5',
                'KEY_KP6': '6', 'KEY_KP7': '7', 'KEY_KP8': '8',
                'KEY_KP9': '9', 'KEY_KPDOT': '>',
            }
            return numpad_nav.get(key, self.key_map.get(key, f'[{key}]'))

    def handle_key_release(self, key):
        """Handle a key release event"""
        try:
            # Handle modifier key releases
            if key in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                self.shift_pressed = False
                print(f'[SHIFT_RELEASE]', end='', flush=True)
            elif key == 'KEY_LEFTALT':
                self.left_alt_pressed = False
                print(f'[ALT_RELEASE]', end='', flush=True)
            elif key == 'KEY_RIGHTALT':
                self.right_alt_pressed = False
                print(f'[ALT_RIGHT_RELEASE]', end='', flush=True)
            elif key in ['KEY_LEFTCTRL', 'KEY_RIGHTCTRL']:
                print(f'[CTRL_RELEASE]', end='', flush=True)
            elif key == 'KEY_NUMLOCK':
                print(f'[NUMLOCK_RELEASE]', end='', flush=True)
                
        except Exception as e:
            print(f"Error handling key release: {e}")

    def stop_logging(self):
        """Stop the keyboard logging process"""
        print("\nStopping keyboard logger...")
        self.running = False
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                
        if self.log_file:
            self.log_file.write(f"")
            self.log_file.close()
            
        print(f"Log saved to: {self.output_file}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Keyboard Logger using evtest')
    parser.add_argument('-d', '--device', help='Input device path (e.g., /dev/input/event0)')
    parser.add_argument('-o', '--output', default='keyboard_log.txt', help='Output file name')
    parser.add_argument('-l', '--list', action='store_true', help='List available input devices')
    
    args = parser.parse_args()
    
    if args.list:
        logger = KeyboardLogger()
        logger.list_input_devices()
        return
        
    # Check if running as root
    if os.geteuid() != 0:
        print("Warning: This script may need to run as root to access input devices")
        print("Try: sudo python3 keyboard_logger.py")
        
    logger = KeyboardLogger(output_file=args.output, device_path=args.device)
    
    def signal_handler(signum, frame):
        logger.stop_logging()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.start_logging()
    except KeyboardInterrupt:
        logger.stop_logging()

if __name__ == "__main__":
    main()