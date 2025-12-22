import subprocess

from loguru import logger
from pynput import keyboard

from modules.common import HotkeyCombination


def focus_chrome_tab_and_element(title='qwen', css_selector='#chat-input'):
    script = f'''
    tell application "Google Chrome"
        activate
        set found to false
        repeat with w in every window
            set tab_list to every tab of w
            repeat with i from 1 to (count of tab_list)
                set t to item i of tab_list
                if (title of t contains "{title}") or (URL of t contains "{title}") then
                    set active tab index of w to i
                    set index of w to 1
                    execute t javascript "(() => {{
                        const el = document.querySelector('{css_selector}');
                        if (el) {{
                            el.focus();
                            el.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                            return 'Focused {css_selector}';
                        }} else {{
                            return 'Element {css_selector} not found';
                        }}
                    }})();"
                    set found to true
                    return "Tab activated and JS executed"
                end if
            end repeat
        end repeat
        if not found then return "No tab with '{title}' found"
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger.error(e.stderr.strip())


def init_listener(hotkey_combination: HotkeyCombination):
    hotkey_combination = hotkey_combination.mac
    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse(hotkey_combination),
        focus_chrome_tab_and_element
    )
    def _for_canonical(f):
        return lambda k: f(l.canonical(k))
    logger.info(f'Use hotkey combination: {hotkey_combination}')
    with keyboard.Listener(
        on_press=_for_canonical(hotkey.press),
        on_release=_for_canonical(hotkey.release)
    ) as l:
        try:
            l.join()
        except KeyboardInterrupt:
            logger.info("🛑 Exiting...")
