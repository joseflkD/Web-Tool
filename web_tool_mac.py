import pyautogui
import random
import time
import threading
from datetime import datetime
from PIL import Image, ImageDraw
import pystray
from pynput import keyboard, mouse
from AppKit import NSWorkspace
import Quartz

# Local Imports
import web_tool_config as config

class WebToolMac:
    def __init__(self):
        self.should_exit = False
        self.is_paused_by_user = False
        self.is_paused_by_auto = False
        self.mac_api_lock = threading.Lock()
        with self.mac_api_lock:
            self.last_user_pos = pyautogui.position()
        self.last_activity_time = time.time()
        self.icon = None
        self.thread = None
        self.last_logged_app = ""
        self.last_logged_title = ""

        # Mac Screen Bounds
        with self.mac_api_lock:
            w, h = pyautogui.size()
        self.v_left, self.v_top, self.v_width, self.v_height = 0, 0, w, h
        self.log(f"macOS Screen bounds set: {self.v_width}x{self.v_height}")

        self.is_bot_moving = False
        self.last_bot_action_done = time.time()
        self.current_date = datetime.now().date()

        # Setup Global Hotkey Listener
        # We wrap the hotkey start and callbacks in the lock to be safe.
        with self.mac_api_lock:
            self.keyboard_listener = keyboard.GlobalHotKeys({
                '<f9>': self.toggle_pause,
                '<cmd>+<alt>+p': self.toggle_pause
            })
            self.log("Starting Keyboard listener (F9 or Cmd+Alt+P)...")
            self.keyboard_listener.start()

    # Removed: Standard pynput listeners for on_key_press, etc.
    # Using Quartz polling in simulation_loop instead to minimize threads.

    def trigger_auto_pause(self):
        with self.mac_api_lock:
            if not self.is_paused_by_auto:
                self.is_paused_by_auto = True
                self.log(f"Auto-Paused for {config.PAUSE_DURATION}s", "Manual interaction detected")
                self.update_tray_state("orange")
            self.last_activity_time = time.time()

    def log(self, message, action=None):
        ts = datetime.now().strftime("%H:%M:%S")
        msg = f"[{ts}] ACTION: {action} - {message}" if action else f"[{ts}] {message}"
        print(msg)

    def toggle_pause(self):
        with self.mac_api_lock:
            if self.is_paused_by_user or self.is_paused_by_auto:
                self.resume_simulation()
            else:
                self.pause_simulation()

    def resume_simulation(self):
        self.is_paused_by_user = self.is_paused_by_auto = False
        self.log("Resuming Simulation...")
        self.update_tray_state("green")

    def pause_simulation(self):
        with self.mac_api_lock:
            self.is_paused_by_user = True
            self.log("Paused Simulation.")
            self.update_tray_state("gold")

    def update_tray_state(self, color):
        if self.icon:
            # Updating icon.icon and icon.title can trigger TIS calls
            with self.mac_api_lock:
                self.icon.icon = self.create_image(color)
                if self.is_paused_by_user: self.icon.title = "Web-Tool: Paused (User)"
                elif self.is_paused_by_auto: self.icon.title = "Web-Tool: Auto-Paused"
                else: self.icon.title = "Web-Tool: Active"

    def create_image(self, color):
        image = Image.new('RGB', (64, 64), (255, 255, 255))
        ImageDraw.Draw(image).ellipse((8, 8, 56, 56), fill=color)
        return image

    def quit_app(self, icon, item):
        self.log("Exiting...")
        self.should_exit = True
        self.is_bot_moving = True
        with self.mac_api_lock:
            self.keyboard_listener.stop()
            icon.stop()

    def check_log_rotation(self):
        """Truncates the log file if the day has changed."""
        now_date = datetime.now().date()
        if now_date > self.current_date:
            try:
                with open(config.LOG_FILE, 'w') as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d')}] --- Log cleared for new day ---\n")
                self.current_date = now_date
                self.log("Daily log rotation performed.")
            except Exception as e:
                self.log(f"Failed to rotate log: {e}")

    def get_active_app_info(self):
        try:
            with self.mac_api_lock:
                active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
                if active_app:
                    app_name = active_app.localizedName().lower()
                    window_list = Quartz.CGWindowListCopyWindowInfo(
                        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
                        Quartz.kCGNullWindowID
                    )
                    title = ""
                    for window in window_list:
                        if window.get('kCGWindowLayer', 0) == 0:
                            if window.get('kCGWindowOwnerName', '').lower() == app_name:
                                title = window.get('kCGWindowName', '').lower()
                                break
                    if app_name != self.last_logged_app or title != self.last_logged_title:
                        self.last_logged_app = app_name
                        self.last_logged_title = title
                        self.log(f"Active App Changed: '{app_name}' - '{title}'")
                    return app_name, title
        except Exception: pass
        return None, ""

    def is_browser_active(self):
        app, title = self.get_active_app_info()
        return (app and any(b in app for b in config.BROWSER_APPS)) or any(b in title for b in config.BROWSER_APPS)

    def is_ide_active(self):
        app, title = self.get_active_app_info()
        return (app and any(ide in app for ide in config.IDE_APPS)) or any(ide in title for ide in config.IDE_APPS)

    def do_mouse_move(self):
        with self.mac_api_lock:
            cur_x, cur_y = pyautogui.position()
        if random.random() > 0.3:
            dx, dy = random.randint(-50, 50), random.randint(-50, 50)
            tx = max(self.v_left, min(self.v_left + self.v_width, cur_x + dx))
            ty = max(self.v_top, min(self.v_top + self.v_height, cur_y + dy))
            act, dur = "Micro-jiggle", random.uniform(0.3, 0.8)
        else:
            tx = random.randint(self.v_left + 100, self.v_left + self.v_width - 100)
            ty = random.randint(self.v_top + 100, self.v_top + self.v_height - 100)
            act, dur = "Natural move", random.uniform(1.2, 2.5)

        self.log(f"To ({tx}, {ty})", act)
        self.is_bot_moving = True
        try:
            with self.mac_api_lock:
                pyautogui.moveTo(tx, ty, duration=dur, tween=pyautogui.easeInOutQuad)
                self.last_user_pos = pyautogui.position()
        finally:
            self.is_bot_moving = False
            self.last_bot_action_done = time.time()

    def do_keypress(self):
        key = random.choice(['shift', 'ctrl', 'alt'])
        self.log(f"Pressing {key}", "Ghost keystroke")
        self.is_bot_moving = True
        try:
            with self.mac_api_lock:
                pyautogui.press(key)
        finally:
            self.is_bot_moving = False
            self.last_bot_action_done = time.time()

    def do_app_switch(self):
        self.log("Command+Tab", "App switch")
        self.is_bot_moving = True
        try:
            with self.mac_api_lock:
                pyautogui.keyDown('command')
                time.sleep(0.5)
                for _ in range(random.randint(1, 4)):
                    pyautogui.press('tab')
                    time.sleep(random.uniform(0.2, 0.4))
                time.sleep(0.5)
                pyautogui.keyUp('command')
        finally:
            self.is_bot_moving = False
            self.last_bot_action_done = time.time()

    def do_ide_switch(self):
        self.log("Random Scroll + Return to Top + Switch", "IDE Simulation")
        self.is_bot_moving = True
        try:
            # 1. Random Scroll currently active file
            for _ in range(random.randint(2, 4)):
                with self.mac_api_lock:
                    pyautogui.scroll(random.randint(-500, 500))
                time.sleep(random.uniform(0.3, 0.7))

            # 2. Return to Top
            with self.mac_api_lock:
                pyautogui.keyDown('command'); pyautogui.press('up'); pyautogui.keyUp('command')
            time.sleep(0.5)

            # 3. Switch Tabs
            presses = random.randint(1, 4)
            with self.mac_api_lock:
                pyautogui.keyDown('ctrl')
                for _ in range(presses):
                    pyautogui.press('tab')
                    time.sleep(random.uniform(0.1, 0.3))
                pyautogui.keyUp('ctrl')
            time.sleep(0.5)

            # 4. Jump to Bottom of new file
            with self.mac_api_lock:
                pyautogui.keyDown('command'); pyautogui.press('down'); pyautogui.keyUp('command')
            time.sleep(0.5)

            # 5. Scroll back up multiple times to simulate reading
            for _ in range(random.randint(3, 6)):
                with self.mac_api_lock:
                    pyautogui.scroll(random.randint(300, 600))
                time.sleep(random.uniform(0.2, 0.5))
        finally:
            self.is_bot_moving = False
            self.last_bot_action_done = time.time()

    def do_browser_switch(self):
        self.log("Random Scroll + Return to Top + Switch", "Browser Simulation")
        self.is_bot_moving = True
        try:
            # 1. Random Scroll current page
            for _ in range(random.randint(2, 4)):
                with self.mac_api_lock:
                    pyautogui.scroll(random.randint(-8, 8) * 100)
                time.sleep(random.uniform(0.5, 1.2))

            # 2. Return to Top
            with self.mac_api_lock:
                pyautogui.keyDown('command'); pyautogui.press('up'); pyautogui.keyUp('command')
            time.sleep(0.5)

            # 3. Switch Tabs
            presses = random.randint(1, 4)
            with self.mac_api_lock:
                pyautogui.keyDown('ctrl')
                for _ in range(presses):
                    pyautogui.press('tab')
                    time.sleep(random.uniform(0.1, 0.3))
                pyautogui.keyUp('ctrl')
            time.sleep(0.5)
        finally:
            self.is_bot_moving = False
            self.last_bot_action_done = time.time()

    def simulation_loop(self):
        # Initialize next run times
        now = time.time()
        next_app = now + random.randint(*config.APP_SWITCH_INTERVAL)
        next_move = now + random.randint(*config.MOVE_INTERVAL)
        next_type = now + random.randint(*config.TYPING_INTERVAL)
        next_ide = now + random.randint(*config.IDE_SWITCH_INTERVAL)
        next_browser = now + random.randint(*config.BROWSER_SWITCH_INTERVAL)

        l_app_timestamp = 0
        cooldown = 5

        while not self.should_exit:
            self.check_log_rotation()

            # Poll Quartz for system-wide idle time
            with self.mac_api_lock:
                idle_sec = Quartz.CGEventSourceSecondsSinceLastEventType(
                    Quartz.kCGEventSourceStateCombinedSessionState, Quartz.kCGAnyInputEventType
                )

            # If manual interaction detected (within last 0.5s)
            # AND it's been more than 1.5s since our last bot action (grace period)
            if not self.is_bot_moving and idle_sec < 0.5:
                if time.time() - self.last_bot_action_done > 1.5:
                    self.trigger_auto_pause()

            with self.mac_api_lock:
                if self.is_paused_by_auto and (time.time() - self.last_activity_time > config.PAUSE_DURATION):
                     self.is_paused_by_auto = False
                     self.log("Resuming (Idle timeout reached)")
                     self.update_tray_state("green")

            with self.mac_api_lock:
                should_run = not self.is_paused_by_user and not self.is_paused_by_auto

            if should_run:
                now = time.time()

                # 1. App Switch (Window level)
                if config.ENABLE_APP_SWITCH and now >= next_app:
                    self.do_app_switch()
                    l_app_timestamp = time.time()
                    next_app = time.time() + random.randint(*config.APP_SWITCH_INTERVAL)
                    continue

                # 2. Cooldown check
                if now - l_app_timestamp < cooldown:
                    time.sleep(1)
                    continue

                # 3. Mouse Movement
                if config.ENABLE_MOUSE and now >= next_move:
                    self.do_mouse_move()
                    next_move = time.time() + random.randint(*config.MOVE_INTERVAL)

                # 4. Keypresses
                if config.ENABLE_KEYS and now >= next_type:
                    self.do_keypress()
                    next_type = time.time() + random.randint(*config.TYPING_INTERVAL)

                # 5. IDE Simulation (Internal Tabs)
                if config.ENABLE_IDE_SWITCH and now >= next_ide:
                    if self.is_ide_active():
                        self.do_ide_switch()
                    next_ide = time.time() + random.randint(*config.IDE_SWITCH_INTERVAL)

                # 6. Browser Simulation (Internal Tabs)
                if config.ENABLE_BROWSER_SWITCH and now >= next_browser:
                    if self.is_browser_active():
                        self.do_browser_switch()
                    next_browser = time.time() + random.randint(*config.BROWSER_SWITCH_INTERVAL)

            time.sleep(1)

    def run(self):
        threading.Thread(target=self.simulation_loop, daemon=True).start()
        menu = pystray.Menu(pystray.MenuItem("Toggle Pause (F9)", self.toggle_pause), pystray.MenuItem("Quit", self.quit_app))
        self.icon = pystray.Icon("WebToolMac", self.create_image("green"), "Web-Tool (Mac): Active", menu)
        self.icon.run()

if __name__ == "__main__":
    WebToolMac().run()
