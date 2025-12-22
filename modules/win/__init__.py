import datetime
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from pywinauto import Application
import keyboard
import os
import subprocess
import psutil
from loguru import logger

from modules.common import HotkeyCombination


def is_port_open(host='127.0.0.1', port=9222, timeout=3):
    """Check if Chrome remote debugging port is open"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0

def init_chrome():
    # Check if Chrome debug port is open
    if not is_port_open():
        logger.error("❌ Chrome is not running with --remote-debugging-port=9222")
        return

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    logger.info("Connecting to Chrome...")
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        logger.error(f"Failed to connect to Chrome: {e}")
        logger.error("Make sure ONLY ONE Chrome instance is using port 9222")
        return

    app = Application(backend="uia").connect(
        title_re=f".*{driver.title}.*Chrome",
        timeout=10
    )
    return app, driver

def focus_chrome_and_chat(app, driver, chat_title):

    logger.info(f"Connected! Searching for {chat_title} Chat tab...")
    start_ = None
    chat_tab = None
    try:
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            title = driver.title
            logger.debug(f"{title=}")
            if chat_title in title.lower():
                chat_tab = handle
                logger.info(f"Found {chat_title} tab: {title}")
                start_ = datetime.datetime.now()
                break
    except Exception as e:
        raise e
    if not chat_tab:
        logger.error(f"❌ {chat_title} Chat tab not found!")
        return

    driver.switch_to.window(chat_tab)

    # Focus Chrome window
    try:
        logger.debug(f"✅ init webd  {datetime.datetime.now() - start_}")

        logger.debug(f"✅ done {datetime.datetime.now() - start_}")

        window = app.top_window()
        logger.debug(f"✅ done {datetime.datetime.now() - start_}")

        window.set_focus()
        logger.debug(f"✅ done {datetime.datetime.now() - start_}")
    except Exception as e:
        logger.error(f"⚠️ Could not focus window: {e}")

    # Focus input field
    try:
        wait = WebDriverWait(driver, 8)
        selectors = [
            "#prompt-textarea > p",
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
            driver.execute_script("arguments[0].focus();", input_el)
            end_ = datetime.datetime.now()
            logger.info(f"✅ Focused on {chat_title} input field! {end_ - start_}")
        else:
            exit(1)
    except Exception as e:
        logger.error(f"Error focusing input: {e}")



def on_hotkey(app, driver, hotkey_combination: HotkeyCombination):
    logger.info(f"🟢 {hotkey_combination} detected!")

    focus_chrome_and_chat(app, driver, 'chatgpt' )
    # Add your logic here:
    # - Bring Chrome to front
    # - Type text
    # - Launch an app
    # - etc.

def background_listener(app, driver, hotkey_combination: HotkeyCombination):
    """Run the hotkey listener in background"""
    logger.info(f"👂 Listening for {hotkey_combination} (press Ctrl+C to stop)...")
    # Register global hotkey
    keyboard.add_hotkey(hotkey_combination.win, on_hotkey, args=(app, driver, hotkey_combination))
    # Keep the script alive
    keyboard.wait()  # Blocks until Ctrl+C or exit



CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\temp\ai-chat-hotkey"
DEBUG_PORT = 9222
# TARGET_URL = "https://chat.qwen.ai"
TARGET_URL = "https://chatgpt.com"


def is_chrome_debug_running():
    """Check if Chrome is already running with matching debug port and user-data-dir"""
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if not cmdline or 'chrome' not in cmdline[0].lower():
                continue

            # Check for required flags
            if f'--remote-debugging-port={DEBUG_PORT}' in cmdline and f'--user-data-dir={USER_DATA_DIR}' in cmdline:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def launch_chrome():
    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        TARGET_URL
    ]

    # Ensure the user data dir exists
    os.makedirs(USER_DATA_DIR, exist_ok=True)

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

def init_listener(hotkey_combination: HotkeyCombination):
    try:
        if not is_chrome_debug_running():
            launch_chrome()
        app_, driver_ = init_chrome()
        # Your main app logic here
        background_listener(app_, driver_, hotkey_combination)  # or however your app runs
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