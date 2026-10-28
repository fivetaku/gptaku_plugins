#!/bin/sh
# Run a hook script with a working Python 3 in UTF-8 mode.
# On Windows `python3` is often the Microsoft Store stub (exits non-zero), and pipes
# default to the legacy codepage (cp949), so try real interpreters and force -X utf8.
script="$(dirname "$0")/$1"
for p in python3 python "py -3"; do
  if $p -c "import sys; sys.exit(sys.version_info[0] < 3)" </dev/null >/dev/null 2>&1; then
    exec $p -X utf8 -B "$script"
  fi
done
echo "gptaku-core: Python 3 not found" >&2
exit 1
