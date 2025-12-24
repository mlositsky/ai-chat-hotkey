import datetime
import socket
from time import sleep

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from pywinauto import Application, Desktop
import keyboard
import os
import subprocess
import psutil
from loguru import logger

from modules.common import HotkeyCombination

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

class Listener:
    def __init__(self, chat_title: str, target_url: str, input_field_selector: str, hotkey_combination: str, debug_port: int):
        self.hotkey_combination = HotkeyCombination(hotkey_combination)
        self.target_url = target_url
        self.input_field_selector = input_field_selector
        self.chat_title =chat_title
        self.app = None
        self.driver = None
        self.user_data_dir = f"C:\\temp\\{chat_title}"
        self.debug_port = debug_port

        self.init_listener()

    def init_listener(self):
        try:
            if not self.is_chrome_debug_running():
                self.launch_chrome()
            self.init_chrome()
            self.background_listener()  # or however your app runs
        except KeyboardInterrupt:
            logger.info("🛑 Hotkey listener stopped.")
        except SystemExit:
            pass  # Allow sys.exit() to work normally
        except Exception as e:
            import traceback

            logger.info("--- FATAL ERROR ---")
            traceback.print_exc()

        # Keep console open after running
        input("Press ENTER to exit...")
        exit(0)

    def is_port_open(self, host='127.0.0.1', timeout=3):
        """Check if Chrome remote debugging port is open"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, self.debug_port)) == 0

    def init_chrome(self,):
        # Check if Chrome debug port is open
        if not self.is_port_open():
            logger.error(f"❌ Chrome is not running with --remote-debugging-port={self.debug_port}")
            raise

        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")

        logger.info("Connecting to Chrome...")
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            logger.error(f"Failed to connect to Chrome: {e}")
            logger.error(f"Make sure ONLY ONE Chrome instance is using port {self.debug_port}")
            return
        desktop = Desktop(backend="uia")

        for w in desktop.windows():
            logger.debug(f"Check if '{self.chat_title}' in '{w.window_text()}'")
            if self.chat_title in w.window_text().lower():
                self.app = Application(backend="uia").connect(
                    process=w.process_id(),
                    timeout=10
                )
                logger.info(f"Window set to '{w.window_text()}' pid: {w.process_id()}")
                break
        self.driver = driver
        return

    def focus_chrome_and_chat(self):

        logger.info(f"Connected! Searching for {self.chat_title} Chat tab...")
        chat_tab = None
        try:
            handles=self.driver.window_handles
        except selenium.common.exceptions.InvalidSessionIdException: # noqa
            self.launch_chrome()
            sleep(6)
            self.init_chrome()
            handles=self.driver.window_handles
        try:
            for handle in handles:
                self.driver.switch_to.window(handle)
                current_url = self.driver.current_url
                logger.debug(f"{current_url=}")
                if self.target_url in current_url.lower():
                    chat_tab = handle
                    logger.info(f"Found {self.chat_title} tab")
                    start_ = datetime.datetime.now()
                    break
        except Exception as e:
            raise e
        if not chat_tab:
            logger.info(f"💬 {self.chat_title} tab not found. Opening a new one...")
            self.driver.execute_script(f"window.open('{self.target_url}', '_blank');")
            sleep(2)  # Allow time for the new tab to load

            # Refresh window handles and find the new tab
            new_handles = self.driver.window_handles
            for handle in new_handles:
                if handle not in handles:  # This is the newly opened tab
                    self.driver.switch_to.window(handle)
                    chat_tab = handle
                    logger.info(f"✅ Opened and switched to new {self.chat_title} tab")
                    break

        self.driver.switch_to.window(chat_tab)

        # Focus Chrome window
        try:
            window = self.app.top_window()
            window.set_focus()
            logger.debug(f"✅ Focused")
        except Exception as e:
            logger.error(f"⚠️ Could not focus window: {e}")

        # Focus input field
        try:
            wait = WebDriverWait(self.driver, 8)
            selectors = [
                self.input_field_selector,
            ]

            input_el = None
            for sel in selectors:
                try:
                    el = wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                    if el.is_displayed() and el.is_enabled():
                        input_el = el
                        break
                except Exception as e:
                    logger.error(f"Error focusing input: {e}")
                    continue

            if input_el:
                self.driver.execute_script("arguments[0].focus();", input_el)
                logger.info(f"✅ Focused on {self.chat_title} input field!")
            else:
                exit(1)
        except Exception as e:
            logger.error(f"Error focusing input: {e}")



    def on_hotkey(self):
        logger.info(f"🟢 {self.hotkey_combination} detected!")

        self.focus_chrome_and_chat()

    def background_listener(self):
        """Run the hotkey listener in background"""
        logger.info(f"👂 Listening for {self.hotkey_combination} (press Ctrl+C to stop)...")
        # Register global hotkey
        keyboard.add_hotkey(self.hotkey_combination.win, self.on_hotkey)
        # Keep the script alive
        keyboard.wait()  # Blocks until Ctrl+C or exit


    def is_chrome_debug_running(self):
        """Check if Chrome is already running with matching debug port and user-data-dir"""
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if not cmdline or 'chrome' not in cmdline[0].lower():
                    continue

                # Check for required flags
                if f'--remote-debugging-port={self.debug_port}' in cmdline and f'--user-data-dir={self.user_data_dir}' in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False


    def launch_chrome(self):
        cmd = [
            CHROME_PATH,
            f"--remote-debugging-port={self.debug_port}",
            f"--user-data-dir={self.user_data_dir}",
            self.target_url
        ]

        # Ensure the user data dir exists
        os.makedirs(self.user_data_dir, exist_ok=True)

        logger.info("Launching Chrome for AI Chat with remote debugging...")
        try:
            # Start process without blocking (detach)
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP)
            logger.info("✅ Chrome launched successfully!")
        except FileNotFoundError:
            logger.error(f"❌ Chrome not found at: {CHROME_PATH}")
            logger.error("Please verify your Chrome installation path.")
        except Exception as e:
            logger.error(f"❌ Failed to launch Chrome: {e}")
