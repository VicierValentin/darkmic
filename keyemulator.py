#!/usr/bin/env python3
import argparse
import re
import sys
import time

# USB HID usage IDs for common keys
UNSHIFTED = {
    'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07,
    'e': 0x08, 'f': 0x09, 'g': 0x0A, 'h': 0x0B,
    'i': 0x0C, 'j': 0x0D, 'k': 0x0E, 'l': 0x0F,
    'm': 0x10, 'n': 0x11, 'o': 0x12, 'p': 0x13,
    'q': 0x14, 'r': 0x15, 's': 0x16, 't': 0x17,
    'u': 0x18, 'v': 0x19, 'w': 0x1A, 'x': 0x1B,
    'y': 0x1C, 'z': 0x1D,
    '1': 0x1E, '2': 0x1F, '3': 0x20, '4': 0x21,
    '5': 0x22, '6': 0x23, '7': 0x24, '8': 0x25,
    '9': 0x26, '0': 0x27,
    '\n': 0x28,   # ENTER
    '\x1b': 0x29,# ESC
    '\b': 0x2A,  # BACKSPACE
    '\t': 0x2B,  # TAB
    ' ':  0x2C,  # SPACE
    '-':  0x2D, '=': 0x2E, '[': 0x2F, ']': 0x30,
    '\\': 0x31, ';': 0x33, "'": 0x34, '`': 0x35,
    ',':  0x36, '.': 0x37, '/': 0x38
}

# Characters that require Shift + unshifted-key
SHIFTED = {
    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
    '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
    '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\',
    ':': ';', '"': "'", '~': '`', '<': ',', '>': '.', '?': '/'
}

# Bracketed tokens from the log file
SPECIAL = {
    '[ENTER]':  (0x00, 0x28),
    '[ESC]':    (0x00, 0x29),
    '[BACKSPACE]': (0x00, 0x2A),
    '[TAB]':    (0x00, 0x2B),
    '[DELETE]': (0x00, 0x4C),
    # Extend as needed...
}

def parse_log(path):
    """
    Yield tokens: either bracketed special keys or single characters.
    """
    data = open(path, 'r', encoding='utf-8').read()
    # Regex splits into '[TOKEN]' or any single character
    for tok in re.findall(r'\[[^\]]+\]|.', data):
        # skip shift‐press/release or numlock entries
        if tok in ('[SHIFT_PRESS]', '[SHIFT_RELEASE]',
                   '[NUMLOCK_ON]', '[NUMLOCK_OFF]', '[NUMLOCK_RELEASE]'):
            continue
        yield tok

def make_report(modifier, usage):
    """
    Build an 8-byte HID report.
    """
    return bytes([modifier, 0x00,
                  usage, 0x00, 0x00, 0x00, 0x00, 0x00])

def send_key(fd, modifier, usage, delay):
    """
    Press and release one key.
    """
    # key down
    fd.write(make_report(modifier, usage))
    fd.flush()
    time.sleep(delay)
    # key up
    fd.write(make_report(0x00, 0x00))
    fd.flush()
    time.sleep(delay)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--log', required=True, help='Path to keyboard_log.txt')
    p.add_argument('--device', default='/dev/hidg0', help='HID gadget device')
    p.add_argument('--delay', type=float, default=0.02, help='Delay between events')
    args = p.parse_args()

    try:
        fd = open(args.device, 'wb')
    except PermissionError:
        sys.exit(f"Error: cannot open {args.device}. Try sudo.")

    for tok in parse_log(args.log):
        # Special bracketed token?
        if tok in SPECIAL:
            mod, usage = SPECIAL[tok]
        # Single char
        elif len(tok) == 1:
            c = tok
            # Shifted symbol?
            if c in SHIFTED:
                base = SHIFTED[c]
                mod = 0x02  # left shift
                usage = UNSHIFTED[base]
            # Uppercase letter
            elif 'A' <= c <= 'Z':
                mod = 0x02
                usage = UNSHIFTED[c.lower()]
            # Lowercase or unshifted symbol
            elif c in UNSHIFTED:
                mod = 0x00
                usage = UNSHIFTED[c]
            else:
                # unrecognized char – skip
                continue
        else:
            # skip unknown multi-char token
            continue

        send_key(fd, mod, usage, args.delay)

    fd.close()

if __name__ == '__main__':
    main()
