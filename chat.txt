#!/bin/bash

# HID device file
HID_DEVICE="/dev/hidg0"

# Function to send a key press
send_key() {
    local keycode=$1
    local modifier=${2:-0}
    
    # Send key press (modifier, reserved, key1, key2, key3, key4, key5, key6)
    printf "\\x$(printf %02x $modifier)\\x00\\x$(printf %02x $keycode)\\x00\\x00\\x00\\x00\\x00" > $HID_DEVICE
    
    # Small delay
    sleep 0.01
    
    # Send key release (all zeros)
    printf "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00" | tee $HID_DEVICE
}

# Function to get keycode for a character
get_keycode() {
    case $1 in
        'a') echo 4 ;;
        'b') echo 5 ;;
        'c') echo 6 ;;
        'd') echo 7 ;;
        'e') echo 8 ;;
        'f') echo 9 ;;
        'g') echo 10 ;;
        'h') echo 11 ;;
        'i') echo 12 ;;
        'j') echo 13 ;;
        'k') echo 14 ;;
        'l') echo 15 ;;
        'm') echo 16 ;;
        'n') echo 17 ;;
        'o') echo 18 ;;
        'p') echo 19 ;;
        'q') echo 20 ;;
        'r') echo 21 ;;
        's') echo 22 ;;
        't') echo 23 ;;
        'u') echo 24 ;;
        'v') echo 25 ;;
        'w') echo 26 ;;
        'x') echo 27 ;;
        'y') echo 28 ;;
        'z') echo 29 ;;
        ' ') echo 44 ;;  # Space
        '\n') echo 40 ;; # Enter
        '1') echo 30 ;;
        '2') echo 31 ;;
        '3') echo 32 ;;
        '4') echo 33 ;;
        '5') echo 34 ;;
        '6') echo 35 ;;
        '7') echo 36 ;;
        '8') echo 37 ;;
        '9') echo 38 ;;
        '0') echo 39 ;;
        *) echo 0 ;;     # Unknown character
    esac
}

# Function to send a string
send_string() {
    local text="$1"
    local i=0
    
    while [ $i -lt ${#text} ]; do
        char="${text:$i:1}"
        keycode=$(get_keycode "$char")
        
        if [ $keycode -ne 0 ]; then
            send_key $keycode
            sleep 0.05  # Delay between characters
        fi
        
        i=$((i + 1))
    done
}

# Function to send special keys
send_special_key() {
    case $1 in
        'enter') send_key 40 ;;
        'escape') send_key 41 ;;
        'backspace') send_key 42 ;;
        'tab') send_key 43 ;;
        'space') send_key 44 ;;
        'caps_lock') send_key 57 ;;
        'f1') send_key 58 ;;
        'f2') send_key 59 ;;
        'f3') send_key 60 ;;
        'f4') send_key 61 ;;
        'f5') send_key 62 ;;
        'f6') send_key 63 ;;
        'f7') send_key 64 ;;
        'f8') send_key 65 ;;
        'f9') send_key 66 ;;
        'f10') send_key 67 ;;
        'f11') send_key 68 ;;
        'f12') send_key 69 ;;
        'home') send_key 74 ;;
        'page_up') send_key 75 ;;
        'delete') send_key 76 ;;
        'end') send_key 77 ;;
        'page_down') send_key 78 ;;
        'right_arrow') send_key 79 ;;
        'left_arrow') send_key 80 ;;
        'down_arrow') send_key 81 ;;
        'up_arrow') send_key 82 ;;
        *) echo "Unknown special key: $1" ;;
    esac
}

# Main script logic
case "$1" in
    -s|--string)
        if [ -z "$2" ]; then
            echo "Usage: $0 -s \"text to send\""
            exit 1
        fi
        send_string "$2"
        ;;
    -k|--key)
        if [ -z "$2" ]; then
            echo "Usage: $0 -k special_key_name"
            exit 1
        fi
        send_special_key "$2"
        ;;
    -c|--char)
        if [ -z "$2" ]; then
            echo "Usage: $0 -c character"
            exit 1
        fi
        keycode=$(get_keycode "$2")
        send_key $keycode
        ;;
    *)
        echo "USB HID Keyboard Script"
        echo "Usage:"
        echo "  $0 -s \"text\"          Send a string"
        echo "  $0 -k special_key      Send a special key"
        echo "  $0 -c character        Send a single character"
        echo ""
        echo "Examples:"
        echo "  $0 -s \"hello world\"    # Send text"
        echo "  $0 -k enter             # Send Enter key"
        echo "  $0 -k f1                # Send F1 key"
        echo "  $0 -c a                 # Send character 'a'"
        echo ""
        echo "Special keys available:"
        echo "  enter, escape, backspace, tab, space, caps_lock"
        echo "  f1-f12, home, end, page_up, page_down, delete"
        echo "  up_arrow, down_arrow, left_arrow, right_arrow"
        exit 1
        ;;
esac