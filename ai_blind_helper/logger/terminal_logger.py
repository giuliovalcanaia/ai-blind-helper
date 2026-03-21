import argparse
import sys
import os
from datetime import datetime
from provider import *

class TerminalLogger:
    """
    Captures all terminal prints and errors and saves them to a file,
    while also showing them on screen.
    """
    def __init__(self, log_folder="logs"):
        # Create the log folder if it doesn't exist
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        # Create filename: logs/log_2025-12-19_10-30-00.txt
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(log_folder, f"log_{timestamp}.txt")
        
        # Open the file in append mode and keep a reference
        self.log_file = open(self.filename, "a", encoding="utf-8")
        self.terminal = sys.stdout # Keep the original terminal
        
    def write(self, message):
        # Write to the screen (original terminal)
        self.terminal.write(message)
        # Write to the file
        self.log_file.write(message)
        # Force flush to disk immediately (useful if the program crashes)
        self.log_file.flush() 

    def flush(self):
        # Required for compatibility with the system
        self.terminal.flush()
        self.log_file.flush()

    def start(self):
        """Redireciona stdout e stderr para esta classe"""
        sys.stdout = self
        sys.stderr = self # Also capture errors (exceptions/tracebacks)
        print(f"--- [Logger] Logging session at: {self.filename} ---")