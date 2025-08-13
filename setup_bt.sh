#!/bin/bash

# Bluetooth Setup and Listener Script for BeagleBone Black
# This script sets up Bluetooth, makes it discoverable, and creates a listening service

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RFCOMM_DEVICE="/dev/rfcomm0"
RFCOMM_CHANNEL=1
SERVICE_NAME="BeagleBone-BT-Service"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to check if bluetooth service is installed
check_bluetooth_installed() {
    if ! command -v bluetoothctl &> /dev/null; then
        print_error "Bluetooth tools not installed!"
        print_status "Please install with: sudo apt install bluetooth bluez bluez-tools rfcomm"
        exit 1
    fi
}

# Function to start bluetooth service
start_bluetooth_service() {
    print_status "Starting Bluetooth service..."
    
    systemctl start bluetooth
    if [ $? -eq 0 ]; then
        print_success "Bluetooth service started"
    else
        print_error "Failed to start Bluetooth service"
        exit 1
    fi
    
    systemctl enable bluetooth
    sleep 2
}

# Function to get bluetooth adapter info
get_bluetooth_info() {
    print_status "Getting Bluetooth adapter information..."
    
    # Get Bluetooth adapter address
    BT_ADAPTER=$(hciconfig | grep -o "hci[0-9]" | head -n1)
    if [ -z "$BT_ADAPTER" ]; then
        print_error "No Bluetooth adapter found!"
        exit 1
    fi
    
    BT_ADDRESS=$(hciconfig $BT_ADAPTER | grep "BD Address" | awk '{print $3}')
    if [ -z "$BT_ADDRESS" ]; then
        print_error "Could not get Bluetooth address!"
        exit 1
    fi
    
    print_success "Bluetooth adapter: $BT_ADAPTER"
    print_success "Bluetooth address: $BT_ADDRESS"
}

# Function to configure bluetooth with bluetoothctl
configure_bluetooth() {
    print_status "Configuring Bluetooth settings..."
    
    # Create bluetoothctl commands file
    cat > /tmp/bt_setup_commands << EOF
power on
discoverable on
pairable on
agent on
default-agent
quit
EOF

    # Execute bluetoothctl commands
    bluetoothctl < /tmp/bt_setup_commands
    
    # Clean up
    rm -f /tmp/bt_setup_commands
    
    sleep 3
    
    # Verify settings
    if bluetoothctl show | grep -q "Powered: yes"; then
        print_success "Bluetooth powered on"
    else
        print_warning "Bluetooth may not be powered on properly"
    fi
    
    if bluetoothctl show | grep -q "Discoverable: yes"; then
        print_success "Bluetooth is discoverable"
    else
        print_warning "Bluetooth may not be discoverable"
    fi

    sleep 2

    bluetoothctl pair E4:1F:D5:BE:C5:02
    bluetoothctl trust E4:1F:D5:BE:C5:02
    #bluetoothctl connect E4:1F:D5:BE:C5:02

    sleep 3
}

# Function to setup RFCOMM service
setup_rfcomm_service() {
    print_status "Setting up RFCOMM listening service..."
    
    # Kill any existing rfcomm processes
    pkill -f "rfcomm listen" 2>/dev/null
    
    # Release any existing rfcomm connections
    rfcomm release $RFCOMM_DEVICE 2>/dev/null
    
    # Wait a moment
    sleep 2
    
    # Start RFCOMM listener in background
    print_status "Starting RFCOMM listener on channel $RFCOMM_CHANNEL..."
    rfcomm listen $RFCOMM_DEVICE $RFCOMM_CHANNEL &
    RFCOMM_PID=$!
    
    # Wait a moment for the service to start
    sleep 3
    
    # Check if rfcomm process is running
    if ps -p $RFCOMM_PID > /dev/null 2>&1; then
        print_success "RFCOMM listener started (PID: $RFCOMM_PID)"
        echo $RFCOMM_PID > /tmp/rfcomm_listener.pid
    else
        print_error "Failed to start RFCOMM listener"
        exit 1
    fi
}

# Function to register SDP service (Serial Port Profile)
register_sdp_service() {
    print_status "Registering Serial Port service..."
    
    # Add Serial Port service
    sdptool add --channel=$RFCOMM_CHANNEL SP
    
    if [ $? -eq 0 ]; then
        print_success "Serial Port service registered on channel $RFCOMM_CHANNEL"
    else
        print_warning "Failed to register SDP service (may still work)"
    fi
}

# Function to show device status
show_status() {
    echo
    print_success "=== Bluetooth Setup Complete ==="
    echo -e "${BLUE}Device Name:${NC} $(hostname)"
    echo -e "${BLUE}Bluetooth Address:${NC} $BT_ADDRESS"
    echo -e "${BLUE}RFCOMM Device:${NC} $RFCOMM_DEVICE"
    echo -e "${BLUE}RFCOMM Channel:${NC} $RFCOMM_CHANNEL"
    echo -e "${BLUE}Service Status:${NC} Running"
    echo
    
    print_status "Your BeagleBone is now discoverable and ready to receive connections!"
    print_status "From your PC, you can connect using:"
    echo -e "${YELLOW}  sudo rfcomm connect /dev/rfcomm1 $BT_ADDRESS $RFCOMM_CHANNEL${NC}"
    echo
    print_status "To send data:"
    echo -e "${YELLOW}  echo 'hello world' > /dev/rfcomm1${NC}"
    echo
}

# Function to monitor the connection
monitor_connection() {
    print_status "Monitoring for incoming connections..."
    print_status "Press Ctrl+C to stop"
    echo
    
    # Monitor the RFCOMM device for data
    while true; do
        if [ -e "$RFCOMM_DEVICE" ]; then
            # Check if device is ready for reading
            if [ -r "$RFCOMM_DEVICE" ]; then
                print_success "Connection established on $RFCOMM_DEVICE"
            fi
        fi
        sleep 2
    done
}

# Function to cleanup on exit
cleanup() {
    echo
    print_status "Cleaning up..."
    
    # Kill RFCOMM listener
    if [ -f /tmp/rfcomm_listener.pid ]; then
        RFCOMM_PID=$(cat /tmp/rfcomm_listener.pid)
        if ps -p $RFCOMM_PID > /dev/null 2>&1; then
            kill $RFCOMM_PID 2>/dev/null
            print_status "RFCOMM listener stopped"
        fi
        rm -f /tmp/rfcomm_listener.pid
    fi
    
    # Release RFCOMM device
    rfcomm release $RFCOMM_DEVICE 2>/dev/null
    
    # Remove SDP service
    sdptool del SP 2>/dev/null
    
    print_success "Cleanup complete"
    exit 0
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -m, --monitor    Start monitoring mode after setup"
    echo "  -c, --channel N  Use RFCOMM channel N (default: 1)"
    echo "  -d, --device D   Use RFCOMM device D (default: /dev/rfcomm0)"
    echo
    echo "Examples:"
    echo "  $0                    # Basic setup"
    echo "  $0 -m                 # Setup and monitor connections"
    echo "  $0 -c 2 -d /dev/rfcomm1  # Use channel 2 and device rfcomm1"
}

# Parse command line arguments
MONITOR_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -m|--monitor)
            MONITOR_MODE=true
            shift
            ;;
        -c|--channel)
            RFCOMM_CHANNEL="$2"
            shift 2
            ;;
        -d|--device)
            RFCOMM_DEVICE="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Set up signal handlers for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Main execution
main() {
    print_status "BeagleBone Black Bluetooth Setup Script"
    echo
    
    # Perform checks and setup
    check_root
    #check_bluetooth_installed
    start_bluetooth_service
    get_bluetooth_info
    configure_bluetooth
    setup_rfcomm_service
    #register_sdp_service
    show_status
    
    # Monitor mode if requested
    if [ "$MONITOR_MODE" = true ]; then
        monitor_connection
    else
        print_status "Setup complete. Use -m flag to start monitoring mode."
        print_status "Or run your Python monitoring script now."
        
        # Keep the script running to maintain the RFCOMM listener
        print_status "Keeping RFCOMM service running... (Ctrl+C to stop)"
        while true; do
            sleep 10
            # Check if RFCOMM listener is still running
            if [ -f /tmp/rfcomm_listener.pid ]; then
                RFCOMM_PID=$(cat /tmp/rfcomm_listener.pid)
                if ! ps -p $RFCOMM_PID > /dev/null 2>&1; then
                    print_warning "RFCOMM listener died, restarting..."
                    setup_rfcomm_service
                fi
            fi
        done
    fi
}

# Run main function
main