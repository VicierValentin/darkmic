#!/usr/bin/env python3
"""
BeagleBone Black AZERTY Keyboard Logger and USB HID Emulator

This application:
1. Reads keyboard input from USB keyboard with AZERTY layout
2. Logs all typed characters to a local text file
3. Emulates a USB HID keyboard via /dev/hidg0
4. Properly handles modifier keys (Shift, Ctrl, AltGr, etc.)

Requirements:
- keyboard library: pip install keyboard
- Root privileges to access /dev/input/eventX and /dev/hidg0
- USB gadget configured on BeagleBone Black

Author: Assistant
Date: 2025
"""

import keyboard
import time
import logging
from datetime import datetime
from threading import Lock
import struct
import os

class AzertyKeyboardProcessor:
    """
    Handles AZERTY keyboard input processing, logging, and USB HID emulation
    """
    
    def __init__(self, log_file="keyboard_log.txt", hid_device="/dev/hidg0"):
        self.log_file = log_file
        self.hid_device = hid_device
        self.log_lock = Lock()
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Current modifier states
        self.modifiers = {
            'shift': False,
            'ctrl': False,
            'alt': False,
            'altgr': False,
            'win': False
        }
        
        # AZERTY key mapping without modifiers
        self.azerty_base_map = {
            'a': 0x04,
            'b': 0x05,
            'c': 0x06,
            'd': 0x07,
            'e': 0x08,
            'f': 0x09,
            'g': 0x0A,
            'h': 0x0B,
            'i': 0x0C,
            'j': 0x0D,
            'k': 0x0E,
            'l': 0x0F,
            'm': 0x10,
            'n': 0x11,
            'o': 0x12,
            'p': 0x13,
            'q': 0x14,
            'r': 0x15,
            's': 0x16,
            't': 0x17,
            'u': 0x18,
            'v': 0x19,
            'w': 0x1A,
            'x': 0x1B,
            'y': 0x1C,
            'z': 0x1D,

            'k0': 0x27,
            'k1': 0x1E,
            'k2': 0x1F,
            'k3': 0x20,
            'k4': 0x21,
            'k5': 0x22,
            'k6': 0x23,
            'k7': 0x24,
            'k8': 0x25,
            'k9': 0x26,

            '0': 0x27,
            '1': 0x1E,
            '2': 0x1F,
            '3': 0x20,
            '4': 0x21,
            '5': 0x22,
            '6': 0x23,
            '7': 0x24,
            '8': 0x25,
            '9': 0x26,

            '^': 0x2F,
            '&': 0x1E,
            '*': 0x32,
            '(': 0x22,
            ')': 0x2D,
            '$': 0x30, 
            '!': 0x38,
            '-': 0x23,
            '−': 0x2D,
            '=': 0x2E,
            ';': 0x33,

            '[': 0x2F,
            ']': 0x30,
            '\'': 0x34,
            '\\': 0x32,
            'c<': 0x64,
            'k>': 0x64,
            ',': 0x36,
            '.': 0x37,
            '/': 0x38,
            '`': 0x35,

            'k.': 0x36,
            '×': 0x32,  # Multiplication signœ

            # Special keys
            'space': 0x2C, 'enter': 0x28, 'backspace': 0x2A, 'tab': 0x2B,
            'escape': 0x29, 'delete': 0x4C, 'insert': 0x49,
            'home': 0x4A, 'end': 0x4D, 'page up': 0x4B, 'page down': 0x4E,
            
            # Arrow keys
            'up': 0x52, 'down': 0x51, 'left': 0x50, 'right': 0x4F,
            
            # Function keys
            'f1': 0x3A, 'f2': 0x3B, 'f3': 0x3C, 'f4': 0x3D,
            'f5': 0x3E, 'f6': 0x3F, 'f7': 0x40, 'f8': 0x41,
            'f9': 0x42, 'f10': 0x43, 'f11': 0x44, 'f12': 0x45,
        }
        
        # AZERTY characters with Shift modifier
        self.azerty_shift_map = {
           '!': 0x1E,
           '@': 0x1F,
           '#': 0x20,
           '$': 0x21,
           '%': 0x22,
           '^': 0x23,
           '&': 0x24,
           '*': 0x25,
           '(': 0x26,
           ')': 0x27,
           ':': 0x33,

            '_': 0x2D,  # °
            '+': 0x2E,

            '"': 0x34, 
            '<': 0x36,
            '>': 0x37,
            '?': 0x38,
            '|': 0x32, 
            '{': 0x2F,
            '}': 0x30,

            '÷': 0x37,  # Division sign

            'c>': 0x64,

        }
        
        # AZERTY characters with AltGr modifier
        self.azerty_altgr_map = {
            '@': 0x1F,
           '3': 0x20,
           '$': 0x21,
           '5': 0x22,
           '6': 0x23,
           '{': 0x24,
           '[': 0x25,
           ']': 0x26,
           '}': 0x27,
           '\\': 0x2D,
            '=': 0x2E,
            '~': 0x35,
        }
        
        # USB HID modifier byte values
        self.hid_modifiers = {
            'left_ctrl': 0x01,
            'left_shift': 0x02,
            'left_alt': 0x04,
            'left_win': 0x08,
            'right_ctrl': 0x10,
            'right_shift': 0x20,
            'right_alt': 0x40,  # AltGr
            'right_win': 0x80
        }
        
        # Initialize HID device
        self.hid_fd = None
        self.init_hid_device()
        
        self.logger.info("AZERTY Keyboard Processor initialized")
    
    def init_hid_device(self):
        """Initialize the USB HID gadget device"""
        try:
            self.hid_fd = os.open(self.hid_device, os.O_WRONLY | os.O_NONBLOCK)
            self.logger.info(f"HID device {self.hid_device} opened successfully")
        except Exception as e:
            self.logger.error(f"Failed to open HID device {self.hid_device}: {e}")
            self.hid_fd = None
    
    def log_keystroke(self, key_info):
        """Log keystroke to file with timestamp"""
        with self.log_lock:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    f.write(f"[{timestamp}] {key_info}\n")
            except Exception as e:
                self.logger.error(f"Failed to write to log file: {e}")
    
    def get_hid_scancode(self, key_name, hid_modifiers_byte):
        """Get USB HID scancode for a key"""
        key_lower = key_name.lower()
        # Check if key is in shift map
        if key_lower in self.azerty_altgr_map and 'altgr' in self.modifiers and self.modifiers['altgr']:
            print(f"Key is an AltGr character: {key_lower}")
            return self.azerty_altgr_map[key_lower], 0x40  # AltGr modifier
        if key_lower in self.azerty_shift_map:
            print(f"Key is a shifted character: {key_lower}")
            return self.azerty_shift_map[key_lower], 0x20
        # Check if key is in numkey map
        if key_lower.startswith('k') and len(key_lower) > 1:
            print(f"Key is a numkey: {key_lower}")
            return self.azerty_base_map.get(key_lower, 0x00), 0x20
        if key_lower.startswith('c') and len(key_lower) > 1:
            print(f"Key is a numkey: {key_lower}")
            return self.azerty_base_map.get(key_lower, 0x00), 0x00
        return self.azerty_base_map.get(key_lower, 0x00), 0x00

    def create_hid_report(self, scancode, modifiers_byte):
        """Create USB HID keyboard report"""
        # HID report format: [modifier_byte, reserved, key1, key2, key3, key4, key5, key6]
        report = struct.pack('8B', modifiers_byte, 0x00, scancode, 0x00, 0x00, 0x00, 0x00, 0x00)
        return report
    
    def send_hid_report(self, report):
        """Send HID report to USB gadget"""
        if self.hid_fd is not None:
            try:
                os.write(self.hid_fd, report)
                return True
            except Exception as e:
                self.logger.error(f"Failed to send HID report: {e}")
                return False
        return False
    
    def send_key_release(self):
        """Send key release report (all zeros)"""
        release_report = struct.pack('8B', 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
        self.send_hid_report(release_report)
    
    def process_character(self, char, modifiers_state):
        """Process a character with its modifiers and send appropriate HID report"""
        scancode = 0x00
        hid_modifiers_byte = 0x00

        print(f"Processing character: {char}, with modifiers: {modifiers_state}\n")
        
        
        
        # Add other modifiers
        if modifiers_state.get('ctrl', False):
            hid_modifiers_byte |= self.hid_modifiers['left_ctrl']
        if modifiers_state.get('right_ctrl', False):
            hid_modifiers_byte |= self.hid_modifiers['right_ctrl']
        if modifiers_state.get('shift', False):
            hid_modifiers_byte |= self.hid_modifiers['left_shift']
        if modifiers_state.get('alt', False):
            hid_modifiers_byte |= self.hid_modifiers['left_alt']
        if modifiers_state.get('win', False):
            hid_modifiers_byte |= self.hid_modifiers['left_win']

        scancode, modi = self.get_hid_scancode(char, hid_modifiers_byte)
        hid_modifiers_byte |= modi
        print(f"Scancode: {scancode}, Modifiers byte: {hid_modifiers_byte}\n")


        # Create and send HID report
        if scancode != 0x00:
            print(f"Creating HID report for scancode: {scancode}, modifiers: {hid_modifiers_byte}\n")
            report = self.create_hid_report(scancode, hid_modifiers_byte)
            success = self.send_hid_report(report)
            
            # Small delay and then send key release
            time.sleep(0.01)
            self.send_key_release()
            
            return success
        
        return False
    
    def handle_special_key(self, key_name, modifiers_state):
        """Handle special keys (function keys, arrows, etc.)"""
        
        hid_modifiers_byte = 0x00

        # Add modifiers
        if modifiers_state.get('shift', False):
            hid_modifiers_byte |= self.hid_modifiers['left_shift']
        if modifiers_state.get('ctrl', False):
            hid_modifiers_byte |= self.hid_modifiers['left_ctrl']
        if modifiers_state.get('alt', False):
            hid_modifiers_byte |= self.hid_modifiers['left_alt']
        if modifiers_state.get('altgr', False):
            hid_modifiers_byte |= self.hid_modifiers['right_alt']
        if modifiers_state.get('win', False):
            hid_modifiers_byte |= self.hid_modifiers['left_win']
        
        scancode, trash = self.get_hid_scancode(key_name, hid_modifiers_byte)
        

        if scancode != 0x00:
            report = self.create_hid_report(scancode, hid_modifiers_byte)
            success = self.send_hid_report(report)
            
            # Small delay and then send key release
            time.sleep(0.01)
            self.send_key_release()
            
            return success
        
        return False
    
    def on_key_event(self, event):
        """Handle keyboard events"""
        try:
            # Update modifier states
            if event.name in ['shift', 'left shift', 'right shift']:
                self.modifiers['shift'] = (event.event_type == keyboard.KEY_DOWN)
            elif event.name in ['ctrl', 'left ctrl', 'right ctrl']:
                self.modifiers['ctrl'] = (event.event_type == keyboard.KEY_DOWN)
            elif event.name in ['alt', 'left alt']:
                self.modifiers['alt'] = (event.event_type == keyboard.KEY_DOWN)
            elif event.name in ['alt gr', 'right alt']:
                self.modifiers['altgr'] = (event.event_type == keyboard.KEY_DOWN)
            elif event.name in ['windows', 'left windows', 'right windows']:
                self.modifiers['win'] = (event.event_type == keyboard.KEY_DOWN)
            
            # Process key press events (not releases or repeats)
            if event.event_type == keyboard.KEY_DOWN:
                key_info = f"Key: {event.name}"
                
                # Add modifier information
                active_modifiers = [mod for mod, state in self.modifiers.items() if state]
                if active_modifiers:
                    key_info += f" | Modifiers: {', '.join(active_modifiers)}"
                
                # Log the keystroke
                self.log_keystroke(key_info)
                
                char = event.name
                print(f"EVENT CODE : {event.scan_code}")

                if char in {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'} and event.scan_code > 11:
                    char = 'k' + char
                if event.scan_code == 83:
                    char = 'k.'
                if event.scan_code == 86:  
                    char = 'c' + char
                
                # Process the key for HID transmission
                if len(event.name) == 1:
                    # Single character
                    success = self.process_character(char, self.modifiers)
                    self.logger.debug(f"Processed character '{char}': {'success' if success else 'failed'}")
                
                else:
                    # Special key (space, enter, function keys, etc.)
                    success = self.handle_special_key(event.name, self.modifiers)
                    self.logger.debug(f"Processed special key '{event.name}': {'success' if success else 'failed'}")
                
        except Exception as e:
            self.logger.error(f"Error processing key event: {e}")
    
    def start_monitoring(self):
        """Start monitoring keyboard input"""
        self.logger.info("Starting keyboard monitoring...")
        self.logger.info(f"Logging to: {self.log_file}")
        self.logger.info(f"HID device: {self.hid_device}")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            # Hook all keyboard events
            keyboard.hook(self.on_key_event)
            
            # Keep the program running
            keyboard.wait()
            
        except KeyboardInterrupt:
            self.logger.info("Stopping keyboard monitoring...")
        except Exception as e:
            self.logger.error(f"Error during monitoring: {e}")
        finally:
            # Cleanup
            if self.hid_fd is not None:
                os.close(self.hid_fd)
                self.logger.info("HID device closed")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'hid_fd') and self.hid_fd is not None:
            try:
                os.close(self.hid_fd)
            except:
                pass

def main():
    """Main function"""
    # Check if running as root
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root to access /dev/input and /dev/hidg0")
        print("Please run with: sudo python3 keyboard_hid_emulator.py")
        return 1
    
    # Check if HID gadget device exists
    hid_device = "/dev/hidg0"
    if not os.path.exists(hid_device):
        print(f"ERROR: HID gadget device {hid_device} not found")
        print("Please ensure USB gadget is properly configured on BeagleBone Black")
        print("Refer to BeagleBone documentation for USB gadget setup")
        return 1
    
    try:
        # Create and start the keyboard processor
        processor = AzertyKeyboardProcessor()
        processor.start_monitoring()
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())