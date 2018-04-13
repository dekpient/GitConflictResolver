import sublime
from . import settings


_icon_folder = "/".join([settings.PLUGIN_NAME, "gutter"])
_icons = {
    "ours": "left",
    "ancestor": "dash",
    "theirs": "right"
}


def get(group):
    base = ""
    extension = ""
    if int(sublime.version()) < 3000:
        base = "/".join(["..", _icon_folder])
    else:
        base = "/".join(["Packages", _icon_folder])
        extension = ".png"

    return "/".join([base, _icons[group] + extension])
