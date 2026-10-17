#!/usr/bin/env python3
# Copyright 2026 Héctor Tarrido-Picart
# SPDX-License-Identifier: Apache-2.0
#
# yoda — Claude Code hook. The main conversation gets the rules from the
# output style (output-styles/yoda.md, forced on while the plugin is enabled).
# This hook covers what an output style can't:
#   prompt          add a short per-turn reminder, which counters drift in long sessions
#   subagent-start  give subagents the rules, since output styles don't apply to them

import json
import re
import sys
from pathlib import Path

STYLE = Path(__file__).resolve().parent.parent / "output-styles" / "yoda.md"
REMINDER = (
    "Yoda style: answer only what was asked, answer first, no ceremony or recap. "
    "Open-ended question? Answer the likely case, then one short Yoda-style question for other branches. "
    "Short readable sentences; inversion only when it costs no words. "
    "Negations unambiguous; code, paths and errors verbatim. "
    "Follow the rules, not the length of earlier replies."
)


def rules():
    try:
        # Strip frontmatter; the body is the instruction set.
        return re.sub(r"\A---.*?\n---\n", "", STYLE.read_text(), flags=re.S).strip()
    except OSError:
        return REMINDER


def emit(event, context):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}))


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    if event == "prompt":
        emit("UserPromptSubmit", REMINDER)
    elif event == "subagent-start":
        emit("SubagentStart", rules())


if __name__ == "__main__":
    main()
