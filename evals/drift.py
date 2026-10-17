#!/usr/bin/env python3
# Copyright 2026 Héctor Tarrido-Picart
# SPDX-License-Identifier: Apache-2.0
#
# Drift check: holds one multi-turn conversation with and without the plugin and
# prints reply length per turn. With the plugin, lengths should stay low and flat;
# a steady climb toward the baseline means the style is drifting.
#
# Usage: python3 evals/drift.py [--turns N]
# Runs `claude -p` 2*N times, so it uses your Claude Code quota.

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent

PROMPTS = [
    "Why would git push be rejected with 'non-fast-forward'?",
    "What's the difference between a process and a thread?",
    "When should I use a Python dataclass instead of a dict?",
    "How does HTTP caching with ETag work?",
    "Why is my React component re-rendering on every keystroke?",
    "What does 'set -euo pipefail' do in bash?",
    "How do database indexes speed up queries, and when do they hurt?",
    "What's the difference between TCP and UDP?",
    "How should I store passwords in a database?",
    "What causes a deadlock and how do I avoid one?",
    "When is a linked list better than an array?",
    "What does Docker's layer cache do?",
]


def ask(prompt, session_id, use_plugin, cwd):
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if session_id:
        cmd += ["--resume", session_id]
    if use_plugin:
        cmd += ["--plugin-dir", str(PLUGIN_DIR)]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=True).stdout
    data = json.loads(out)
    return data["session_id"], data["usage"]["output_tokens"], len(data["result"].split())


def run(turns, use_plugin):
    rows, session_id = [], None
    # An empty directory keeps project files and CLAUDE.md out of the conversation.
    with tempfile.TemporaryDirectory() as cwd:
        for prompt in PROMPTS[:turns]:
            session_id, tokens, words = ask(prompt, session_id, use_plugin, cwd)
            rows.append((tokens, words))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--turns", type=int, default=10, choices=range(1, len(PROMPTS) + 1))
    turns = parser.parse_args().turns

    base, yoda = run(turns, False), run(turns, True)

    print(f"{'turn':>4}  {'base tok':>8}  {'yoda tok':>8}  {'base words':>10}  {'yoda words':>10}")
    for i, ((bt, bw), (yt, yw)) in enumerate(zip(base, yoda), 1):
        print(f"{i:>4}  {bt:>8}  {yt:>8}  {bw:>10}  {yw:>10}")
    half = turns // 2 or 1
    for name, rows in (("base", base), ("yoda", yoda)):
        first = sum(t for t, _ in rows[:half]) / half
        last = sum(t for t, _ in rows[-half:]) / half
        print(f"{name}: avg output tokens, first {half} turns {first:.0f}, last {half} turns {last:.0f}")
    saved = 1 - sum(t for t, _ in yoda) / max(1, sum(t for t, _ in base))
    print(f"yoda used {saved:.0%} fewer output tokens overall")


if __name__ == "__main__":
    main()
