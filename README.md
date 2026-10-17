# yoda

A Claude Code plugin that makes Claude's replies terse and in Yoda's voice. Fewer output tokens per reply. Code, commands, paths and errors stay exactly as they are.

```
You:    why is my git push rejected?
Claude: Behind the remote, your branch is. Others pushed first.
        Pull and rebase, then push:
        git pull --rebase && git push
```

Inspired by and adapted from [Caveman](https://github.com/JuliusBrussee/caveman).

## Why

Every output token is billed and read. Most replies spend tokens on ceremony: "Sure! I'd be happy to help…", recaps, closing offers. This plugin tells Claude to drop that and lead with the answer.

Yoda's word order is a natural fit: it puts the important word first ("Failing, the test is."). The plugin uses that inversion only when it costs no extra words. Yoda filler like "Hmm", "young padawan" or "the Force" is never added, since it would cost tokens.

## Install

```
/plugin marketplace add htarrido-picart/yoda
/plugin install yoda@yoda
```

Start a new session afterwards. Requires `python3` on your `PATH`; without it the hooks do nothing and Claude replies normally.

### For a team

Add this to a project's `.claude/settings.json` so everyone working in it is offered the plugin:

```json
{
  "extraKnownMarketplaces": {
    "yoda": { "source": { "source": "github", "repo": "htarrido-picart/yoda" } }
  },
  "enabledPlugins": { "yoda@yoda": true }
}
```

## Usage

Yoda mode is **on by default** in every new session.

| Say or type | Effect |
| --- | --- |
| `/yoda`, "yoda mode", "talk like yoda" | Turn on |
| `/yoda off`, "stop yoda", "normal mode" | Turn off |
| `/yoda status` | Show the current mode without changing it |

The mode is tracked per session, so turning it off in one session doesn't affect others.

### Configuration

| Variable | Values | Default |
| --- | --- | --- |
| `YODA_DEFAULT_MODE` | `on`, `off` | `on` |

Set `YODA_DEFAULT_MODE=off` to make the plugin opt-in: it then stays quiet until you type `/yoda`.

## What stays normal

Claude drops the Yoda voice, writes in plain sentences, and then resumes for:

- Security warnings
- Confirming actions that can't be undone
- Step-by-step instructions where word order could cause confusion
- Questions to you, and when you seem confused
- Anything saved outside the chat: code, comments, commit messages, PRs, docs, issues

Code blocks, commands, file paths, identifiers, numbers and error messages are never changed.

## How it works

```
.claude-plugin/
  plugin.json        plugin manifest and hook registration
  marketplace.json   lets this repo act as its own marketplace
skills/yoda/
  SKILL.md           the voice rules
hooks/
  yoda.py            hook script (Python 3, standard library only)
```

`hooks/yoda.py` handles three Claude Code hook events:

| Event | What it does |
| --- | --- |
| `SessionStart` | Injects the rules from `SKILL.md` if the mode is on |
| `SubagentStart` | Gives subagents the same rules |
| `UserPromptSubmit` | Detects on/off/status commands and adds a one-line reminder each turn while on |

The per-turn reminder costs a few *input* tokens. The savings are in *output* tokens, which cost more.

Mode state lives in `~/.claude/yoda/<session_id>`. Those files are tiny and safe to delete.

## Development

Run Claude Code with the plugin loaded from a local checkout:

```
claude --plugin-dir path/to/yoda
```

Test the hook directly:

```
echo '{"session_id":"t1","prompt":"stop yoda"}' | python3 hooks/yoda.py prompt
echo '{"session_id":"t1"}' | python3 hooks/yoda.py session-start
```

Measure savings by comparing output tokens with and without the plugin:

```
P="explain git rebase vs merge"
claude -p "$P" --output-format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["usage"]["output_tokens"])'
claude -p "$P" --output-format json --plugin-dir . | python3 -c 'import json,sys; print(json.load(sys.stdin)["usage"]["output_tokens"])'
```

Validate the manifests before publishing:

```
claude plugin validate .
```

To release, bump `version` in `.claude-plugin/plugin.json` and push. Users update with `/plugin marketplace update yoda`.

## License

[Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for attribution: `skills/yoda/SKILL.md` is adapted from Caveman, also Apache-2.0.
