import pyautogui
import random
import time
import threading
import ctypes
from datetime import datetime
from PIL import Image, ImageDraw
import pystray
from pynput import keyboard, mouse

# Local Imports
import web_tool_config as config

class WebToolWin:
    def __init__(self):
        self.should_exit = False
        self.is_paused_by_user = False
        self.is_paused_by_auto = False
        self.last_user_pos = pyautogui.position()
        self.last_activity_time = time.time()
        self.icon = None
        self.thread = None
        self.last_logged_title = ""
        self.last_bot_action_done = time.time()
        self.startup_grace_until = time.time() + 3  # Ignore input events for 3s on startup

        self.user32 = ctypes.windll.user32

        # Windows Screen Bounds
        self.v_left = self.user32.GetSystemMetrics(76)
        self.v_top = self.user32.GetSystemMetrics(77)
        self.v_width = self.user32.GetSystemMetrics(78)
        self.v_height = self.user32.GetSystemMetrics(79)
        self.log(f"Windows Multi-monitor bounds: {self.v_width}x{self.v_height} at ({self.v_left}, {self.v_top})")

        self.is_bot_moving = False
        self.current_date = datetime.now().date()

        # Setup Global Listeners
        # Setup Global Listeners
        self.keyboard_listener = keyboard.GlobalHotKeys({'<f9>': self.toggle_pause})
        self.keyboard_listener.start()

        self.activity_listener = keyboard.Listener(on_press=self.on_key_press)
        self.activity_listener.start()

        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move, on_click=self.on_mouse_click, on_scroll=self.on_mouse_scroll
        )
        self.mouse_listener.start()

    def _should_trigger_pause(self):
        """Returns True only if we're past the startup grace period and the bot isn't acting."""
        return (
            time.time() > self.startup_grace_until
            and not self.is_bot_moving
            and (time.time() - self.last_bot_action_done > 1.5)
        )

    def on_key_press(self, key):
        if self._should_trigger_pause():
            self.trigger_auto_pause()

    def on_mouse_move(self, x, y):
        if self._should_trigger_pause():
            self.trigger_auto_pause()

    def on_mouse_click(self, x, y, button, pressed):
        if self._should_trigger_pause():
            self.trigger_auto_pause()

    def on_mouse_scroll(self, x, y, dx, dy):
        if self._should_trigger_pause():
            self.trigger_auto_pause()

    def trigger_auto_pause(self):
        if not self.is_paused_by_auto:
            self.is_paused_by_auto = True
            self.log(f"Auto-Paused for {config.PAUSE_DURATION}s", "Manual interaction detected")
            self.update_tray_state("orange")
        self.last_activity_time = time.time()

    def log(self, message, action=None):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] ACTION: {action} - {message}" if action else f"[{ts}] {message}")

    def toggle_pause(self):
        if self.is_paused_by_user or self.is_paused_by_auto:
            self.resume_simulation()
        else:
            self.pause_simulation()

    def resume_simulation(self):
        self.is_paused_by_user = self.is_paused_by_auto = False
        self.startup_grace_until = time.time() + 1.5  # Ignore the F9 keypress that just resumed us
        self.log("Resuming Simulation...")
        self.update_tray_state("green")

    def pause_simulation(self):
        self.is_paused_by_user = True
        self.log("Paused Simulation.")
        self.update_tray_state("gold")

    def update_tray_state(self, color):
        if self.icon:
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
        self.keyboard_listener.stop()
        self.activity_listener.stop()
        self.mouse_listener.stop()
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
            hwnd = self.user32.GetForegroundWindow()
            length = self.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buf, length + 1)
            
            class_buf = ctypes.create_unicode_buffer(256)
            self.user32.GetClassNameW(hwnd, class_buf, 256)
            
            title = f"{buf.value} {class_buf.value}".lower()
            if title != self.last_logged_title:
                self.last_logged_title = title
                self.log(f"Active App Changed: '{title}'")
            return None, title
        except Exception: pass
        return None, ""

    def is_browser_active(self):
        _, title = self.get_active_app_info()
        return any(b in title for b in config.BROWSER_APPS)

    def is_ide_active(self):
        _, title = self.get_active_app_info()
        return any(ide in title for ide in config.IDE_APPS) if title else False

    def do_mouse_move(self):
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
            pyautogui.moveTo(tx, ty, duration=dur, tween=pyautogui.easeInOutQuad)
            self.last_user_pos = pyautogui.position()
        finally:
            self.is_bot_moving = False
            self.last_bot_action_done = time.time()

    def do_keypress(self):
        key = random.choice(['shift', 'ctrl', 'alt'])
        self.log(f"Pressing {key}", "Ghost keystroke")
        self.is_bot_moving = True
        try: pyautogui.press(key)
        finally:
            self.is_bot_moving = False
            self.last_bot_action_done = time.time()

    def is_productive_app(self, title):
        """Checks if the window title matches a known productive application."""
        title = title.lower()
        is_ide = any(app in title for app in config.IDE_APPS)
        is_browser = any(app in title for app in config.BROWSER_APPS)
        return is_ide or is_browser

    def do_app_switch(self):
        self.log("Alt+Tab", "App switch")
        self.is_bot_moving = True
        try:
            # Try to switch to a productive app (up to 5 attempts)
            for attempt in range(5):
                pyautogui.keyDown('alt')
                time.sleep(0.5)  # Increased delay to ensure OS catches it
                
                # Vary number of tabs to cycle through windows
                # Use attempt number to increase range if stuck? No, random is fine.
                for _ in range(random.randint(1, 4)):
                    pyautogui.press('tab')
                    time.sleep(random.uniform(0.2, 0.4))
                time.sleep(0.5)
                pyautogui.keyUp('alt')
                
                # Check where we landed
                time.sleep(1.0) # Wait for window to focus and title to update
                _, title = self.get_active_app_info()
                
                if self.is_productive_app(title):
                    self.log(f"Landed on productive app: '{title}'", "Smart Switch Success")
                    break
                else:
                    self.log(f"Landed on NEUTRAL app: '{title}'. Retrying...", "Smart Switch Retry")
                    time.sleep(0.5)
            else:
                 self.log("Failed to find productive app after 5 attempts.", "Smart Switch Giveup")

        finally:
            self.is_bot_moving = False
            self.last_bot_action_done = time.time()

    def do_ide_switch(self):
        self.log("Random Scroll + Return to Top + Switch", "IDE Simulation")
        self.is_bot_moving = True
        try:
            # 1. Random Scroll currently active file
            for _ in range(random.randint(2, 4)):
                pyautogui.scroll(random.randint(-500, 500))
                time.sleep(random.uniform(0.3, 0.7))

            # 2. Return to Top
            pyautogui.keyDown('ctrl'); pyautogui.press('home'); pyautogui.keyUp('ctrl')
            time.sleep(0.5)

            # 3. Switch Tabs
            presses = random.randint(1, 4)
            pyautogui.keyDown('ctrl')
            for _ in range(presses):
                pyautogui.press('tab')
                time.sleep(random.uniform(0.1, 0.3))
            pyautogui.keyUp('ctrl')
            time.sleep(0.5)

            # 4. Jump to Bottom
            pyautogui.keyDown('ctrl'); pyautogui.press('end'); pyautogui.keyUp('ctrl')
            time.sleep(0.5)
            # 5. Scroll back up multiple times to simulate reading
            for _ in range(random.randint(3, 6)):
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
                pyautogui.scroll(random.randint(-8, 8) * 100)
                time.sleep(random.uniform(0.5, 1.2))

            # 2. Return to Top
            pyautogui.press('home')
            time.sleep(0.5)

            # 3. Switch Tabs
            presses = random.randint(1, 4)
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
            if self.is_paused_by_auto and (time.time() - self.last_activity_time > config.PAUSE_DURATION):
                 self.is_paused_by_auto = False
                 self.log("Resuming (Idle timeout reached)")
                 self.update_tray_state("green")

            if not self.is_paused_by_user and not self.is_paused_by_auto:
                now = time.time()

                # 1. App Switch (Window level)
                if config.ENABLE_APP_SWITCH and now >= next_app:
                    self.do_app_switch()
                    l_app_timestamp = time.time()
                    next_app = time.time() + random.randint(*config.APP_SWITCH_INTERVAL)
                    continue

                # 2. Cooldown check - don't do other actions immediately after app switch
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
                        # Reset timer only if we actually tried to switch,
                        # otherwise try again soon (or keep same time? Let's spread it out to avoid spamming checks)
                        # Actually if not active, we still reset to avoid checking every single second effectively waiting for focus
                        # But maybe we want it to happen SOON after entering IDE.
                        # Let's say if not active, check again in 10 seconds?
                        # For now, let's just reset standard interval to behave like "every X minutes do this if in IDE"
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
        self.icon = pystray.Icon("WebToolWin", self.create_image("green"), "Web-Tool (Win): Active", menu)
        self.icon.run()

if __name__ == "__main__":
    WebToolWin().run()
