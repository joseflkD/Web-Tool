# Web-Tool Simulation Script

A human-like activity simulator designed to prevent computer systems from entering an "idle" state. It mimics real work behavior through randomized mouse movements, keystrokes, and intelligent application interactions tailored for macOS and Windows.

> [!WARNING]
> This tool is intended for personal use, such as preventing system timeouts during long-running tasks. Using automation to mislead monitoring software may violate company policies and carries professional risks.

## Key Features

- **OS-Specific Precision**: Two distinct versions (`_mac.py` and `_win.py`) use native APIs (Quartz on Mac, Win32 on Windows) for exact window and screen detection.
- **Smart Auto-Pause**: Instantly detects manual mouse movements or typing and pauses for 60 seconds (configurable). Includes a **1.5s Grace Period** after bot actions to prevent false triggers.
- **Realistic "Reading" Simulation**:
    - **IDE (VS Code, Cursor, etc.)**: Switches tabs, jumps to the bottom, and performs multiple upward scrolls to simulate reading/reviewing code. (Supports `antigravity` as an IDE).
    - **Browsers**: Performs random scrolling and returns to the top before switching tabs.
- **Advanced Navigation**: Randomly switches through 1–4 tabs or recent applications using `Command+Tab` (Mac) or `Alt+Tab` (Win).
- **Daily Log Rotation**: Automatically clears and restarts the `web_tool.log` file at the start of each new day.
- **Centralized Config**: Manage all timings, app lists, and feature toggles in one shared `web_tool_config.py` file.

## Prerequisites

- **Python 3.x**
- **PyAutoGUI, pynput, pystray, Pillow**: Essential for simulation and tray interface.
- **macOS only**: Requires `pyobjc-framework-Quartz` and `pyobjc-framework-AppKit`.

## Installation

### 1. Clone & Setup
```bash
git clone https://github.com/Jay-Dee0/Web-Tool.git
cd Web-Tool
python3 -m venv venv
```

### 2. Activate Environment
- **Mac:** `source venv/bin/activate`
- **Windows:** `.\venv\Scripts\activate`

> [!IMPORTANT]
> **macOS Permissions**: Since this script simulates mouse and keyboard input, you MUST grant your Terminal (or IDE) **Accessibility** permissions.
> 1. Go to **System Settings** > **Privacy & Security** > **Accessibility**.
> 2. Add and enable your terminal (e.g., Terminal.app, iTerm2) or Python.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### 🚀 Easy Launch
- **macOS:** Run `./run_web_tool.sh`. It runs in the background and logs to `web_tool.log`.
- **Windows:** Double-click `run_web_tool.bat`.

### ⚙️ Configuration
Open **[web_tool_config.py](web_tool_config.py)** to customize:
- **Intervals**: How often to move the mouse, type, or switch apps.
- **App Lists**: Which apps should be treated as IDEs (includes `antigravity`) or Browsers.
- **Feature Toggles**: Enable/disable specific behaviors like mouse movement or app switching.

### 🎮 Controls
- **F9 Hotkey**: Global toggle to Pause/Resume simulation.
- **Tray Icon**: 🟢 Green (Active), 🟠 Orange (Auto-Paused), 🟡 Gold (Manual Pause).
- **Logs**: View activity in real-time with `tail -f web_tool.log`.

## Safety & Failsafes
- **Grace Period**: Logic prevents the script from pausing itself immediately after performing an automated action.
- **Auto-Pause**: The script yields control immediately if it detects user activity.
- **Manual Toggle**: Use **F9** or the Tray menu for instant stops.
- **Background Execution**: Launchers are designed to keep your terminal clean while providing easy PID management for manual stops.
