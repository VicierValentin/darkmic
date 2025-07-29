#!/usr/bin/env python3
"""
QWERTY to AZERTY Keyboard Log Translator

This script translates keyboard logs from QWERTY layout to AZERTY layout,
handling both regular keys and special symbols with modifiers.
"""

import re
import sys
from typing import Dict, Tuple, Optional

class QwertyToAzertyTranslator:
    def __init__(self):
        # Basic QWERTY to AZERTY key mappings
        self.basic_mapping = {
            # First row
            'q': 'a', 'w': 'z', 'e': 'e', 'r': 'r', 't': 't', 'y': 'y', 'u': 'u', 'i': 'i', 'o': 'o', 'p': 'p',
            # Second row  
            'a': 'q', 's': 's', 'd': 'd', 'f': 'f', 'g': 'g', 'h': 'h', 'j': 'j', 'k': 'k', 'l': 'l',
            # Third row
            'z': 'w', 'x': 'x', 'c': 'c', 'v': 'v', 'b': 'b', 'n': 'n', 'm': 'm',
            # Numbers (same positions)
            '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9', '0': '0'
        }
        
        # QWERTY to AZERTY symbol mappings (without modifiers)
        self.symbol_mapping = {
            # QWERTY symbols -> AZERTY symbols (unshifted)
            ';': 'm',
            "'": 'ù',
            '[': '^',
            ']': '$',
            '\\': '*',
            '/': '!',
            '.': '.',
            ',': ',',
            '`': '²',
            '-': ')',
            '=': '=',
        }
        
        # QWERTY shifted symbols to AZERTY shifted symbols
        self.shifted_symbol_mapping = {
            # QWERTY Shift+key -> AZERTY Shift+key
            '!': '1',  # Shift+1 on QWERTY -> Shift+1 on AZERTY (but different symbol)
            '@': '2',  # Shift+2 on QWERTY -> Shift+2 on AZERTY  
            '#': '3',
            '$': '4',
            '%': '5',
            '^': '6',
            '&': '7',
            '*': '8',
            '(': '9',
            ')': '0',
            '_': '°',  # Shift+- on QWERTY -> Shift+) on AZERTY
            '+': '+',  # Shift+= on QWERTY -> Shift+= on AZERTY
            '{': '¨',  # Shift+[ on QWERTY -> Shift+^ on AZERTY
            '}': '£',  # Shift+] on QWERTY -> Shift+$ on AZERTY
            '|': 'µ',  # Shift+\ on QWERTY -> Shift+* on AZERTY
            ':': 'M',  # Shift+; on QWERTY -> Shift+m on AZERTY
            '"': '%',  # Shift+' on QWERTY -> Shift+ù on AZERTY
            '<': '?',  # Shift+, on QWERTY -> Shift+, on AZERTY
            '>': '.',  # Shift+. on QWERTY -> Shift+. on AZERTY
            '?': '§',  # Shift+/ on QWERTY -> Shift+! on AZERTY
            '~': '~',  # Shift+` on QWERTY -> similar on AZERTY
        }
        
        # AltGr mappings for AZERTY (common symbols accessed with AltGr)
        self.altgr_mapping = {
            # Common AltGr symbols on AZERTY
            '@': '~',   # AltGr+0 = @
            '3': '#',   # AltGr+e = €
            '$': '{',
            '5': '[',
            '6': '|',
            '{': '`',
            '[': '\\',
            ']': '^',
            '}': '@',
            '\\': ']',
            '=': '}',
            '~': 'ê',
            
        }

    def translate_key(self, key: str, modifiers: str = "") -> str:
        """
        Translate a single key from QWERTY to AZERTY layout
        
        Args:
            key: The key to translate
            modifiers: Modifier keys (e.g., "shift", "altgr")
            
        Returns:
            Translated key for AZERTY layout
        """
        key_lower = key.lower()
        
        # Handle special modifier keys
        if key_lower in ['shift', 'ctrl', 'alt', 'alt gr', 'altgr', 'win', 'cmd']:
            return key  # Keep modifier keys as-is
            
        # Handle AltGr combinations
        if 'altgr' in modifiers.lower():
            # For AltGr combinations, we need to map the symbol back to the key position
            for symbol, azerty_key in self.altgr_mapping.items():
                if key == symbol:
                    return f"AltGr+{azerty_key}"
            return f"AltGr+{self.basic_mapping.get(key_lower, key)}"
        
        # Handle shifted symbols
        if key in self.shifted_symbol_mapping:
            azerty_pos = self.shifted_symbol_mapping[key]
            return f"Shift+{azerty_pos}"
        
        # Handle basic symbols
        if key in self.symbol_mapping:
            return self.symbol_mapping[key]
            
        # Handle basic letter/number mappings
        if key_lower in self.basic_mapping:
            mapped = self.basic_mapping[key_lower]
            # Preserve original case
            if key.isupper():
                return mapped.upper()
            return mapped
            
        # If no mapping found, return original key
        return key

    def parse_log_line(self, line: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse a keyboard log line and extract timestamp, key, and modifiers
        
        Args:
            line: Log line to parse
            
        Returns:
            Tuple of (timestamp, key, modifiers) or None if parsing fails
        """
        # Pattern to match log lines like: [2025-07-25 21:02:38.099] Key: t
        # or [2025-07-25 21:03:03.728] Key: alt gr | Modifiers: altgr
        pattern = r'\[([^\]]+)\]\s+Key:\s+([^|]+?)(?:\s+\|\s+Modifiers:\s+(.+))?$'
        
        match = re.match(pattern, line.strip())
        if match:
            timestamp = match.group(1)
            key = match.group(2).strip()
            modifiers = match.group(3).strip() if match.group(3) else ""
            return timestamp, key, modifiers
        
        return None

    def translate_log_file(self, input_file: str, output_file: str = None) -> None:
        """
        Translate an entire keyboard log file from QWERTY to AZERTY
        
        Args:
            input_file: Path to input log file
            output_file: Path to output file (if None, prints to stdout)
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: File '{input_file}' not found.")
            return
        except Exception as e:
            print(f"Error reading file: {e}")
            return

        translated_lines = []
        
        for line_num, line in enumerate(lines, 1):
            if line.strip():  # Skip empty lines
                parsed = self.parse_log_line(line)
                if parsed:
                    timestamp, key, modifiers = parsed
                    translated_key = self.translate_key(key, modifiers)
                    
                    # Reconstruct the log line
                    if modifiers:
                        translated_line = f"[{timestamp}] Key: {translated_key} | Modifiers: {modifiers}"
                    else:
                        translated_line = f"[{timestamp}] Key: {translated_key}"
                    
                    translated_lines.append(translated_line)
                else:
                    # Keep original line if parsing fails
                    translated_lines.append(line.rstrip())
            else:
                translated_lines.append("")
        
        # Output results
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    for line in translated_lines:
                        f.write(line + '\n')
                print(f"Translation completed. Output saved to '{output_file}'")
            except Exception as e:
                print(f"Error writing output file: {e}")
        else:
            print("QWERTY to AZERTY Translation:")
            print("=" * 50)
            for line in translated_lines:
                print(line)

def main():
    translator = QwertyToAzertyTranslator()
    
    if len(sys.argv) < 2:
        print("Usage: python qwerty_to_azerty.py <input_file> [output_file]")
        print("Example: python qwerty_to_azerty.py keyboard_log.txt translated_log.txt")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    translator.translate_log_file(input_file, output_file)

if __name__ == "__main__":
    main()
