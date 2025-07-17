import sys
import tty
import termios

def main():
    output_file = "output.txt"
    print("Start typing. Press Ctrl+C to stop.")
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            tty.setraw(fd)  # Set terminal to raw mode
            while True:
                ch = sys.stdin.read(1)  # Read one char immediately
                f.write(ch)
                f.flush()  # Save immediately
    except KeyboardInterrupt:
        print("\nStopped by user. Data saved to", output_file)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # Restore settings

if __name__ == "__main__":
    main()
