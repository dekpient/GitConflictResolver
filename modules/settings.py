import sublime

PLUGIN_NAME = "Git Conflict Resolver"

_settings_file = "GitConflictResolver.sublime-settings"
_subl_settings = {}
_default_settings = {
    "git_path": "git",
    "live_matching": True,
    "matching_scope": "invalid",
    "fill_conflict_area": False,
    "outline_conflict_area": True,
    "ours_gutter": False,
    "theirs_gutter": False,
    "ancestor_gutter": False,
    "show_only_filenames": True,
    "log_debug": False
}


def load():
    global _subl_settings
    _subl_settings = sublime.load_settings(_settings_file)


def get(key):
    return _subl_settings.get(key, _default_settings[key])
