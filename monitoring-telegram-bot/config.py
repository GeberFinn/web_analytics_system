import importlib
import os
import sys


def load_config():
    config_name = os.environ.get("TG_CONF")
    if config_name is None:
        config_name = "development"

    try:
        config = importlib.import_module(f"settings.{config_name}")
        print(f"Config '{config_name}' loaded successfully")
    except (TypeError, ValueError, ImportError):
        print(f"Invalid config '{config_name}'")
        sys.exit(1)

    return config
