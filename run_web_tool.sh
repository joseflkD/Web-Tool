#!/bin/bash


# Ensure we are in the script's directory
cd "$(dirname "$0")" || exit

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run installation steps first."
    exit 1
fi

# Activate venv and run script in background
source venv/bin/activate
nohup python -u web_tool_mac.py >> web_tool.log 2>&1 &
echo "Web-Tool started in background. Logs: web_tool.log"
echo "PID: $!"
