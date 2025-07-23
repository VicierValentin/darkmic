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
    '\n': 0x28,    # ENTER
    '\x1b': 0x29, # ESC
    '\b':  0x2A,  # BACKSPACE
    '\t':  0x2B,  # TAB
    ' ':   0x2C,  # SPACE
    '-':   0x2D, '=': 0x2E, '[': 0x2F, ']': 0x30,
    '\\':  0x31, ';': 0x33, "'": 0x34, '`': 0x35,
    ',':   0x36, '.': 0x37, '/': 0x38, 'É': 0x1F,
    'À': 0x27, 'Ç': 0x26, 'È': 0x24
}

# Characters requiring Shift + base key
SHIFTED = {
    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
    '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
    '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\',
    ':': ';', '"': "'", '~': '`', '<': ',', '>': '.', '?': '/'
}

# Bracketed tokens from the log (extend as needed)
SPECIAL = {
    '[ESC]':        (0x00, 0x29),
    '[BACKSPACE]':  (0x00, 0x2A),
    '[DELETE]':     (0x00, 0x4C),
    '[TAB]':        (0x00, 0x2B),
    '[UP]':         (0x00, 0x52),
    '[DOWN]':       (0x00, 0x51),
    '[LEFT]':       (0x00, 0x50),
    '[RIGHT]':      (0x00, 0x4F),
    '[HOME]':       (0x00, 0x4A),
    '[END]':        (0x00, 0x4D),
    '[PAGEUP]':     (0x00, 0x4B),
    '[PAGEDOWN]':   (0x00, 0x4E),
    '[F1]':         (0x00, 0x3A),
    '[F2]':         (0x00, 0x3B),
    '[F3]':         (0x00, 0x3C),
    '[F4]':         (0x00, 0x3D),
    '[F5]':         (0x00, 0x3E),
    '[F6]':         (0x00, 0x3F),
    '[F7]':         (0x00, 0x40),
    '[F8]':         (0x00, 0x41),
    '[F9]':         (0x00, 0x42),
    '[F10]':        (0x00, 0x43),
    '[F11]':        (0x00, 0x44),
    '[[]':          (0x00, 0x2F),
    '[F12]':        (0x00, 0x45),
}

# Tokens to ignore
IGNORED = {
    '[SHIFT_PRESS]', '[SHIFT_RELEASE]',
    '[CTRL_PRESS]', '[CTRL_RELEASE]',
    '[ALT_PRESS]',   '[ALT_RELEASE]',
    '[ALTGR_PRESS]', '[ALTGR_RELEASE]',
    '[NUMLOCK_ON]',  '[NUMLOCK_OFF]', '[NUMLOCK_RELEASE]'
}

def follow_tokens(fd):
    """
    Generator yielding one token at a time from fd.
    Tokens are either '[SOMETHING]' or a single character.
    Blocks and waits for new data indefinitely.
    """
    fd.seek(0, 2)  # go to file end
    buffer = ''
    while True:
        ch = fd.read(1)
        if not ch:
            time.sleep(0.1)
            continue

        if ch == '[':
            token = '['
            while True:
                c2 = fd.read(1)
                if not c2:
                    time.sleep(0.1)
                    continue
                token += c2
                if c2 == ']':
                    break
            if token not in IGNORED:
                yield token
        else:
            yield ch

def make_report(modifier, usage):
    """Build an 8-byte HID report."""
    return bytes([modifier, 0x00,
                  usage, 0x00, 0x00, 0x00, 0x00, 0x00])

def send_key(fd, mod, usage, delay):
    """Send key down + key up with a small delay."""
    fd.write(make_report(mod, usage))
    fd.flush()
    time.sleep(delay)
    fd.write(make_report(0x00, 0x00))  # release all
    fd.flush()
    time.sleep(delay)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--log',     required=True, help='Path to keyboard_log.txt')
    p.add_argument('--device',  default='/dev/hidg0', help='HID gadget device')
    p.add_argument('--delay',   type=float, default=0.02,  help='Delay between events')
    args = p.parse_args()

    try:
        hid = open(args.device, 'wb')
    except PermissionError:
        sys.exit(f"Cannot open {args.device}; try sudo.")

    with open(args.log, 'r', encoding='utf-8') as logf:
        for tok in follow_tokens(logf):
            # Special bracketed key?
            if tok in SPECIAL:
                mod, usage = SPECIAL[tok]

            # Single character
            elif len(tok) == 1:
                c = tok
                # shifted symbol?
                if c in SHIFTED:
                    base = SHIFTED[c]
                    mod = 0x02         # left shift
                    usage = UNSHIFTED[base]
                # uppercase letter
                elif 'A' <= c <= 'Z':
                    mod = 0x02
                    usage = UNSHIFTED[c.lower()]
                # unshifted
                elif c in UNSHIFTED:
                    mod = 0x00
                    usage = UNSHIFTED[c]
                else:
                    # unknown char
                    continue
            else:
                # unknown multi-char token
                continue

            send_key(hid, mod, usage, args.delay)

    hid.close()

if __name__ == '__main__':
    main()
