#!/usr/bin/env python3
# Copyright 2026 Héctor Tarrido-Picart
# SPDX-License-Identifier: Apache-2.0
#
# yoda — Claude Code hook. One script, three events:
#   session-start   inject the ruleset if the mode is on
#   subagent-start  hand the ruleset to subagents too
#   prompt          track /yoda, /yoda off, "stop yoda", "normal mode"; nudge each turn while on
#
# Mode is stored per session in ~/.claude/yoda/<session_id>. Default comes from
# YODA_DEFAULT_MODE (on|off), else "on".

import json
import os
import re
import sys
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / "yoda"
SKILL = Path(__file__).resolve().parent.parent / "skills" / "yoda" / "SKILL.md"
REMINDER = (
    "Yoda mode on. Terse Yoda voice: answer first, no filler, inversion only when "
    "it costs no words, negations unambiguous, code/paths/errors verbatim."
)


def read_stdin():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}


def state_file(session_id):
    sid = session_id if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id or "") else "default"
    return STATE_DIR / sid


def default_mode():
    return "off" if os.environ.get("YODA_DEFAULT_MODE") == "off" else "on"


def read_mode(session_id):
    try:
        mode = state_file(session_id).read_text().strip()
        if mode in ("on", "off"):
            return mode
    except OSError:
        pass  # no state yet
    return default_mode()


def write_mode(session_id, mode):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_file(session_id).write_text(mode)
    except OSError:
        pass  # persistence is best effort


def ruleset():
    try:
        # Strip frontmatter; the body is the instruction set.
        return re.sub(r"\A---.*?\n---\n", "", SKILL.read_text(), flags=re.S).strip()
    except OSError:
        return REMINDER


def emit(event, context):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}))


def on_prompt(data):
    sid = data.get("session_id")
    prompt = str(data.get("prompt") or "").strip().lower()
    cmd = r"^/(yoda:)?yoda\b"

    if re.match(cmd + r"\s+status\b", prompt):
        emit("UserPromptSubmit", "Report this status verbatim without changing mode: Yoda mode: " + read_mode(sid))
    elif re.match(cmd + r"\s+off\b", prompt) or re.search(r"\b(stop yoda|normal mode)\b", prompt):
        write_mode(sid, "off")
        emit("UserPromptSubmit", "Yoda mode turned off. Respond in your normal style from now on. Confirm in one line.")
    elif re.match(cmd, prompt) or re.search(r"\b(yoda mode|talk like yoda)\b", prompt):
        was_off = read_mode(sid) == "off"
        write_mode(sid, "on")
        emit("UserPromptSubmit", ruleset() if was_off else REMINDER)
    elif read_mode(sid) == "on":
        emit("UserPromptSubmit", REMINDER)


def main():
    data = read_stdin()
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    if event == "session-start" and read_mode(data.get("session_id")) == "on":
        emit("SessionStart", ruleset())
    elif event == "subagent-start" and read_mode(data.get("session_id")) == "on":
        emit("SubagentStart", ruleset())
    elif event == "prompt":
        on_prompt(data)


if __name__ == "__main__":
    main()
