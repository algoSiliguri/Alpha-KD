# Prompt: Grill-Me Checkpoint (Extraction Interview)

Use this to extract knowledge from me one question at a time.

## Instructions to the agent

Interview me about the topic I name. Rules:

1. Ask **one question at a time**. Wait for my answer before the next.
2. Before each question, provide your **recommended answer** so I can confirm,
   correct, or redirect.
3. After **every** answer, append a checkpoint to
   `brainstorms/<topic-slug>.md` (create if missing).
4. Each checkpoint must track these sections, kept up to date:
   - **Summary** — current one-paragraph understanding
   - **Q&A log** — every question + my answer, in order
   - **Decisions** — choices I have confirmed
   - **Assumptions** — things you inferred but I did not confirm
   - **Open flags** — unresolved questions / risks
   - **Candidate wiki notes** — durable items that *might* be promoted later
   - **Promotion status** — always `not promoted yet` until I say otherwise
5. Prefer short, specific questions. Surface contradictions when you spot them.
6. **Never** write to `wiki/`. Never promote without my explicit approval.
7. Stop when I say "stop" or "promote".

Begin by asking me what topic to grill, then ask question 1.
