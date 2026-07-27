# Session mailbox — how the two Claude sessions talk

> **Channel: GitHub issue #14** — <https://github.com/AllisonBowman/Garden-Gnome/issues/14>

This project is worked from two places at once, and they can't call each other.

| | reaches | cannot reach |
|---|---|---|
| **Cloud session** (Claude Code on the web) | this repo, GitHub | `fly`, the Simulator, the catalog DB, Apple's portal — its network policy answers **403** to every host except npm / PyPI / Anthropic |
| **Terminal session** (Claude Code on the Mac) | the machine, the accounts, the device | nothing here is blocked |

Issue #14 is the seam. Comments are messages: append-only, timestamped, and
conflict-free, which is why this beats a tracked file that both sides would
have to pull, edit, and push.

## Reading and writing it

```bash
# read
gh issue view 14 --repo AllisonBowman/Garden-Gnome --comments

# write
gh issue comment 14 --repo AllisonBowman/Garden-Gnome --body "..."

# post command output — the common case
curl -s https://garden-gnome-api.fly.dev/ai/status \
  | gh issue comment 14 --repo AllisonBowman/Garden-Gnome --body-file -
```

## Conventions

- Prefix every comment `**[terminal]**` or `**[cloud]**`.
- One topic per comment.
- Paste real output in a fenced block. Raw beats a summary — the summary is
  usually where the useful detail was already lost.
- **Never paste a secret value.** `fly secrets list` prints names and digests,
  not values; that is the version to paste. No `.p8` contents, no API keys,
  no tokens. If a command would print a secret, don't run it into the mailbox.

## What this is not

**Polling, not push.** Neither session is notified when the other writes.
Someone has to look, which in practice means telling a session "check the
mailbox" when you want it to act.

There is one real push path, and it only works for pull requests: the cloud
session can subscribe to a PR and receive GitHub events as they happen. If the
terminal session comments on a subscribed PR, the cloud session wakes up. Worth
setting up when a PR is the thing being worked on; not a general channel.
