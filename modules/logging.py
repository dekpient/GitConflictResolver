from . import settings


def debug(*args):
    """Print args to the console if the "debug" setting is True."""
    if settings.get('log_debug'):
        printf(*args)


def printf(*args):
    """Print args to the console, prefixed by the plugin name."""
    print(settings.PLUGIN_NAME + ":", *args)
