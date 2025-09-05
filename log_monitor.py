#!/usr/bin/env python3
"""
Real-time log monitoring for query refinement process.
This script tails the log files and provides a colored, structured view of the refinement flow.
"""

import os
import sys
import time
import re
from datetime import datetime
from typing import Optional


# ANSI color codes for beautiful terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def colorize(text: str, color: str) -> str:
    """Add color to text."""
    return f"{color}{text}{Colors.END}"


def parse_log_line(line: str) -> Optional[dict]:
    """Parse a log line and extract relevant information."""

    # Match standard log format: timestamp - module - level - [task_id] - message
    pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - (\w+) - (?:\[([^\]]*)\] )?- (.+)"
    match = re.match(pattern, line.strip())

    if not match:
        return None

    timestamp, module, level, task_id, message = match.groups()

    return {
        "timestamp": timestamp,
        "module": module.strip(),
        "level": level.strip(),
        "task_id": task_id or "",
        "message": message.strip(),
    }


def format_log_entry(entry: dict) -> str:
    """Format a log entry with colors and structure."""

    # Color mapping for log levels
    level_colors = {
        "DEBUG": Colors.CYAN,
        "INFO": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.RED + Colors.BOLD,
    }

    level_color = level_colors.get(entry["level"], "")

    # Special formatting for refinement-related messages
    message = entry["message"]

    # Highlight special refinement markers
    if "STARTING" in message or "Starting" in message:
        message = colorize(message, Colors.BOLD + Colors.GREEN)
    elif "Checking" in message or "check_element" in message:
        message = colorize(message, Colors.BLUE)
    elif "result:" in message or "Analysis" in message:
        message = colorize(message, Colors.CYAN)
    elif "cost:" in message or "tokens" in message:
        message = colorize(message, Colors.YELLOW)
    elif "ERROR" in message or "failed" in message or entry["level"] == "ERROR":
        message = colorize(message, Colors.RED)
    elif "complete" in message or "Success" in message or "READY" in message:
        message = colorize(message, Colors.GREEN)
    elif "=" in message and len(message) > 40:  # Separator lines
        message = colorize(message, Colors.BOLD)

    # Format the full line
    timestamp = colorize(entry["timestamp"], Colors.CYAN)
    module = colorize(f"[{entry['module']}]", Colors.BLUE)
    level = colorize(f"{entry['level']:>8}", level_color)
    task_part = f"[{entry['task_id']}] " if entry["task_id"] else ""

    return f"{timestamp} {module} {level} {task_part}{message}"


def tail_logs(log_file: str):
    """Tail log files and display refinement process in real-time."""

    print(colorize("QUERY REFINEMENT LOG MONITOR", Colors.BOLD + Colors.HEADER))
    print(colorize("=" * 80, Colors.BOLD))
    print(f"Monitoring: {log_file}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(colorize("=" * 80, Colors.BOLD))
    print("Waiting for log entries... (Ctrl+C to stop)")
    print()

    try:
        # Find the log file
        if not os.path.exists(log_file):
            print(colorize(f"Log file not found: {log_file}", Colors.RED))
            print("   Make sure the API is running and generating logs.")
            return

        # Open file and seek to end
        with open(log_file, "r") as f:
            # Go to end of file
            f.seek(0, 2)

            while True:
                line = f.readline()
                if line:
                    entry = parse_log_line(line)
                    if entry:
                        # Only show refinement-related logs
                        if any(
                            keyword in entry["module"].lower()
                            for keyword in ["query_refiner", "app", "refinement"]
                        ):
                            formatted = format_log_entry(entry)
                            print(formatted)

                            # Add extra spacing for major events
                            if any(
                                marker in entry["message"]
                                for marker in ["STARTING", "READY", "====="]
                            ):
                                print()
                    else:
                        # Print unformatted lines that don't match our pattern
                        if any(
                            keyword in line.lower()
                            for keyword in ["refinement", "query_refiner"]
                        ):
                            print(colorize(line.strip(), Colors.YELLOW))
                else:
                    time.sleep(0.1)

    except KeyboardInterrupt:
        print(colorize("\n\nLog monitoring stopped", Colors.YELLOW))
    except Exception as e:
        print(colorize(f"\nError: {e}", Colors.RED))


def find_latest_log():
    """Find the latest log file."""
    log_dir = "api/logs"

    if not os.path.exists(log_dir):
        print(colorize(f"Log directory not found: {log_dir}", Colors.RED))
        return None

    # Look for common log file patterns
    patterns = ["*.log", "api.log", "scholarqa.log", "app.log"]

    import glob

    for pattern in patterns:
        files = glob.glob(os.path.join(log_dir, pattern))
        if files:
            # Return the most recently modified
            return max(files, key=os.path.getmtime)

    # If no specific log files, try to find any .log files
    log_files = glob.glob(os.path.join(log_dir, "**/*.log"), recursive=True)
    if log_files:
        return max(log_files, key=os.path.getmtime)

    return None


def main():
    """Main function."""

    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = find_latest_log()
        if not log_file:
            print(colorize("No log file found", Colors.RED))
            print("Usage: python log_monitor.py [log_file_path]")
            print("\nOr start the API to generate logs automatically.")
            return

    print(f"Using log file: {log_file}")
    tail_logs(log_file)


if __name__ == "__main__":
    main()
