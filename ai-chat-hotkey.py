#!/usr/bin/env python
import os
import platform
from pathlib import Path

from loguru import logger
from yaml import safe_load
from modules.common import HotkeyCombination

system = platform.system()
if system == "Darwin":
    print("macOS detected")
    hotkey_combination = HotkeyCombination('alt+space')
    from modules.mac import init_listener
    init_listener(hotkey_combination)
elif system == "Windows":
    print("Windows detected")
    from modules.win import Listener
else:
    print(f"Other: {system}")
    exit()



import click

def load_config(logging=False):
    config_path = os.getenv("AI_CHAT_HOTKEYS_CONFIG", default=Path(os.getenv("HOME")) / ".config" / "ai-chat-hotkeys.yaml")
    if logging:
        logger.info(f"Loading config from {config_path.as_posix()}")
    if not Path(config_path).is_file():
        default_config_path = Path(os.path.abspath(__file__)).parent / "default-ai-chat-hotkeys.yaml"
        if logging:
            logger.warning(f"User config file not found!")
            logger.warning(f"Using defaults: {default_config_path.absolute().as_posix()}")
        config_path = default_config_path

    with open(config_path,'r') as config_file:
        return safe_load(config_file)

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    Dynamically generated commands from config.yaml
    """
    if ctx.invoked_subcommand is None:
        cfg = load_config(True)
        websites = cfg.get("websites", [])

        if not websites:
            raise click.ClickException("No websites defined in config")

        default_cmd = websites[0]["chat-title"]
        ctx.invoke(cli.commands[default_cmd])



def make_command(site_config: dict):
    @click.command(name=site_config["chat-title"])
    def _cmd():
        click.echo(f"Opening: {site_config['chat-title']}")
        click.echo(f"URL: {site_config['target-url']}")
        click.echo(f"Input selector: {site_config['input-field-selector']}")
        click.echo(f"Hotkey: {site_config['hotkey-combination']}")
        Listener(
            hotkey_combination=site_config['hotkey-combination'],
            chat_title=site_config['chat-title'],
            target_url=site_config['target-url'],
            input_field_selector=site_config['input-field-selector'],
        )

    return _cmd


def register_commands():
    cfg = load_config()
    for site in cfg.get("websites", []):
        cli.add_command(make_command(site))


register_commands()

if __name__ == "__main__":
    cli()
