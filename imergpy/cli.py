import sys
from .server import start_server

def main():
    """Entry point for the imergpy CLI."""
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nShutting down imergpy interface...")
        sys.exit(0)

if __name__ == "__main__":
    main()
