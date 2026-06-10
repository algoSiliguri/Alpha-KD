---
name: promote-to-wiki
description: Promote an approved brainstorms/ candidate note into durable product truth in wiki/. Requires explicit human approval before writing. Manual invocation only via /promote-to-wiki.
disable-model-invocation: true
---

# Promote-to-Wiki — Durable Knowledge Promotion

Promote a clarified candidate requirement from `brainstorms/` into `wiki/`.
`wiki/` is committed product truth — only stable, approved knowledge enters.

## Flow

```
candidate note
→ verify approval
→ check contradictions
→ add metadata
→ promote to wiki
→ suggest GitHub epic/story
```

## Rules

1. **Verify approval first.** Only proceed when Koustav explicitly said
   "promote" for this specific note. If unclear, ask and stop.
2. Read the named `brainstorms/<topic>.md`.
3. Extract **only stable, verified knowledge**. Drop scratch, dead ends, and
   anything under "Open flags" unless Koustav confirms it now.
4. **Check contradictions** against existing `wiki/` notes before writing.
   Surface conflicts; do not silently overwrite prior truth.
5. Write to `wiki/<topic-slug>.md` with frontmatter metadata:
   - **status** — verified / partial / draft
   - **source** — brainstorm file(s) it came from
   - **created / updated** — dates
   - **confidence** — high / medium / low
   - **open-questions** — carried-over unresolved items
   - **issue** — linked GitHub issue/epic if one exists
6. Body must separate **user-confirmed facts** from **assistant
   recommendations**. Mark anything uncertain with `> [!warning] Unverified`.
7. Do not invent facts. Missing info → list under open questions, never guess.
8. After writing, suggest whether this should become a GitHub epic or story
   (title + one-line body), but do not create it without approval.
9. Report the path of the created note.
