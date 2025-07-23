#!/bin/bash
#
# bbb-keyboard.sh
# Configure BeagleBone Black as a USB HID keyboard via ConfigFS
# Unbinds any existing gadget on the UDC before binding the new one.
#

set -e

# 1. Ensure we’re running as root
if [ "$(id -u)" -ne 0 ]; then
  echo "Error: Must be run as root. Exiting." >&2
  exit 1
fi

# 2. Load composite framework and mount ConfigFS
modprobe libcomposite
mountpoint -q /sys/kernel/config || mount -t configfs none /sys/kernel/config

# 3. Unbind all other USB gadgets (clear their UDC binding)
for g in /sys/kernel/config/usb_gadget/*; do
  [ -d "$g" ] || continue
  # Skip if this is the gadget we're about to create
  if [ "$(basename "$g")" != "keyboard" ]; then
    if [ -f "$g/UDC" ] && [ -n "$(cat "$g/UDC")" ]; then
      echo "Unbinding existing gadget: $(basename "$g")"
      echo "" > "$g/UDC"
    fi
  fi
done

# 4. Clean up any previous "keyboard" gadget
GADGET_DIR=/sys/kernel/config/usb_gadget/keyboard

# 5. Create gadget directory and set IDs
mkdir -p "$GADGET_DIR"
echo 0x1d6b > "$GADGET_DIR/idVendor"     # Linux Foundation
echo 0x0104 > "$GADGET_DIR/idProduct"    # Multifunction Composite Gadget

# 6. Create English strings
mkdir -p "$GADGET_DIR/strings/0x409"
echo "YourCompany"  > "$GADGET_DIR/strings/0x409/manufacturer"
echo "BBB Keyboard" > "$GADGET_DIR/strings/0x409/product"
echo "12345678"     > "$GADGET_DIR/strings/0x409/serialnumber"

# 7. Create HID function (keyboard)
mkdir -p "$GADGET_DIR/functions/hid.usb0"
echo 1 > "$GADGET_DIR/functions/hid.usb0/protocol"
echo 1 > "$GADGET_DIR/functions/hid.usb0/subclass"
echo 8 > "$GADGET_DIR/functions/hid.usb0/report_length"

# 8. Write standard keyboard report descriptor
cat > "$GADGET_DIR/functions/hid.usb0/report_desc" <<'EOF'
05 01 09 06 A1 01 05 07 19 E0 29 E7 15 00
25 01 75 01 95 08 81 02 95 01 75 08 81 01
95 05 75 01 05 08 19 01 29 05 91 02 95 01
75 03 91 01 95 06 75 08 15 00 25 65 05 07
19 00 29 65 81 00 C0
EOF

# 9. Create configuration and link HID function
mkdir -p "$GADGET_DIR/configs/c.1"
echo 120 > "$GADGET_DIR/configs/c.1/MaxPower"
ln -s "$GADGET_DIR/functions/hid.usb0" "$GADGET_DIR/configs/c.1/"

# 10. Verify available UDCs and select one
mapfile -t UDC_LIST < <(ls /sys/class/udc)
if [ ${#UDC_LIST[@]} -eq 0 ]; then
  echo "Error: No UDC available. Exiting." >&2
  exit 1
elif [ ${#UDC_LIST[@]} -gt 1 ]; then
  echo "Warning: Multiple UDCs found: ${UDC_LIST[*]}"
  echo "Using first one: ${UDC_LIST[0]}"
fi

UDC="${UDC_LIST[0]}"
echo "$UDC" > "$GADGET_DIR/UDC"

echo
echo "USB HID keyboard gadget is now live!"
echo "On the host PC you’ll see a new keyboard device."
echo "Send reports by writing 8-byte frames to /dev/hidg0 on the BBB."
