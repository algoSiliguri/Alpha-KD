# Antigravity 2.0 — Manual PR Review Playbook

Status: manual-only. No MCP wiring, no scheduled tasks, no automation, and
Antigravity does not write code in this phase. It is a second pair of eyes.

## Role in the workflow

```
small patch → tests/verification → PR opened
            → Antigravity manual review (this doc)
            → merge or reject
```

Claude Code implements; Antigravity reviews. Keep the boundary hard.

## How to run a review

1. Open Antigravity IDE and open `~/Documents/GitHub/Alpha-KD` as the
   workspace (first time: it will register the project; trust the folder
   at the repo level, not the home directory).
2. Check out the PR branch locally first (`gh pr checkout <N>`), so
   Antigravity sees the exact diff state.
3. Ask it to review, scoped narrowly. Useful prompts:
   - "Walk through the diff of this branch vs main. Flag correctness risks."
   - "Does this change violate any rule in CLAUDE.md or .claude/rules/?"
   - "Trace how `<changed function>` is used. Any caller this breaks?"
4. It has the Understand-Anything skill (symlinked into its skills dir) —
   let it use the knowledge graph for structure questions; if the graph is
   stale (`meta.json` commit hash behind HEAD), ask it to refresh via
   `/understand --auto-update` before trusting structure answers.
5. Capture output: paste findings (or the generated walkthrough/artifact)
   as a comment on the GitHub PR. Evidence lives on the PR, not in
   Antigravity's local brain.

## Hard limits during this phase

- Antigravity must NOT edit files, commit, or push.
- No MCP servers configured for it.
- No scheduled/background tasks.
- Findings are advisory; merge decision stays with Koustav.

## Revisit when

- The manual loop feels repetitive enough to justify automation, AND
- the grill-me → wiki → epic pipeline is stable.
