#!/usr/bin/env python3
"""
Keyboard Logger using evtest
Reads keyboard input and writes to a text file,
with full AZERTY layout mapping.
"""

import subprocess
import sys
import os
import signal
import threading
from datetime import datetime

class KeyboardLogger:
    def __init__(self, output_file="keyboard_log.txt", device_path=None):
        self.output_file = output_file
        self.device_path = device_path
        self.process = None
        self.running = False
        self.log_file = None

        # AZERTY key codes → characters (no Shift)
        self.key_map = {
            # Numbers row
            'KEY_1': '&',   'KEY_2': 'é',  'KEY_3': '"',   'KEY_4': "'",
            'KEY_5': '(',   'KEY_6': '-',  'KEY_7': 'è',   'KEY_8': '_',
            'KEY_9': 'ç',   'KEY_0': 'à',  'KEY_MINUS': ')','KEY_EQUAL': '=',

            # QWERTY’s Q→A row
            'KEY_A': 'q',   'KEY_Z': 'w',  'KEY_E': 'e',  'KEY_R': 'r',
            'KEY_T': 't',   'KEY_Y': 'y',  'KEY_U': 'u',  'KEY_I': 'i',
            'KEY_O': 'o',   'KEY_P': 'p',  'KEY_LEFTBRACE': '^','KEY_RIGHTBRACE': '$',

            # QWERTY’s A→Q row
            'KEY_Q': 'a',   'KEY_S': 's',  'KEY_D': 'd',  'KEY_F': 'f',
            'KEY_G': 'g',   'KEY_H': 'h',  'KEY_J': 'j',  'KEY_K': 'k',
            'KEY_L': 'l',   'KEY_SEMICOLON': 'm', 'KEY_APOSTROPHE': 'ù',
            'KEY_BACKSLASH': '*',

            # QWERTY’s Z→W row
            'KEY_W': 'z',   'KEY_X': 'x',  'KEY_C': 'c',  'KEY_V': 'v',
            'KEY_B': 'b',   'KEY_N': 'n',  'KEY_COMMA': ';','KEY_DOT': ':',
            'KEY_SLASH': '!',

            # Whitespace & controls
            'KEY_SPACE': ' ',  'KEY_ENTER': '\n', 'KEY_TAB': '\t',
            'KEY_BACKSPACE': '[BACKSPACE]', 'KEY_DELETE': '[DELETE]',

            # Function keys
            'KEY_F1': '[F1]',   'KEY_F2': '[F2]',   'KEY_F3': '[F3]',
            'KEY_F4': '[F4]',   'KEY_F5': '[F5]',   'KEY_F6': '[F6]',
            'KEY_F7': '[F7]',   'KEY_F8': '[F8]',   'KEY_F9': '[F9]',
            'KEY_F10': '[F10]', 'KEY_F11': '[F11]', 'KEY_F12': '[F12]',

            # Arrow keys
            'KEY_UP': '[UP]',     'KEY_DOWN': '[DOWN]',
            'KEY_LEFT': '[LEFT]', 'KEY_RIGHT': '[RIGHT]',
            'KEY_HOME': '[HOME]', 'KEY_END': '[END]',
            'KEY_PAGEUP': '[PAGEUP]', 'KEY_PAGEDOWN': '[PAGEDOWN]',

            # Numpad & NumLock
            'KEY_NUMLOCK': '[NUMLOCK]',
            'KEY_KP0': '[NUM0]', 'KEY_KP1': '[NUM1]', 'KEY_KP2': '[NUM2]',
            'KEY_KP3': '[NUM3]', 'KEY_KP4': '[NUM4]', 'KEY_KP5': '[NUM5]',
            'KEY_KP6': '[NUM6]', 'KEY_KP7': '[NUM7]', 'KEY_KP8': '[NUM8]',
            'KEY_KP9': '[NUM9]', 'KEY_KPDOT': '[NUM.]', 'KEY_KPPLUS': '[NUM+]',
            'KEY_KPMINUS': '[NUM-]','KEY_KPASTERISK': '[NUM*]','KEY_KPSLASH': '[NUM/]',
            'KEY_KPENTER': '[NUM_ENTER]', 'KEY_KPEQUAL': '[NUM=]',
            'KEY_KPCOMMA': '[NUM,]','KEY_KPLEFTPAREN': '[NUM(]','KEY_KPRIGHTPAREN': '[NUM)]',
        }

        # AZERTY Shift modifications
        self.shift_map = {
            '&': '1',   'é': '2',   '"': '3',   "'": '4',   '(': '5',
            '-': '6',   'è': '7',   '_': '8',   'ç': '9',   'à': '0',
            ')': '°',   '=': '+',   '^': '¨',   '$': '£',
            ';': '.',   ':': '/',   '!': '§',   ',': '?'
        }

        # Modifier states
        self.shift_pressed = False
        self.caps_lock = False
        self.num_lock = True  # Numpad starts NumLock ON

    def find_keyboard_device(self):
        try:
            result = subprocess.run(['ls', '/dev/input/'], capture_output=True, text=True)
            devices = result.stdout.strip().split('\n')
            event_devices = [d for d in devices if d.startswith('event')]

            for device in event_devices:
                path = f'/dev/input/{device}'
                try:
                    probe = subprocess.run(['evtest', path], input='\n',
                                           capture_output=True, text=True, timeout=2)
                    if 'EV_KEY' in probe.stdout and 'KEY_A' in probe.stdout:
                        print(f"Found keyboard device: {path}")
                        return path
                except:
                    continue
            return None
        except Exception as e:
            print(f"Error finding keyboard device: {e}")
            return None

    def list_input_devices(self):
        try:
            print("Available input devices:")
            print(subprocess.run(['ls', '-la', '/dev/input/'],
                                 capture_output=True, text=True).stdout)
            evs = subprocess.run(['ls', '/dev/input/event*'],
                                 shell=True, capture_output=True, text=True)
            if evs.returncode == 0:
                print("\nEvent devices:")
                for d in evs.stdout.strip().split('\n'):
                    print(f"  {d}")
        except Exception as e:
            print(f"Error listing devices: {e}")

    def start_logging(self):
        if self.running:
            print("Logger is already running!")
            return

        if not self.device_path:
            self.device_path = self.find_keyboard_device()
        if not self.device_path:
            print("No keyboard device found!")
            self.list_input_devices()
            return
        if not os.path.exists(self.device_path):
            print(f"Device {self.device_path} does not exist!")
            return

        try:
            subprocess.run(['evtest', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("evtest not installed. Install with: sudo apt-get install evtest")
            return

        try:
            self.log_file = open(self.output_file, 'a', encoding='utf-8')
            self.log_file.write(f"\n")
            self.log_file.flush()

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

            t = threading.Thread(target=self.read_events)
            t.daemon = True
            t.start()

            try:
                self.process.wait()
            except KeyboardInterrupt:
                self.stop_logging()

        except Exception as e:
            print(f"Error starting logger: {e}")
            self.stop_logging()

    def read_events(self):
        try:
            while self.running and self.process:
                line = self.process.stdout.readline()
                if not line:
                    break
                self.parse_event_line(line.strip())
        except Exception as e:
            print(f"Error reading events: {e}")

    def parse_event_line(self, line):
        try:
            if 'EV_KEY' in line:
                parts = line.split('(')
                if len(parts) >= 3:
                    key_name = parts[2].split(')')[0]
                    if 'value 1' in line:
                        self.handle_key_press(key_name)
                    elif 'value 0' in line:
                        self.handle_key_release(key_name)
        except Exception as e:
            print(f"Error parsing line: {e}")

    def handle_key_press(self, key):
        try:
            # Modifier presses
            if key in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                self.shift_pressed = True
                self.log_file.write('[SHIFT_PRESS]')
                self.log_file.flush()
                print('[SHIFT_PRESS]', end='', flush=True)
                return
            if key == 'KEY_CAPSLOCK':
                self.caps_lock = not self.caps_lock
                return
            if key == 'KEY_NUMLOCK':
                self.num_lock = not self.num_lock
                state = "ON" if self.num_lock else "OFF"
                self.log_file.write(f'[NUMLOCK_{state}]')
                self.log_file.flush()
                print(f'[NUMLOCK_{state}]', end='', flush=True)
                return

            # Numpad handling
            if key.startswith('KEY_KP') and key not in (
                'KEY_KPENTER','KEY_KPPLUS','KEY_KPMINUS',
                'KEY_KPASTERISK','KEY_KPSLASH'
            ):
                char = self.handle_numpad_key(key)
            else:
                char = self.key_map.get(key, f'[{key}]')
                # Alpha: apply shift/caps
                if char.isalpha():
                    if self.shift_pressed ^ self.caps_lock:
                        char = char.upper()
                # Symbols
                elif self.shift_pressed and char in self.shift_map:
                    char = self.shift_map[char]

            self.log_file.write(char)
            self.log_file.flush()
            print(char, end='', flush=True)

        except Exception as e:
            print(f"Error handling key press: {e}")

    def handle_numpad_key(self, key):
        if self.num_lock:
            nums = {
                'KEY_KP0': '0','KEY_KP1': '1','KEY_KP2': '2',
                'KEY_KP3': '3','KEY_KP4': '4','KEY_KP5': '5',
                'KEY_KP6': '6','KEY_KP7': '7','KEY_KP8': '8',
                'KEY_KP9': '9','KEY_KPDOT': '.'
            }
            return nums.get(key, self.key_map.get(key, f'[{key}]'))
        else:
            nav = {
                'KEY_KP0': '[INS]','KEY_KP1': '[END]','KEY_KP2': '[DOWN]',
                'KEY_KP3': '[PGDN]','KEY_KP4': '[LEFT]','KEY_KP5': '[NUM5]',
                'KEY_KP6': '[RIGHT]','KEY_KP7': '[HOME]','KEY_KP8': '[UP]',
                'KEY_KP9': '[PGUP]','KEY_KPDOT': '[DEL]'
            }
            return nav.get(key, self.key_map.get(key, f'[{key}]'))

    def handle_key_release(self, key):
        try:
            if key in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                self.shift_pressed = False
                self.log_file.write('[SHIFT_RELEASE]')
                self.log_file.flush()
                print('[SHIFT_RELEASE]', end='', flush=True)
            elif key in ['KEY_LEFTCTRL', 'KEY_RIGHTCTRL']:
                self.log_file.write('[CTRL_RELEASE]')
                self.log_file.flush()
                print('[CTRL_RELEASE]', end='', flush=True)
            elif key in ['KEY_LEFTALT', 'KEY_RIGHTALT']:
                self.log_file.write('[ALT_RELEASE]')
                self.log_file.flush()
                print('[ALT_RELEASE]', end='', flush=True)
            elif key == 'KEY_NUMLOCK':
                self.log_file.write('[NUMLOCK_RELEASE]')
                self.log_file.flush()
                print('[NUMLOCK_RELEASE]', end='', flush=True)
        except Exception as e:
            print(f"Error handling key release: {e}")

    def stop_logging(self):
        print("\nStopping keyboard logger...")
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.log_file:
            self.log_file.write("\n")
            self.log_file.close()
        print(f"Log saved to: {self.output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Keyboard Logger using evtest (AZERTY)')
    parser.add_argument('-d', '--device', help='Input device path (e.g., /dev/input/event0)')
    parser.add_argument('-o', '--output', default='keyboard_log.txt', help='Output file name')
    parser.add_argument('-l', '--list', action='store_true', help='List available input devices')
    args = parser.parse_args()

    if args.list:
        k = KeyboardLogger()
        k.list_input_devices()
        return

    if os.geteuid() != 0:
        print("Warning: This script may need root privileges to access input devices.")
        print("Try: sudo python3 keyboard_logger.py")

    logger = KeyboardLogger(output_file=args.output, device_path=args.device)

    def sig_handler(signum, frame):
        logger.stop_logging()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        logger.start_logging()
    except KeyboardInterrupt:
        logger.stop_logging()


if __name__ == "__main__":
    main()