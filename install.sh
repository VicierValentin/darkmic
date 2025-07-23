#!/bin/bash
# Create gadget directory
cd /sys/kernel/config/usb_gadget/
echo "" > g_multi/UDC
mkdir -p mykeyboard
cd mykeyboard

# Set USB device descriptor
echo 0x1d6b |  tee idVendor   # Linux Foundation
echo 0x0104 |  tee idProduct  # Multifunction Composite Gadget
echo 0x0100 |  tee bcdDevice  # v1.0.0
echo 0x0200 |  tee bcdUSB     # USB2

# Create English locale
mkdir -p strings/0x409
echo "BeagleBone" |  tee strings/0x409/manufacturer
echo "HID Keyboard" |  tee strings/0x409/product

# Create configuration
mkdir -p configs/c.1/strings/0x409
echo "Config 1: HID Keyboard" |  tee configs/c.1/strings/0x409/configuration
echo 250 |  tee configs/c.1/MaxPower

# Create HID function
mkdir -p functions/hid.usb0
echo 1 |  tee functions/hid.usb0/protocol      # Keyboard
echo 1 |  tee functions/hid.usb0/subclass     # Boot interface subclass
echo 8 |  tee functions/hid.usb0/report_length # Report length

# HID Report Descriptor for standard keyboard
echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 |  tee functions/hid.usb0/report_desc

# Link function to configuration
ln -s functions/hid.usb0 configs/c.1/


# Enable gadget
ls /sys/class/udc |  tee UDC