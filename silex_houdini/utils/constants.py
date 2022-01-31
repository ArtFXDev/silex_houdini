import re

FILE_PATH_SEQUENCE_CAPTURE = [
    # Matches Houdini's $F syntax
    re.compile(r"^.+[[\W_]_](\$F\d*)[\W_].+$"),
    # Matches Houdini's $T/$R/$N syntax
    re.compile(r"^.+[\W_](\$[TRN])[\W_].+$"),
    # Matches Arnolds's $T/$R/$N syntax
    re.compile(r"^.+[\W_](\%\(.+\)d)[\W_].+$"),
    # Matches V-ray's <UDIM> or <Whatever> syntax
    re.compile(r"^.+[\W_](\<.+\>)[\W_].+$"),
]
