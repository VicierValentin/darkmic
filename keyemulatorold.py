#!/usr/bin/env python3
import argparse
import re
import sys
import time
import unicodedata

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
    ',':   0x36, '.': 0x37, '/': 0x38
}

# Characters requiring Shift + base key
SHIFTED = {
    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
    '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
    '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\',
    ':': ';', '"': "'", '~': '`', '<': ',', '>': '.', '?': '/'
}

# AZERTY layout special characters mapping
# These characters can be directly typed on AZERTY keyboards
AZERTY_DIRECT = {
    # Numbers row (without shift)
    '&': (0x00, 0x1E),  # 1 key
    'é': (0x00, 0x1F),  # 2 key
    '"': (0x00, 0x20),  # 3 key
    "'": (0x00, 0x21),  # 4 key
    '(': (0x00, 0x22),  # 5 key
    '-': (0x00, 0x23),  # 6 key
    'è': (0x00, 0x24),  # 7 key
    '_': (0x00, 0x25),  # 8 key
    'ç': (0x00, 0x26),  # 9 key
    'à': (0x00, 0x27),  # 0 key
    ')': (0x00, 0x2D),  # - key
    '=': (0x00, 0x2E),  # = key
    
    # Numbers row (with shift)
    '1': (0x02, 0x1E),  # Shift + 1 key
    '2': (0x02, 0x1F),  # Shift + 2 key
    '3': (0x02, 0x20),  # Shift + 3 key
    '4': (0x02, 0x21),  # Shift + 4 key
    '5': (0x02, 0x22),  # Shift + 5 key
    '6': (0x02, 0x23),  # Shift + 6 key
    '7': (0x02, 0x24),  # Shift + 7 key
    '8': (0x02, 0x25),  # Shift + 8 key
    '9': (0x02, 0x26),  # Shift + 9 key
    '0': (0x02, 0x27),  # Shift + 0 key
    '°': (0x02, 0x2D),  # Shift + - key
    '+': (0x02, 0x2E),  # Shift + = key
    
    # Other AZERTY specific characters
    '^': (0x00, 0x2F),  # [ key on QWERTY
    '$': (0x00, 0x30),  # ] key on QWERTY
    'ù': (0x00, 0x34),  # ' key on QWERTY
    '*': (0x00, 0x31),  # \ key on QWERTY
    'm': (0x00, 0x33),  # ; key on QWERTY (m on AZERTY)
    '!': (0x00, 0x38),  # / key on QWERTY
    ';': (0x00, 0x36),  # , key on QWERTY
    ':': (0x00, 0x37),  # . key on QWERTY
    
    # Shifted versions
    '¨': (0x02, 0x2F),  # Shift + ^ key
    '£': (0x02, 0x30),  # Shift + $ key
    'µ': (0x02, 0x33),  # Shift + m key
    '%': (0x02, 0x34),  # Shift + ù key
    '§': (0x02, 0x38),  # Shift + ! key
    '.': (0x02, 0x36),  # Shift + ; key
    '/': (0x02, 0x37),  # Shift + : key
    '?': (0x02, 0x36),  # Alternative for .
}

# AltGr combinations for special characters
ALTGR_CHARS = {
    # Common AltGr characters on AZERTY
    '€': (0x40, 0x08),  # AltGr + E
    '~': (0x40, 0x1F),  # AltGr + 2
    '#': (0x40, 0x20),  # AltGr + 3
    '{': (0x40, 0x21),  # AltGr + 4
    '[': (0x40, 0x22),  # AltGr + 5
    '|': (0x40, 0x23),  # AltGr + 6
    '`': (0x40, 0x24),  # AltGr + 7
    '\\': (0x40, 0x25), # AltGr + 8
    ']': (0x40, 0x2D),  # AltGr + -
    '}': (0x40, 0x2E),  # AltGr + =
    '@': (0x40, 0x27),  # AltGr + 0
}

# Dead key combinations for accented characters
# These require a dead key followed by a base character
DEAD_KEY_COMBINATIONS = {
    # Acute accent (´) combinations
    'á': [(0x00, 0x34), (0x00, 0x04)],  # ´ + a
    'é': [(0x00, 0x34), (0x00, 0x08)],  # ´ + e  
    'í': [(0x00, 0x34), (0x00, 0x0C)],  # ´ + i
    'ó': [(0x00, 0x34), (0x00, 0x12)],  # ´ + o
    'ú': [(0x00, 0x34), (0x00, 0x18)],  # ´ + u
    'ý': [(0x00, 0x34), (0x00, 0x1C)],  # ´ + y
    
    # Grave accent (`) combinations
    'à': [(0x00, 0x35), (0x00, 0x04)],  # ` + a
    'è': [(0x00, 0x35), (0x00, 0x08)],  # ` + e
    'ì': [(0x00, 0x35), (0x00, 0x0C)],  # ` + i
    'ò': [(0x00, 0x35), (0x00, 0x12)],  # ` + o
    'ù': [(0x00, 0x35), (0x00, 0x18)],  # ` + u
    
    # Circumflex (^) combinations
    'â': [(0x00, 0x2F), (0x00, 0x04)],  # ^ + a
    'ê': [(0x00, 0x2F), (0x00, 0x08)],  # ^ + e
    'î': [(0x00, 0x2F), (0x00, 0x0C)],  # ^ + i
    'ô': [(0x00, 0x2F), (0x00, 0x12)],  # ^ + o
    'û': [(0x00, 0x2F), (0x00, 0x18)],  # ^ + u
    
    # Diaeresis (¨) combinations
    'ä': [(0x02, 0x2F), (0x00, 0x04)],  # ¨ + a
    'ë': [(0x02, 0x2F), (0x00, 0x08)],  # ¨ + e
    'ï': [(0x02, 0x2F), (0x00, 0x0C)],  # ¨ + i
    'ö': [(0x02, 0x2F), (0x00, 0x12)],  # ¨ + o
    'ü': [(0x02, 0x2F), (0x00, 0x18)],  # ¨ + u
    'ÿ': [(0x02, 0x2F), (0x00, 0x1C)],  # ¨ + y
    
    # Cedilla combinations
    'ç': [(0x00, 0x06)],  # Direct c with cedilla (simplified)
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

def send_key_sequence(fd, key_sequence, delay):
    """Send a sequence of keys (for dead key combinations)."""
    for mod, usage in key_sequence:
        send_key(fd, mod, usage, delay)

def handle_special_char(c):
    """
    Handle special characters by returning appropriate key sequences.
    Returns a tuple: (is_handled, key_data)
    """
    # Check AZERTY direct mappings first
    if c in AZERTY_DIRECT:
        return True, [AZERTY_DIRECT[c]]
    
    # Check AltGr combinations
    if c in ALTGR_CHARS:
        return True, [ALTGR_CHARS[c]]
    
    # Check dead key combinations
    if c in DEAD_KEY_COMBINATIONS:
        return True, DEAD_KEY_COMBINATIONS[c]
    
    # Try to decompose the character (e.g., é -> e + ´)
    try:
        decomposed = unicodedata.decompose(c)
        if len(decomposed) == 2:
            base_char = decomposed[0]
            accent = decomposed[1]
            
            # Map common combining accents to dead keys
            accent_map = {
                '\u0301': (0x00, 0x34),  # Combining acute accent -> ´
                '\u0300': (0x00, 0x35),  # Combining grave accent -> `
                '\u0302': (0x00, 0x2F),  # Combining circumflex -> ^
                '\u0308': (0x02, 0x2F),  # Combining diaeresis -> ¨
            }
            
            if accent in accent_map and base_char.lower() in UNSHIFTED:
                dead_key = accent_map[accent]
                base_key = (0x00, UNSHIFTED[base_char.lower()])
                return True, [dead_key, base_key]
    except:
        pass
    
    return False, None

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--log',     required=True, help='Path to keyboard_log.txt')
    p.add_argument('--device',  default='/dev/hidg0', help='HID gadget device')
    p.add_argument('--delay',   type=float, default=0.02,  help='Delay between events')
    p.add_argument('--layout',  default='azerty', choices=['azerty', 'qwerty'], 
                   help='Keyboard layout to use')
    args = p.parse_args()

    try:
        hid = open(args.device, 'wb')
    except PermissionError:
        sys.exit(f"Cannot open {args.device}; try sudo.")

    print(f"Starting key emulator with {args.layout.upper()} layout")
    print(f"Reading from: {args.log}")
    print(f"Output device: {args.device}")
    print(f"Key delay: {args.delay}s")

    with open(args.log, 'r', encoding='utf-8') as logf:
        for tok in follow_tokens(logf):
            # Special bracketed key?
            if tok in SPECIAL:
                mod, usage = SPECIAL[tok]
                send_key(hid, mod, usage, args.delay)

            # Single character
            elif len(tok) == 1:
                c = tok
                
                # Try to handle special characters first
                handled, key_data = handle_special_char(c)
                if handled:
                    if len(key_data) == 1:
                        # Single key press
                        mod, usage = key_data[0]
                        send_key(hid, mod, usage, args.delay)
                    else:
                        # Key sequence (dead keys)
                        send_key_sequence(hid, key_data, args.delay)
                    continue
                
                # Fall back to original logic for standard characters
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
                    # unknown char - try Unicode fallback
                    print(f"Warning: Unknown character '{c}' (U+{ord(c):04X})")
                    continue
                
                send_key(hid, mod, usage, args.delay)
            else:
                # unknown multi-char token
                print(f"Warning: Unknown token '{tok}'")
                continue

    hid.close()

if __name__ == '__main__':
    main()