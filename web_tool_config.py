# --- Configuration ---
PAUSE_DURATION = 60  # Seconds to pause if manual interaction detected
LOG_FILE = "web_tool.log"

# Intervals (min, max) in seconds
MOVE_INTERVAL = (2, 5)
TYPING_INTERVAL = (8, 15)
APP_SWITCH_INTERVAL = (10, 25)  # Stay in apps less time to ensure frequent switching
IDE_SWITCH_INTERVAL = (5, 12)  # Switch internal tabs faster
BROWSER_SWITCH_INTERVAL = (5, 12)

# Feature Toggles
ENABLE_MOUSE = True
ENABLE_KEYS = True
ENABLE_APP_SWITCH = True
ENABLE_IDE_SWITCH = True
ENABLE_BROWSER_SWITCH = True

# App Awareness
IDE_APPS = [
    'code', 'vscode', 'visual studio code', 'pycharm', 'intellij', 'webstorm',
    'phpstorm', 'sublime', 'atom', 'vim', 'emacs', 'neovim', 'eclipse',
    'netbeans', 'android studio', 'xcode', 'cursor', 'antigravity'
]

BROWSER_APPS = [
    'google chrome', 'chrome', 'safari', 'firefox', 'microsoft edge', 'edge',
    'msedge', 'brave', 'arc', 'opera'
]
