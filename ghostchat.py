#!/usr/bin/env python3

import sys
import time
import os

class HIDKeyboard:
    def __init__(self, device_path="/dev/hidg0"):
        self.device_path = device_path
        self.key_map = {
            'a': 4, 'b': 5, 'c': 6, 'd': 7, 'e': 8, 'f': 9, 'g': 10, 'h': 11,
            'i': 12, 'j': 13, 'k': 14, 'l': 15, 'm': 16, 'n': 17, 'o': 18,
            'p': 19, 'q': 20, 'r': 21, 's': 22, 't': 23, 'u': 24, 'v': 25,
            'w': 26, 'x': 27, 'y': 28, 'z': 29, ' ': 44, '\n': 40,
            '1': 30, '2': 31, '3': 32, '4': 33, '5': 34,
            '6': 35, '7': 36, '8': 37, '9': 38, '0': 39
        }
        
        self.special_keys = {
            'enter': 40, 'escape': 41, 'backspace': 42, 'tab': 43, 'space': 44,
            'caps_lock': 57, 'f1': 58, 'f2': 59, 'f3': 60, 'f4': 61, 'f5': 62,
            'f6': 63, 'f7': 64, 'f8': 65, 'f9': 66, 'f10': 67, 'f11': 68, 'f12': 69,
            'home': 74, 'page_up': 75, 'delete': 76, 'end': 77, 'page_down': 78,
            'right_arrow': 79, 'left_arrow': 80, 'down_arrow': 81, 'up_arrow': 82
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
                time.sleep(0.01)
                
                # Send key release (all zeros)
                key_release = bytes([0, 0, 0, 0, 0, 0, 0, 0])
                hid_device.write(key_release)
                hid_device.flush()
                
        except IOError as e:
            print(f"Error accessing HID device: {e}")
            return False
        return True

    def get_keycode(self, char):
        """Get keycode for a character"""
        return self.key_map.get(char.lower(), 0)

    def send_string(self, text):
        """Send a string as HID keyboard input"""
        for char in text:
            keycode = self.get_keycode(char)
            if keycode != 0:
                if not self.send_key(keycode):
                    return False
                time.sleep(0.05)  # Delay between characters
        return True

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
            else:
                # This should be the actual key
                if part in self.special_keys:
                    keys.append(self.special_keys[part])
                else:
                    keycode = self.get_keycode(part)
                    if keycode != 0:
                        keys.append(keycode)
                    else:
                        print(f"Unknown key in combo: {part}")
                        return False
        
        if not keys:
            print("No valid key found in combination")
            return False
            
        # Send the combination (use first key if multiple keys specified)
        return self.send_key(keys[0], modifier)

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
        keycode = self.get_keycode(char)
        if keycode != 0:
            return self.send_key(keycode)
        else:
            print(f"Unknown character: {char}")
            return False

def print_help():
    """Print help information"""
    print("\n=== HID Keyboard Interactive Mode ===")
    print("Commands:")
    print("  text                    - Send text as keyboard input")
    print("  :key <special_key>      - Send special key (e.g., :key enter)")
    print("  :char <character>       - Send single character (e.g., :char a)")
    print("  :combo <combination>    - Send key combination (e.g., :combo ctrl+s)")
    print("  :help                   - Show this help")
    print("  :quit or :exit          - Exit the program")
    print("\nSpecial keys available:")
    print("  enter, escape, backspace, tab, space, caps_lock")
    print("  f1-f12, home, end, page_up, page_down, delete")
    print("  up_arrow, down_arrow, left_arrow, right_arrow")
    print("\nModifier keys available:")
    print("  ctrl, shift, alt, gui (Windows/Cmd key)")
    print("  right_ctrl, right_shift, right_alt, right_gui")
    print("\nExamples:")
    print("  hello world             # Send 'hello world' as text")
    print("  :key enter              # Send Enter key")
    print("  :key f1                 # Send F1 key")
    print("  :char a                 # Send character 'a'")
    print("  :combo ctrl+s           # Send Ctrl+S")
    print("  :combo ctrl+shift+a     # Send Ctrl+Shift+A")
    print("  :combo alt+f4           # Send Alt+F4")
    print("  :combo ctrl+c           # Send Ctrl+C (copy)")
    print("  :combo ctrl+v           # Send Ctrl+V (paste)")
    print("=" * 50)

def interactive_mode():
    """Run interactive mode"""
    keyboard = HIDKeyboard()
    
    print("HID Keyboard Controller - Interactive Mode")
    print("Type ':help' for commands or ':quit' to exit")
    
    # Check if HID device exists
    if not os.path.exists(keyboard.device_path):
        print(f"Warning: HID device {keyboard.device_path} not found!")
        print("Make sure the USB gadget is properly configured.")
    
    while True:
        try:
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
                        if keyboard.send_special_key(key_name):
                            print(f"Sent special key: {key_name}")
                elif command == 'combo':
                    if len(parts) < 2:
                        print("Usage: :combo <key_combination>")
                        print("Examples: :combo ctrl+s, :combo ctrl+shift+a")
                    else:
                        combo = parts[1]
                        if keyboard.send_combo(combo):
                            print(f"Sent key combination: {combo}")
                elif command == 'char':
                    if len(parts) < 2:
                        print("Usage: :char <character>")
                    else:
                        char = parts[1][0] if parts[1] else ''
                        if keyboard.send_char(char):
                            print(f"Sent character: {char}")
                else:
                    print(f"Unknown command: {command}")
                    print("Type ':help' for available commands")
            else:
                # Send as regular text
                if keyboard.send_string(user_input):
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
        keyboard = HIDKeyboard()
        
        if sys.argv[1] in ['-s', '--string']:
            if len(sys.argv) < 3:
                print("Usage: python3 hid_keyboard.py -s \"text to send\"")
                sys.exit(1)
            keyboard.send_string(sys.argv[2])
            
        elif sys.argv[1] in ['-k', '--key']:
            if len(sys.argv) < 3:
                print("Usage: python3 hid_keyboard.py -k special_key_name")
                sys.exit(1)
            keyboard.send_special_key(sys.argv[2])
            
        elif sys.argv[1] in ['-combo', '--combo']:
            if len(sys.argv) < 3:
                print("Usage: python3 hid_keyboard.py -combo key_combination")
                print("Examples: python3 hid_keyboard.py -combo ctrl+s")
                sys.exit(1)
            keyboard.send_combo(sys.argv[2])
            
        elif sys.argv[1] in ['-c', '--char']:
            if len(sys.argv) < 3:
                print("Usage: python3 hid_keyboard.py -c character")
                sys.exit(1)
            keyboard.send_char(sys.argv[2])
            
        elif sys.argv[1] in ['-h', '--help']:
            print("USB HID Keyboard Script (Python)")
            print("Usage:")
            print("  python3 hid_keyboard.py                       # Interactive mode")
            print("  python3 hid_keyboard.py -s \"text\"             # Send a string")
            print("  python3 hid_keyboard.py -k special_key         # Send a special key")
            print("  python3 hid_keyboard.py -c character           # Send a single character")
            print("  python3 hid_keyboard.py -combo key_combination # Send key combination")
            print("\nExamples:")
            print("  python3 hid_keyboard.py -s \"hello world\"       # Send text")
            print("  python3 hid_keyboard.py -k enter                # Send Enter key")
            print("  python3 hid_keyboard.py -k f1                   # Send F1 key")
            print("  python3 hid_keyboard.py -c a                    # Send character 'a'")
            print("  python3 hid_keyboard.py -combo ctrl+s           # Send Ctrl+S")
            print("  python3 hid_keyboard.py -combo ctrl+shift+a     # Send Ctrl+Shift+A")
            print("  python3 hid_keyboard.py -combo alt+f4           # Send Alt+F4")
            
        else:
            print("Unknown option. Use -h or --help for usage information.")
            sys.exit(1)

if __name__ == "__main__":
    main()