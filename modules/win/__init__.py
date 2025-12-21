import datetime
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pywinauto import Application
import keyboard
import os
import subprocess
import psutil

def is_port_open(host='127.0.0.1', port=9222, timeout=3):
    """Check if Chrome remote debugging port is open"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0

def init_chrome():
    # Check if Chrome debug port is open
    if not is_port_open():
        print("❌ Chrome is not running with --remote-debugging-port=9222")
        print("Start Chrome using:")
        print('chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\temp\\chrome_qwen"')
        return

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    print("Connecting to Chrome...")
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Failed to connect to Chrome: {e}")
        print("Make sure ONLY ONE Chrome instance is using port 9222")
        return

    app = Application(backend="uia").connect(
        title_re=f".*{driver.title}.*Chrome",
        timeout=10
    )
    return app, driver

def focus_chrome_and_qwen(app, driver):

    print("Connected! Searching for Qwen Chat tab...")
    start_ = None
    qwen_tab = None
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        title = driver.title
        print(f"{title=}")
        if "qwen" in title.lower() or "通义千问" in title or "Qwen" in title:
            qwen_tab = handle
            print(f"Found Qwen tab: {title}")
            start_ = datetime.datetime.now()
            break

    if not qwen_tab:
        print("❌ Qwen Chat tab not found!")
        driver.quit()
        return

    driver.switch_to.window(qwen_tab)

    # Focus Chrome window
    try:
        print(f"✅ init webd  {datetime.datetime.now() - start_}")

        print(f"✅ done {datetime.datetime.now() - start_}")

        window = app.top_window()
        print(f"✅ done {datetime.datetime.now() - start_}")

        window.set_focus()
        print(f"✅ done {datetime.datetime.now() - start_}")
    except Exception as e:
        print(f"⚠️ Could not focus window: {e}")

    # Focus input field
    try:
        wait = WebDriverWait(driver, 8)
        # Updated selectors for Qwen Chat (as of 2025)
        selectors = [
            "#chat-input",
        ]

        input_el = None
        for sel in selectors:
            try:
                el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                if el.is_displayed() and el.is_enabled():
                    input_el = el
                    break
            except Exception as e:
                print(f"Error focusing input: {e}")
                continue

        if input_el:
            driver.execute_script("arguments[0].focus();", input_el)
            end_ = datetime.datetime.now()
            print(f"✅ Focused on Qwen input field! {end_ - start_}")
        else:
            exit(1)
    except Exception as e:
        print(f"Error focusing input: {e}")



def on_ctrl_space(app, driver):
    """Callback function when Ctrl+Space is pressed"""
    print("\n🟢 Ctrl+Space detected!")

    focus_chrome_and_qwen(app, driver)
    # Add your logic here:
    # - Bring Chrome to front
    # - Type text
    # - Launch an app
    # - etc.

def background_listener(app, driver):
    """Run the hotkey listener in background"""
    print("👂 Listening for Ctrl+Space (press Ctrl+C to stop)...")
    # Register global hotkey
    keyboard.add_hotkey('ctrl+space', on_ctrl_space, args=(app, driver))
    # Keep the script alive
    keyboard.wait()  # Blocks until Ctrl+C or exit



CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\temp\chrome_qwen"
DEBUG_PORT = 9222
TARGET_URL = "https://chat.qwen.ai"


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
    """Launch Chrome with Qwen Chat and debugging enabled"""
    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        TARGET_URL
    ]

    # Ensure the user data dir exists
    os.makedirs(USER_DATA_DIR, exist_ok=True)

    print("Launching Chrome for Qwen Chat with remote debugging...")
    try:
        # Start process without blocking (detach)
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP)
        print("✅ Chrome launched successfully!")
    except FileNotFoundError:
        print(f"❌ Chrome not found at: {CHROME_PATH}")
        print("Please verify your Chrome installation path.")
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")

def init_listener():
    try:
        if not is_chrome_debug_running():
            launch_chrome()
        app_, driver_ = init_chrome()
        # Your main app logic here
        background_listener(app_, driver_)  # or however your app runs
    except KeyboardInterrupt:
        print("\n🛑 Hotkey listener stopped.")
    except SystemExit:
        pass  # Allow sys.exit() to work normally
    except Exception as e:
        import traceback

        print("\n--- FATAL ERROR ---")
        traceback.print_exc()

    # Keep console open after running
    input("\nPress ENTER to exit...")
    exit(0)