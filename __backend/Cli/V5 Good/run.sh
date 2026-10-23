#!/bin/sh
# ---------------------------------------------------------------------------
# world.execute(me);  —  terminal ASCII music video
#   ./run.sh                 play with sound
#   ./run.sh --silent        visuals only
#   ./run.sh --info          print the timeline
#   ./run.sh --dump 15,60    render single frames as text
#   ./run.sh --help          all options
# ---------------------------------------------------------------------------
cd "$(dirname "$0")" || exit 1
exec python3 src/mv.py "$@"
