import itertools as it
import sublime
from . import logging


START = '<<<<<<<'
ANCESTOR = '|||||||'
MIDDLE = '======='
END = '>>>>>>>'
MARKERS = (START, ANCESTOR, MIDDLE, END)

# Other types are not supported
CHAR = {
    'Unix': '\n',
    'Windows': '\r\n'
}


def find_all(view, line_regions):
    start_line_region = None
    last_line_region = len(line_regions) - 1
    conflicts = []

    while start_line_region is not last_line_region:
        conflict = find(view, line_regions, start=start_line_region)
        if conflict:
            conflicts.append(conflict)
            # For simplicity just use the end line region
            start_line_region = conflict.end_line_region
        else:
            break
    return conflicts


def find(view, line_regions, start=None):
    start_marker = None
    ours = []
    anc_markers = None  # May be multiple
    common_ancestors = []  # line or nested conflicts
    ignored_lines = []
    middle_marker = None
    theirs = []
    end_marker = None
    # TODO no view here for testing

    regions = it.dropwhile(lambda re: start and re is not start, line_regions)
    for line_region in regions:
        line = view.substr(line_region)

        # skip lines in nested conflict, they are all in common_ancestors
        if (line_region, line) in ignored_lines:
            continue

        if not start_marker and line.startswith(START):
            start_marker = (line_region, line)
            continue

        # the beginning of a nested conflict block
        # must come before the middle marker
        if (start_marker and anc_markers and not middle_marker and
                line.startswith(START)):
            conflict = find(view, line_regions, start=line_region)
            if conflict:
                common_ancestors.append(conflict)
                ignored_lines.extend(conflict.all_lines)
            continue

        # common ancestors come before the middle marker
        # there may be multiple ancestor blocks
        if start_marker and not middle_marker and line.startswith(ANCESTOR):
            if not anc_markers:
                anc_markers = [(line_region, line)]
            else:
                anc_markers.append((line_region, line))
            continue

        if start_marker and not middle_marker and line.startswith(MIDDLE):
            middle_marker = (line_region, line)
            continue

        if (start_marker and middle_marker and not end_marker and
                line.startswith(END)):
            end_marker = (line_region, line)
            return ConflictRegion({
                'start_marker': start_marker,
                'ours': ours,
                'anc_markers': anc_markers,
                'common_ancestors': common_ancestors,
                'middle_marker': middle_marker,
                'theirs': theirs,
                'end_marker': end_marker
            })

        if (middle_marker and
                (line.startswith(START) or line.startswith(ANCESTOR))):
            # the text is messed up TODO error
            print('The conflict block is messed up. Try rerunning the merge or rebase operation.')
            return None

        # not a marker but the normal content lines in a conflict region
        if start_marker and middle_marker:
            # theirs
            theirs.append((line_region, line))
        elif start_marker and anc_markers and not middle_marker:
            common_ancestors.append((line_region, line))
        elif start_marker and not (anc_markers or middle_marker):
            # ours
            ours.append((line_region, line))

    if start: # nested TODO
        return None

    if start_marker or middle_marker or anc_markers: # TODO error
        logging.debug('Conflict marker line found but did not find a valid conflict block')
    else:
        logging.debug('Conflict block not found')


class ConflictRegion:
    def __init__(self, data):
        # start_marker, ours,
        # anc_markers, common_ancestors,
        # middle_marker, theirs,
        # end_marker
        for key in data:
            setattr(self, key, data[key])

        self.process_ancesters()

        all_lines = ([data['start_marker']] +
                     data['ours'] +
                     (data['anc_markers'] if data['anc_markers'] else []) +
                     self.ancestors +
                     [data['middle_marker']] +
                     data['theirs'] +
                     [data['end_marker']])

        self.all_lines = list(filter(None, all_lines))
        self.all_lines.sort(key=lambda k: k[0].a)
        self.start_line_region = self.start_marker[0]
        self.end_line_region = self.end_marker[0]
        self.whole_region = sublime.Region(self.start_line_region.a,
                                           self.end_line_region.b)
        self.ours_regions = ConflictRegion.extract_region(self.ours)
        self.theirs_regions = ConflictRegion.extract_region(self.theirs)

    def process_ancesters(self):
        common_lines = []
        for entry in self.common_ancestors:
            if isinstance(entry, tuple):
                common_lines.append(entry)
            elif isinstance(entry, ConflictRegion):
                common_lines.extend(entry.all_lines)

        self.ancestors = common_lines
        # Just a list of text - no markers from nested conflicts
        self.ancestor = filter(lambda line: not line.startswith(MARKERS),
                               ConflictRegion.extract_text(common_lines))
        # Include marker lines
        self.ancestor_regions = ConflictRegion.extract_region(common_lines)

    def get_ours(self, line_ending):
        return CHAR[line_ending].join(ConflictRegion.extract_text(self.ours))

    def get_theirs(self, line_ending):
        return CHAR[line_ending].join(ConflictRegion.extract_text(self.theirs))

    def get_ancestor(self, line_ending):
        return CHAR[line_ending].join(self.ancestor)

    def get_both(self, line_ending):
        return CHAR[line_ending].join([self.get_ours(line_ending),
                                      self.get_theirs(line_ending)])

    def get_swap(self, line_ending):
        return CHAR[line_ending].join([self.get_theirs(line_ending),
                                      self.get_ours(line_ending)])

    def get_all(self, line_ending):
        return CHAR[line_ending].join([self.get_ours(line_ending),
                                      self.get_ancestor(line_ending),
                                      self.get_theirs(line_ending)])

    def get_all_swap(self, line_ending):
        return CHAR[line_ending].join([self.get_theirs(line_ending),
                                      self.get_ancestor(line_ending),
                                      self.get_ours(line_ending)])

    @staticmethod
    def extract_region(data):
        return list(map(lambda item: item[0], filter(None, data)))

    @staticmethod
    def extract_text(data):
        return list(map(lambda item: item[1], filter(None, data)))

    def __repr__(self):
        from pprint import pformat
        return pformat(vars(self), indent=4, width=1)
