import sublime
import sublime_plugin
import os
import itertools

_st_version = int(sublime.version())
if _st_version < 3000:
    from modules import conflict
    from modules import drawing_flags as draw
    from modules import git_mixin
    from modules import icons
    from modules import messages as msgs
    from modules import settings
else:
    from .modules import conflict
    from .modules import drawing_flags as draw
    from .modules import git_mixin
    from .modules import icons
    from .modules import messages as msgs
    from .modules import settings


def plugin_loaded():
    settings.load()


def find_conflict(view, begin=0):
    line_regions = view.lines(sublime.Region(begin, view.size()))
    conflict_region = conflict.find(view, line_regions)

    if not conflict_region:
        line_regions = view.lines(sublime.Region(0, view.size()))
        conflict_region = conflict.find(view, line_regions)
        if not conflict_region:
            sublime.status_message(msgs.get('no_conflict_found'))
            return None

    return conflict_region


def draw_gutter(view, conflict_regions):
    for group in ('ours', 'ancestor', 'theirs'):
        scope = group + '_gutter'

        if not settings.get(scope):
            return

        attribute = group + '_regions'
        highlight_regions = list(itertools.chain.from_iterable(
                                 map(lambda region: getattr(region, attribute),
                                     conflict_regions)))

        view.add_regions(
            "GitConflictRegions_" + group,
            highlight_regions,
            settings.get('matching_scope'),
            icons.get(group),
            draw.hidden()
        )


def highlight_conflicts(view):
    clear_highlight_and_gutter(view)

    line_regions = view.lines(sublime.Region(0, view.size()))
    conflict_regions = conflict.find_all(view, line_regions)

    if not conflict_regions:
        return

    view.add_regions(
        "GitConflictRegions",
        list(map(lambda region: region.whole_region, conflict_regions)),
        settings.get('matching_scope'),
        "",
        draw.visible()
    )

    draw_gutter(view, conflict_regions)


def clear_highlight_and_gutter(view):
    view.erase_regions("GitConflictRegions")
    for group in ('ours', 'ancestor', 'theirs'):
        view.erase_regions("GitConflictRegion_" + group)


class FindNextConflict(sublime_plugin.TextCommand):
    def run(self, edit):
        # Reload settings
        settings.load()

        current_selection = self.view.sel()

        # Use the end of the current selection for the search,
        # or use 0 if nothing is selected
        begin = 0
        if len(current_selection) > 0:
            begin = self.view.sel()[-1].end()

        conflict_region = find_conflict(self.view, begin).whole_region
        if conflict_region is None:
            return

        # Add the region to the selection
        self.view.show_at_center(conflict_region)
        current_selection.clear()
        current_selection.add(conflict_region)


class Keep(sublime_plugin.TextCommand):
    def run(self, edit, keep):
        # Reload settings
        settings.load()

        current_selection = self.view.sel()

        # Use the begin of the current selection for the search,
        # or use 0 if nothing is selected
        begin = 0
        if len(current_selection) > 0:
            begin = current_selection[0].begin()

        conflict_region = find_conflict(self.view, begin)
        if conflict_region is None:
            return

        keep_function = getattr(conflict_region, 'get_' + keep)
        replace_text = keep_function(self.view.line_endings())

        if not replace_text:
            replace_text = ""

        self.view.replace(edit, conflict_region.whole_region, replace_text)


class ListConflictFiles(sublime_plugin.WindowCommand, git_mixin.GitMixin):
    def run(self):
        # Reload settings
        settings.load()

        # Ensure git executable is available
        if not self.git_executable_available():
            sublime.error_message(msgs.get('git_executable_not_found'))
            return

        self.git_repo = self.determine_git_repo()
        if not self.git_repo:
            sublime.status_message(msgs.get('no_git_repo_found'))
            return

        conflict_files = self.get_conflict_files()
        if not conflict_files:
            sublime.status_message(
                msgs.get('no_conflict_files_found', self.git_repo))
            return

        self.show_quickpanel_selection(conflict_files)

    def get_conflict_files(self):
        # Search for conflicts using git executable
        conflict_files = self.git_command(
            ["diff", "--name-only", "--diff-filter=U"],
            repo=self.git_repo
        )

        conflict_files = conflict_files.splitlines()
        # Remove empty strings and sort the list
        return sorted([x for x in conflict_files if x])

    def get_representation_list(self, conflict_files):
        """Returns a list with only filenames if the 'show_only_filenames'
        option is set, otherwise it returns just a clone of the given list"""
        result = None
        if settings.get('show_only_filenames'):
            result = []
            for string in conflict_files:
                result.append(string.rpartition('/')[2])
        else:

            result = list(conflict_files)
        # Add an "Open all ..." option
        result.insert(0, msgs.get('open_all'))

        return result

    def show_quickpanel_selection(self, conflict_files):
        full_path = [os.path.join(self.git_repo, x) for x in conflict_files]
        show_files = self.get_representation_list(full_path)

        # Show the conflict files in the quickpanel and open them on selection
        def open_conflict(index):
            if index < 0:
                return
            elif index == 0:
                # Open all ...
                self.open_files(*full_path)
            else:
                self.open_files(full_path[index - 1])

        self.window.show_quick_panel(show_files, open_conflict)

    def open_files(self, *files):
        for file in files:
            # Workaround sublime issue #39 using sublime.set_timeout
            # open_file doesn't set cursor when run from a quick panel callback
            sublime.set_timeout(
                lambda file=file: init_view(self.window.open_file(file)),
                0
            )


def init_view(view):
    return  # TODO: Find a workaround for the cursor position bug

    if view.is_loading():
        sublime.set_timeout(lambda: init_view(view), 50)
    else:
        view.run_command("find_next_conflict")


class ScanForConflicts(sublime_plugin.EventListener):
    def on_activated(self, view):
        if settings.get('live_matching'):
            highlight_conflicts(view)

    def on_load(self, view):
        if settings.get('live_matching'):
            highlight_conflicts(view)

    def on_pre_save(self, view):
        if settings.get('live_matching'):
            highlight_conflicts(view)


# ST3 automatically calls plugin_loaded when the API is ready
# For ST2 we have to call the function manually
if _st_version < 3000:
    plugin_loaded()
