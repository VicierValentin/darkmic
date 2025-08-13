#!/usr/bin/env python3

import sys
import time
import os
import threading
import queue

# Try to import keyboard library, handle if not available
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: 'keyboard' library not installed. Direct input capture disabled.")
    print("Install with: pip install keyboard")
    print("Note: May require root privileges on Linux.")

class HIDKeyboard:
    def __init__(self, device_path="/dev/hidg0"):
        self.device_path = device_path
        self.key_map = {
            'a': 4, 'b': 5, 'c': 6, 'd': 7, 'e': 8, 'f': 9, 'g': 10, 'h': 11,
            'i': 12, 'j': 13, 'k': 14, 'l': 15, 'm': 16, 'n': 17, 'o': 18,
            'p': 19, 'q': 20, 'r': 21, 's': 22, 't': 23, 'u': 24, 'v': 25,
            'w': 26, 'x': 27, 'y': 28, 'z': 29, ' ': 44, '\n': 40,
            '1': 30, '2': 31, '3': 32, '4': 33, '5': 34,
            '6': 35, '7': 36, '8': 37, '9': 38, '0': 39,
            # Special characters that require shift
            '!': (30, 0x02), '@': (0x1f, 0x02), '#': (32, 0x02), '$': (33, 0x02), '%': (34, 0x02),
            '^': (35, 0x02), '&': (36, 0x02), '*': (37, 0x02), '(': (38, 0x02), ')': (39, 0x02),
            '-': 45, '_': (45, 0x02), '=': 46, '+': (46, 0x02),
            '[': 47, '{': (47, 0x02), '[': 48, '}': (48, 0x02),
            '|': (0x64, 0x02), ';': 51, ':': (51, 0x02),
            "'": 52, '"': (52, 0x02), '`': 53, '~': (53, 0x02),
            ',': 54, '<': (54, 0x02), '.': 55, '>': (55, 0x02),
            '/': 56, '?': (56, 0x02), ']': 0x30,
        }
        
        # Extended character map for AltGr combinations (common European layouts)
        self.altgr_map = {
            # Common AltGr characters
            '€': (0x22, 0x40),    # 
            #'@': (20, 0x40),   # AltGr + Q = @
            '²': (31, 0x40),   # AltGr + 2 = ²
            '³': (32, 0x40),   # AltGr + 3 = ³
            '¼': (33, 0x40),   # AltGr + 4 = ¼
            '½': (34, 0x40),   # AltGr + 5 = ½
            '¾': (35, 0x40),   # AltGr + 6 = ¾
            '{': (36, 0x40),   # AltGr + 7 = {
            '[': (37, 0x40),   # AltGr + 8 = [
            #']': (38, 0x40),   # AltGr + 9 = ]
            '}': (39, 0x40),   # AltGr + 0 = }
            '\\': (0x25, 0x40),  # AltGr + - = \
            '|': (46, 0x40),   # AltGr + = = |
            '’': (0x27, 0x40),   # AltGr + 8 = ×
            '×': (0x2E, 0x40),   # AltGr + 8 = ×
            '¤': (0x21, 0x40),   # AltGr + 8 = ¤
            '¥': (0x2D, 0x40),   # AltGr + 9 = ¥
            '§': (40, 0x02),   # AltGr + 0 = §
            # Add more AltGr combinations as needed
        }
        
        self.special_keys = {
            'enter': 40, 'escape': 41, 'backspace': 42, 'tab': 43, 'space': 44,
            'caps_lock': 57, 'f1': 58, 'f2': 59, 'f3': 60, 'f4': 61, 'f5': 62,
            'f6': 63, 'f7': 64, 'f8': 65, 'f9': 66, 'f10': 67, 'f11': 68, 'f12': 69,
            'home': 74, 'page_up': 75, 'delete': 76, 'end': 77, 'page_down': 78,
            'right_arrow': 79, 'left_arrow': 80, 'down_arrow': 81, 'up_arrow': 82, 'left': 0x64, 'deux': 0x1F, 'etoile': 0x32,
        }
        
        # Modifier key constants
        self.modifiers = {
            'ctrl': 0x01,
            'shift': 0x02,
            'alt': 0x04,
            'gui': 0x08,    # Windows key / Cmd key
            'right_ctrl': 0x10,
            'right_shift': 0x20,
            'right_alt': 0x40,
            'right_gui': 0x80
        }

    def send_key(self, keycode, modifier=0):
        """Send a key press and release"""
        try:
            with open(self.device_path, 'wb') as hid_device:
                # Send key press (modifier, reserved, key1, key2, key3, key4, key5, key6)
                key_press = bytes([modifier, 0, keycode, 0, 0, 0, 0, 0])
                hid_device.write(key_press)
                hid_device.flush()
                
                # Small delay
                time.sleep(0.00000001)
                
                # Send key release (all zeros)
                key_release = bytes([0, 0, 0, 0, 0, 0, 0, 0])
                hid_device.write(key_release)
                hid_device.flush()
                
        except IOError as e:
            print(f"Error accessing HID device: {e}")
            return False
        return True

    def get_keycode(self, char):
        """Get keycode for a character, handling special characters with modifiers"""
        # Check AltGr combinations first
        if char in self.altgr_map:
            return self.altgr_map[char]
            
        # Check regular characters
        if char.lower() in self.key_map:
            keycode = self.key_map[char.lower()]
            
            # Handle uppercase letters (require shift)
            if char.isupper() and char.lower() in 'abcdefghijklmnopqrstuvwxyz':
                return (keycode, 0x02)  # Add shift modifier
            
            # Return keycode (could be tuple with modifier or just int)
            return keycode
        
        # Check if it's a special character in key_map
        if char in self.key_map:
            return self.key_map[char]
            
        return 0  # Unknown character

    def send_key_with_char(self, char):
        """Send a key for a specific character, handling modifiers automatically"""
        keycode_info = self.get_keycode(char)
        
        if keycode_info == 0:
            print(f"Unknown character: {char}")
            return False
            
        # Handle tuple (keycode, modifier) or simple keycode
        if isinstance(keycode_info, tuple):
            keycode, modifier = keycode_info
        else:
            keycode = keycode_info
            modifier = 0
            
        return self.send_key(keycode, modifier)

    def send_string(self, text):
        """Send a string as HID keyboard input"""
        for char in text:
            if not self.send_key_with_char(char):
                # If character sending failed, try to continue with others
                continue
            time.sleep(0.00000001)  # Delay between characters
        return True

    def send_special_key(self, key_name):
        """Send a special key"""
        keycode = self.special_keys.get(key_name.lower())
        if keycode:
            return self.send_key(keycode)
        else:
            print(f"Unknown special key: {key_name}")
            return False

    def send_char(self, char):
        """Send a single character"""
        return self.send_key_with_char(char)

    def capture_and_send_input(self, stop_event):
        """Capture keyboard input and send as HID output"""
        if not KEYBOARD_AVAILABLE:
            print("Keyboard library not available. Cannot capture direct input.")
            return
            
        print("Direct input mode active. Press Ctrl+Shift+Esc to stop.")
        print("All keyboard input will be forwarded to HID device.")
        
        try:
            def on_key_event(event):
                if stop_event.is_set():
                    return False
                    
                # Check for stop combination (Ctrl+Shift+Esc)
                if event.name == 'esc' and keyboard.is_pressed('ctrl') and keyboard.is_pressed('shift'):
                    print("\nStop combination detected. Exiting direct input mode...")
                    stop_event.set()
                    return False
                    
                # Only process key down events to avoid duplicates
                if event.event_type == keyboard.KEY_DOWN:
                    self.process_keyboard_event(event)
                    
            # Hook all keyboard events
            keyboard.hook(on_key_event)
            
            # Wait until stop event is set
            while not stop_event.is_set():
                time.sleep(0.1)
                
        except Exception as e:
            print(f"\nError setting up keyboard hook: {e}")
            if "dumpkeys" in str(e):
                print("\nThis error is related to missing 'kbd' package on Linux.")
                print("Try one of these solutions:")
                print("1. Install kbd package:")
                print("   sudo apt install kbd          # Ubuntu/Debian")
                print("   sudo yum install kbd           # CentOS/RHEL")
                print("   sudo pacman -S kbd             # Arch Linux")
                print("\n2. Or try running with sudo:")
                print("   sudo python3 hid_keyboard.py -direct")
                print("\n3. Or use alternative method with pynput:")
                print("   pip install pynput")
                print("   Then restart the script")
            else:
                print(f"Unexpected error: {e}")
                print("You may need to run with sudo privileges.")
        finally:
            # Unhook keyboard events
            try:
                keyboard.unhook_all()
            except:
                pass

    def capture_and_send_input_pynput(self, stop_event):
        """Alternative input capture using pynput library"""
        try:
            from pynput import keyboard as pynput_keyboard
        except ImportError:
            print("pynput library not available. Install with: pip install pynput")
            return
            
        print("Direct input mode active (using pynput). Press Ctrl+Shift+Esc to stop.")
        print("All keyboard input will be forwarded to HID device.")
        
        # Track modifier states
        self.modifier_states = {
            'ctrl': False,
            'shift': False,
            'alt': False,
            'altgr': False,  # Right Alt
            'cmd': False
        }
        
        def on_press(key):
            if stop_event.is_set():
                return False
                
            try:
                # Update modifier states
                if key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
                    self.modifier_states['ctrl'] = True
                elif key == pynput_keyboard.Key.shift_l or key == pynput_keyboard.Key.shift_r:
                    self.modifier_states['shift'] = True
                elif key == pynput_keyboard.Key.alt_l:
                    self.modifier_states['alt'] = True
                elif key == pynput_keyboard.Key.alt_r or key == pynput_keyboard.Key.alt_gr:
                    self.modifier_states['altgr'] = True  # AltGr is right alt
                elif key == pynput_keyboard.Key.cmd_l or key == pynput_keyboard.Key.cmd_r:
                    self.modifier_states['cmd'] = True
                
                # Check for stop combination (Ctrl+Shift+Esc)
                if (key == pynput_keyboard.Key.esc and 
                    self.modifier_states['ctrl'] and 
                    self.modifier_states['shift']):
                    print("\nStop combination detected. Exiting direct input mode...")
                    stop_event.set()
                    return False
                
                # Process the key
                self.process_pynput_key(key)
                
            except Exception as e:
                print(f"Error processing key: {e}")
        
        def on_release(key):
            if stop_event.is_set():
                return False
                
            # Update modifier states
            if key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
                self.modifier_states['ctrl'] = False
            elif key == pynput_keyboard.Key.shift_l or key == pynput_keyboard.Key.shift_r:
                self.modifier_states['shift'] = False
            elif key == pynput_keyboard.Key.alt_l:
                self.modifier_states['alt'] = False
            elif key == pynput_keyboard.Key.alt_r or key == pynput_keyboard.Key.alt_gr:
                self.modifier_states['altgr'] = False
            elif key == pynput_keyboard.Key.cmd_l or key == pynput_keyboard.Key.cmd_r:
                self.modifier_states['cmd'] = False
        
        # Start listener
        with pynput_keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            while not stop_event.is_set():
                time.sleep(0.1)
            listener.stop()

    def process_keyboard_event(self, event):
        """Process a keyboard event and send corresponding HID command"""
        key_name = event.name
        
        # Get current modifier states
        modifier = 0
        if keyboard.is_pressed('ctrl'):
            modifier |= self.modifiers['ctrl']
        if keyboard.is_pressed('shift'):
            modifier |= self.modifiers['shift']
        if keyboard.is_pressed('alt'):
            modifier |= self.modifiers['alt']
        if keyboard.is_pressed('cmd') or keyboard.is_pressed('windows'):
            modifier |= self.modifiers['gui']
            
        # Map keyboard library key names to our keycodes
        keycode = self.map_keyboard_key_to_code(key_name)
        
        if keycode != 0:
            success = self.send_key(keycode, modifier)
            if success:
                combo_str = self.format_key_combination(key_name, modifier)
                print(f"Sent: {combo_str}")
            else:
                print(f"Failed to send: {key_name}")

    def process_pynput_key(self, key):
        """Process a pynput key event"""
        # Handle character keys with automatic modifier detection
        if hasattr(key, 'char') and key.char:
            # Use the smart character handling that detects required modifiers
            success = self.send_key_with_char(key.char)
            if success:
                combo_str = f"'{key.char}'"
                print(f"Sent: {combo_str}")
        else:
            # Handle special keys
            keycode = self.map_pynput_key_to_code(key)
            if keycode != 0:
                # Calculate modifier byte for special keys
                modifier = 0
                if self.modifier_states['ctrl']:
                    modifier |= self.modifiers['ctrl']
                if self.modifier_states['shift']:
                    modifier |= self.modifiers['shift']
                if self.modifier_states['alt']:
                    modifier |= self.modifiers['alt']
                if self.modifier_states['altgr']:
                    modifier |= self.modifiers['right_alt']
                if self.modifier_states['cmd']:
                    modifier |= self.modifiers['gui']
                
                success = self.send_key(keycode, modifier)
                if success:
                    key_name = self.get_pynput_key_name(key)
                    combo_str = self.format_key_combination(key_name, modifier)
                    print(f"Sent: {combo_str}")

    def map_keyboard_key_to_code(self, key_name):
        """Map keyboard library key names to HID keycodes"""
        # Direct character mapping
        if len(key_name) == 1 and key_name.isalnum():
            keycode_info = self.get_keycode(key_name)
            if isinstance(keycode_info, tuple):
                return keycode_info[0]
            return keycode_info
            
        # Special key mapping
        key_mapping = {
            'space': 44,
            'enter': 40,
            'esc': 41,
            'escape': 41,
            'backspace': 42,
            'tab': 43,
            'caps lock': 57,
            'f1': 58, 'f2': 59, 'f3': 60, 'f4': 61, 'f5': 62, 'f6': 63,
            'f7': 64, 'f8': 65, 'f9': 66, 'f10': 67, 'f11': 68, 'f12': 69,
            'home': 74,
            'page up': 75,
            'delete': 76,
            'end': 77,
            'page down': 78,
            'right': 79,
            'left': 80,
            'down': 81,
            'up': 82,
            'leftarrow': 0x64,  # Left arrow
        }
        
        return key_mapping.get(key_name, 0)

    def map_pynput_key_to_code(self, key):
        """Map pynput key to HID keycode"""
        try:
            # Handle character keys
            if hasattr(key, 'char') and key.char:
                keycode_info = self.get_keycode(key.char)
                if isinstance(keycode_info, tuple):
                    return keycode_info[0]
                return keycode_info
            
            # Handle special keys
            key_mapping = {
                key.space: 44,
                key.enter: 40,
                key.esc: 41,
                key.backspace: 42,
                key.tab: 43,
                key.caps_lock: 57,
                key.f1: 58, key.f2: 59, key.f3: 60, key.f4: 61,
                key.f5: 62, key.f6: 63, key.f7: 64, key.f8: 65,
                key.f9: 66, key.f10: 67, key.f11: 68, key.f12: 69,
                key.home: 74, key.page_up: 75, key.delete: 76,
                key.end: 77, key.page_down: 78,
                key.right: 79, key.left: 80, key.down: 81, key.up: 82,
            }
            
            return key_mapping.get(key, 0)
            
        except Exception:
            return 0

    def get_pynput_key_name(self, key):
        """Get readable name for pynput key"""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char
            else:
                return key.name
        except:
            return str(key)

    def format_key_combination(self, key_name, modifier):
        """Format a key combination for display"""
        parts = []
        
        if modifier & self.modifiers['ctrl']:
            parts.append('ctrl')
        if modifier & self.modifiers['shift']:
            parts.append('shift')
        if modifier & self.modifiers['alt']:
            parts.append('alt')
        if modifier & self.modifiers['right_alt']:
            parts.append('altgr')
        if modifier & self.modifiers['gui']:
            parts.append('gui')
            
        parts.append(key_name)
        return '+'.join(parts)

    def send_combo(self, combo_string):
        """Send a key combination like 'ctrl+s', 'ctrl+shift+a', etc."""
        parts = combo_string.lower().split('+')
        
        if len(parts) < 2:
            print(f"Invalid combo format: {combo_string}")
            print("Use format like 'ctrl+s' or 'ctrl+shift+a'")
            return False
            
        # Calculate modifier byte
        modifier = 0
        keys = []
        
        for part in parts:
            part = part.strip()
            if part in self.modifiers:
                modifier |= self.modifiers[part]
            elif part == 'altgr':
                modifier |= self.modifiers['right_alt']
            else:
                # This should be the actual key
                if part in self.special_keys:
                    keys.append(self.special_keys[part])
                else:
                    keycode_info = self.get_keycode(part)
                    if isinstance(keycode_info, tuple):
                        keys.append(keycode_info[0])
                    elif keycode_info != 0:
                        keys.append(keycode_info)
                    else:
                        print(f"Unknown key in combo: {part}")
                        return False
        
        if not keys:
            print("No valid key found in combination")
            return False
            
        # Send the combination (use first key if multiple keys specified)
        return self.send_key(keys[0], modifier)

def print_help():
    """Print help information"""
    print("\n=== HID Keyboard Interactive Mode ===")
    print("Commands:")
    print("  text                    - Send text as keyboard input")
    print("  :key <special_key>      - Send special key (e.g., :key enter)")
    print("  :char <character>       - Send single character (e.g., :char a)")
    print("  :combo <combination>    - Send key combination (e.g., :combo ctrl+s)")
    if KEYBOARD_AVAILABLE:
        print("  :direct                 - Enter direct input mode (forward all keystrokes)")
    print("  :help                   - Show this help")
    print("  :quit or :exit          - Exit the program")
    print("\nSpecial keys available:")
    print("  enter, escape, backspace, tab, space, caps_lock")
    print("  f1-f12, home, end, page_up, page_down, delete")
    print("  up_arrow, down_arrow, left_arrow, right_arrow")
    print("\nModifier keys available:")
    print("  ctrl, shift, alt, altgr (right_alt), gui (Windows/Cmd key)")
    print("  right_ctrl, right_shift, right_alt, right_gui")
    print("\nSpecial Characters (automatic handling):")
    print("  Uppercase letters: A-Z (auto-adds shift)")
    print("  Symbols: !@#$%^&*()_+-={}[]|\\:;\"'<>,.?/")
    print("  AltGr characters: €@²³¼½¾ (language dependent)")
    print("\nExamples:")
    print("  Hello World!            # Automatically handles shift for uppercase and !")
    print("  :key enter              # Send Enter key")
    print("  :char €                 # Send Euro symbol (AltGr+E)")
    print("  :combo ctrl+s           # Send Ctrl+S")
    print("  :combo altgr+e          # Send AltGr+E (€)")
    print("  :combo ctrl+shift+a     # Send Ctrl+Shift+A")
    if KEYBOARD_AVAILABLE:
        print("  :direct                 # Forward all keyboard input (Ctrl+Shift+Esc to stop)")
    print("=" * 60)

def interactive_mode():
    """Run interactive mode"""
    hid_keyboard = HIDKeyboard()
    
    print("HID Keyboard Controller - Interactive Mode")
    print("Type ':help' for commands or ':quit' to exit")
    
    # Check if HID device exists
    if not os.path.exists(hid_keyboard.device_path):
        print(f"Warning: HID device {hid_keyboard.device_path} not found!")
        print("Make sure the USB gadget is properly configured.")
    
    while True:
        try:
            user_input = ""
            part = ""
            command = ""
            user_input = input("\nHID> ").strip()
            
            if not user_input:
                continue
                
            # Handle special commands
            if user_input.startswith(':'):
                parts = user_input[1:].split(' ', 1)
                command = parts[0].lower()
                
                if command in ['quit', 'exit']:
                    print("Goodbye!")
                    break
                elif command == 'help':
                    print_help()
                elif command == 'key':
                    if len(parts) < 2:
                        print("Usage: :key <special_key_name>")
                    else:
                        key_name = parts[1]
                        if hid_keyboard.send_special_key(key_name):
                            print(f"Sent special key: {key_name}")
                elif command == 'direct':
                    if not KEYBOARD_AVAILABLE:
                        print("Direct input mode requires 'keyboard' library.")
                        print("Install with: pip install keyboard")
                        print("Note: May require root privileges on Linux.")
                    else:
                        stop_event = threading.Event()
                        try:
                            # Try keyboard library first
                            hid_keyboard.capture_and_send_input(stop_event)
                        except Exception as e:
                            if "dumpkeys" in str(e):
                                print(f"Keyboard library failed: {e}")
                                print("Trying alternative pynput method...")
                                stop_event.clear()  # Reset the event
                                try:
                                    hid_keyboard.capture_and_send_input_pynput(stop_event)
                                except Exception as e2:
                                    print(f"Pynput method also failed: {e2}")
                                    print("Install pynput with: pip install pynput")
                            else:
                                print(f"Error in direct input mode: {e}")
                                print("You may need to run with sudo on Linux.")
                elif command == 'combo':
                    if len(parts) < 2:
                        print("Usage: :combo <key_combination>")
                        print("Examples: :combo ctrl+s, :combo ctrl+shift+a")
                    else:
                        combo = parts[1]
                        if hid_keyboard.send_combo(combo):
                            print(f"Sent key combination: {combo}")
                elif command == 'char':
                    if len(parts) < 2:
                        print("Usage: :char <character>")
                    else:
                        char = parts[1][0] if parts[1] else ''
                        if hid_keyboard.send_char(char):
                            print(f"Sent character: {char}")
                else:
                    print(f"Unknown command: {command}")
                    print("Type ':help' for available commands")
            else:
                # Send as regular text
                if hid_keyboard.send_string(user_input):
                    print(f"Sent text: '{user_input}'")
                    
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break

def main():
    """Main function"""
    if len(sys.argv) == 1:
        # No arguments - run interactive mode
        interactive_mode()
    else:
        # Command line mode (similar to original bash script)
        hid_keyboard = HIDKeyboard()
        
        if sys.argv[1] in ['-s', '--string']:
            if len(sys.argv) < 3:
                print("Usage: python3 hid_keyboard.py -s \"text to send\"")
                sys.exit(1)
            hid_keyboard.send_string(sys.argv[2])
            
        elif sys.argv[1] in ['-k', '--key']:
            if len(sys.argv) < 3:
                print("Usage: python3 hid_keyboard.py -k special_key_name")
                sys.exit(1)
            hid_keyboard.send_special_key(sys.argv[2])
            
        elif sys.argv[1] in ['-direct', '--direct']:
            if not KEYBOARD_AVAILABLE:
                print("Direct input mode requires 'keyboard' library.")
                print("Install with: pip install keyboard")
                sys.exit(1)
            stop_event = threading.Event()
            try:
                # Try keyboard library first
                hid_keyboard.capture_and_send_input(stop_event)
            except Exception as e:
                if "dumpkeys" in str(e):
                    print(f"Keyboard library failed: {e}")
                    print("Trying alternative pynput method...")
                    stop_event.clear()  # Reset the event
                    try:
                        hid_keyboard.capture_and_send_input_pynput(stop_event)
                    except Exception as e2:
                        print(f"Pynput method also failed: {e2}")
                        print("Install pynput with: pip install pynput")
                        sys.exit(1)
                else:
                    print(f"Error in direct input mode: {e}")
                    print("You may need to run with sudo on Linux.")
                    sys.exit(1)
            
        elif sys.argv[1] in ['-combo', '--combo']:
            if len(sys.argv) < 3:
                print("Usage: python3 hid_keyboard.py -combo key_combination")
                print("Examples: python3 hid_keyboard.py -combo ctrl+s")
                sys.exit(1)
            hid_keyboard.send_combo(sys.argv[2])
            
        elif sys.argv[1] in ['-c', '--char']:
            if len(sys.argv) < 3:
                print("Usage: python3 hid_keyboard.py -c character")
                sys.exit(1)
            hid_keyboard.send_char(sys.argv[2])
            
        elif sys.argv[1] in ['-h', '--help']:
            print("USB HID Keyboard Script (Python)")
            print("Usage:")
            print("  python3 hid_keyboard.py                       # Interactive mode")
            print("  python3 hid_keyboard.py -s \"text\"             # Send a string")
            print("  python3 hid_keyboard.py -k special_key         # Send a special key")
            print("  python3 hid_keyboard.py -c character           # Send a single character")
            print("  python3 hid_keyboard.py -combo key_combination # Send key combination")
            if KEYBOARD_AVAILABLE:
                print("  python3 hid_keyboard.py -direct               # Direct input forwarding mode")
            print("\nExamples:")
            print("  python3 hid_keyboard.py -s \"hello world\"       # Send text")
            print("  python3 hid_keyboard.py -k enter                # Send Enter key")
            print("  python3 hid_keyboard.py -k f1                   # Send F1 key")
            print("  python3 hid_keyboard.py -c a                    # Send character 'a'")
            print("  python3 hid_keyboard.py -combo ctrl+s           # Send Ctrl+S")
            print("  python3 hid_keyboard.py -combo ctrl+shift+a     # Send Ctrl+Shift+A")
            print("  python3 hid_keyboard.py -combo alt+f4           # Send Alt+F4")
            if KEYBOARD_AVAILABLE:
                print("  python3 hid_keyboard.py -direct               # Forward all keyboard input")
            
        else:
            print("Unknown option. Use -h or --help for usage information.")
            sys.exit(1)

if __name__ == "__main__":
    main()