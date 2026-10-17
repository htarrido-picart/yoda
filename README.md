<p align="center">
  <img src="assets/mascot.svg" width="176" alt="A small green pixel-art creature with long ears, a brown robe and a walking stick">
</p>

# yoda

A Claude Code plugin that makes Claude's replies terse and in Yoda's word order. Fewer output tokens per reply. Code, commands, paths and errors stay exactly as they are.

```
You:    why is my git push rejected?
Claude: Commits that your local branch lacks, the remote branch has.
        Pull and rebase, then push:
        git pull --rebase && git push
```

Inspired by and adapted from [Caveman](https://github.com/JuliusBrussee/caveman).

## Why

Every output token is billed and read. Most replies spend tokens on ceremony: "Sure! I'd be happy to help…", recaps, extra suggestions nobody asked for. This plugin tells Claude to drop that and answer only what was asked.

Yoda's word order is a natural fit: it puts the important word first ("Failing, the test is."). The plugin uses that inversion only when it costs no extra words. Yoda filler like "Hmm", "young padawan" or "the Force" is never added, since it would cost tokens.

## Install

```
/plugin marketplace add htarrido-picart/yoda
/plugin install yoda@yoda
```

Start a new session afterwards. The hooks need `python3` on your `PATH`; without it the style still applies, but subagents and the per-turn reminder are skipped.

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

## Turning it on and off

Yoda style is **always on while the plugin is enabled**. There is no in-chat off switch: that is what keeps it from drifting or switching off by accident.

To turn it off, disable the plugin:

- In Claude Code: `/plugin`, select `yoda`, choose disable
- From a terminal: `claude plugin disable yoda@yoda` (and `claude plugin enable yoda@yoda` to turn it back on)
- Per project: `"enabledPlugins": { "yoda@yoda": false }` in `.claude/settings.json`

Then run `/reload-plugins` or start a new session.

While enabled, the plugin's output style replaces any output style you selected yourself.

## What stays normal

Claude switches to plain sentences, then returns to the style, for:

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
output-styles/
  yoda.md            the style rules
hooks/
  yoda.py            hook script (Python 3, standard library only)
evals/
  drift.py           measures reply length over a long conversation
```

The rules ship as an [output style](https://code.claude.com/docs/en/output-styles) with `force-for-plugin: true`. That puts them in Claude's system prompt instead of the conversation, so they survive `/compact`, `/clear` and resumed sessions. `keep-coding-instructions: true` keeps Claude Code's normal coding guidance.

`hooks/yoda.py` covers what an output style can't:

| Event | What it does |
| --- | --- |
| `UserPromptSubmit` | Adds a one-line reminder each turn |
| `SubagentStart` | Gives subagents the same rules (output styles don't apply to them) |

### Avoiding drift

Similar plugins tend to "drift": replies get longer as the conversation goes on, because the model copies its own earlier replies. This plugin works against that in three ways:

- The rules live in the system prompt, not in context that gets summarized away.
- The rules and the per-turn reminder tell Claude to match the rules, not the length of its earlier replies.
- The rules cut *content* (answer only what was asked) rather than grammar, which conflicts less with Claude Code's own instructions.

`evals/drift.py` checks this. It holds a 10-turn conversation with and without the plugin and prints the reply length per turn.

## Development

Run Claude Code with the plugin loaded from a local checkout:

```
claude --plugin-dir path/to/yoda
```

Test the hook directly:

```
echo '{}' | python3 hooks/yoda.py prompt
echo '{}' | python3 hooks/yoda.py subagent-start
```

Measure savings and drift (runs `claude -p` 20 times, using your quota):

```
python3 evals/drift.py --turns 10
```

Validate the manifests before publishing:

```
claude plugin validate .
```

To release, bump `version` in `.claude-plugin/plugin.json` and push. Users update with `/plugin marketplace update yoda`.

## License

[Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for attribution: `output-styles/yoda.md` is adapted from Caveman, also Apache-2.0.
