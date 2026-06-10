---
name: grill-me
description: Structured intake interview that turns a messy Alpha-KD product idea into a candidate requirement note in brainstorms/. Asks one question at a time, checkpoints every answer, never writes to wiki/. Manual invocation only via /grill-me.
disable-model-invocation: true
---

# Grill-Me — Extraction Interview

Turn a messy idea into a structured candidate requirement. You are the
interviewer; Koustav is the source of truth. Do not jump to implementation.

## Flow

```
Messy idea
→ clarify user / problem / outcome
→ identify non-goals
→ identify research/trading risk
→ identify UI/product implication
→ identify verification evidence
→ produce candidate requirement draft
→ wait for Koustav approval
```

## Rules

1. Ask **one question at a time**. Wait for the answer before the next.
2. Before each question, state your **recommended answer** so Koustav can
   confirm, correct, or redirect.
3. After **every** answer, update the checkpoint file
   `brainstorms/<topic-slug>.md` (create if missing).
4. The checkpoint file must keep these sections current:
   - **Summary** — one-paragraph current understanding
   - **Q&A log** — every question + answer, in order
   - **Decisions** — choices Koustav confirmed
   - **Assumptions** — inferred, NOT confirmed
   - **Open flags** — unresolved questions / risks
   - **Candidate wiki notes** — durable items that might be promoted later
   - **Promotion status** — always `not promoted yet` until Koustav says otherwise
5. Cover, in roughly this order: who/what problem/desired outcome → explicit
   non-goals → research or trading risk (overfitting, lookahead, regime
   sensitivity) → UI/product implication → what evidence proves it works.
6. Short, specific questions. Surface contradictions with existing `wiki/`
   notes when spotted.
7. **Never** write to `wiki/`. Never promote. Promotion is a separate,
   explicitly approved step (`/promote-to-wiki`).
8. Stop when Koustav says "stop" or "promote". On "promote", tell him to run
   `/promote-to-wiki <topic-slug>`.

## Start

Ask what topic to grill (or use the argument if given), then ask question 1.
