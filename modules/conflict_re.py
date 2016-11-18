import re

# view.find sadly can't handle naming groups
NO_NAMING_GROUPS_PATTERN = r"(?s)<{7}[^\n]*\n"\
                            "(.*?)(?:\|{7}[^\n]*\n"\
                            "(.*?))?={7}\n(.*?)>{7}[^\n]*\n"

CONFLICT_REGEX = re.compile(r"(?s)<{7}[^\n]*\n"
                            "(?P<head>.*?)(?:\|{7}[^\n]*\n"
                            "(?P<ancestor>.*?))?={7}\n"
                            "(?P<both>.*?)>{7}[^\n]*\n"
                            "(?P<current>.*?)>{7}[^\n]*\n")

CONFLICT_MARKER_REGEX = {
  "head" : r"(?s)(<{7}[^\n]*\n)",
  "split": r"(?s)={7}\n",
  "current" : r"(?s)(>{7}[^\n]*\n)"
}

# group patterns; this patterns always match the seperating lines too,
# so we have to remove them later from the matched regions
CONFLICT_GROUP_REGEX = {
    "head": r"(?s)<{7}[^\n]*\n.*?\|{7}|>{7}",
    "ancestor": r"(?s)\|{7}[^\n]*\n.*?={7}",
    "current": r"(?s)={7}[^\n]*\n.*?>{7}"
}

# Swaps conflicting changes and removes git conflict markers
def swap(conflict_text):
  commits = re.split(CONFLICT_MARKER_REGEX["split"], conflict_text)
  head_commit = re.sub(CONFLICT_MARKER_REGEX["head"], '', commits[0])
  new_commit = re.sub(CONFLICT_MARKER_REGEX["current"], '', commits[1])
  return new_commit + head_commit

# Keeps both versions and removes git conflict markers
def keepBoth(conflict_text):
  return re.sub(r"(<<<.*\n|===.*\n|>>>.*\n)", '', conflict_text)