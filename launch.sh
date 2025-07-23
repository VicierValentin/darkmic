#!/bin/bash
#
# Starts the evtest-based logger and then the HID emulator.
#
LOGGER="/usr/bin/python3 /home/debian/readevttest.py -o /var/log/keyboard_log.txt"
EMULATOR="/usr/bin/python3 /home/debian/keyboard_emulator_follow.py \
           --log /var/log/keyboard_log.txt --device /dev/hidg0 --delay 0.02"

# Ensure log file exists
touch /var/log/keyboard_log.txt
chmod 600 /var/log/keyboard_log.txt

# Start logger in background
$LOGGER &
LOGGER_PID=$!

# Give the logger time to initialize
sleep 1

# Start emulator in foreground (so systemd can track it)
exec $EMULATOR
