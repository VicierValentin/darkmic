#!/usr/bin/env python3
import time
import struct

# HID device file
HID_DEVICE = "/dev/hidg0"

# USB HID Keycodes (simplified mapping)
KEY_CODES = {
    'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07, 'e': 0x08,
    'f': 0x09, 'g': 0x0a, 'h': 0x0b, 'i': 0x0c, 'j': 0x0d,
    'k': 0x0e, 'l': 0x0f, 'm': 0x10, 'n': 0x11, 'o': 0x12,
    'p': 0x13, 'q': 0x14, 'r': 0x15, 's': 0x16, 't': 0x17,
    'u': 0x18, 'v': 0x19, 'w': 0x1a, 'x': 0x1b, 'y': 0x1c,
    'z': 0x1d, ' ': 0x2c, '\n': 0x28
}

def send_key(key_code, modifier=0):
    """Send a single key press"""
    # HID report: [modifier, reserved, key1, key2, key3, key4, key5, key6]
    report = struct.pack('8B', modifier, 0, key_code, 0, 0, 0, 0, 0)
    
    with open(HID_DEVICE, 'wb') as f:
        # Key press
        f.write(report)
        f.flush()
        time.sleep(0.01)
        
        # Key release
        release_report = struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)
        f.write(release_report)
        f.flush()

def send_string(text):
    """Send a string as keyboard input"""
    for char in text.lower():
        if char in KEY_CODES:
            send_key(KEY_CODES[char])
            time.sleep(0.05)  # Small delay between characters

# Example usage
if __name__ == "__main__":
    try:
        send_string("hello world\n")
        print("Keyboard data sent successfully!")
    except Exception as e:
        print(f"Error: {e}")