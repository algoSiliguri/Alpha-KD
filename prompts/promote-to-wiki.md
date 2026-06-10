# Prompt: Promote Brainstorm to Wiki

Use this only when I explicitly say "promote".

## Instructions to the agent

1. Read the named `brainstorms/<topic>.md`.
2. Extract **only stable, verified knowledge**. Drop scratch, dead ends, and
   anything still under "Open flags" unless I confirm it.
3. Write to `wiki/<topic-slug>.md`.
4. The wiki note must include:
   - **Status** — verified / partial / draft
   - **Source** — brainstorm file it came from
   - **Verified facts** — user-confirmed, durable
   - **Workflow summary** — what was decided and why
   - **Boundaries** — what this does NOT cover
   - **Open questions** — carried-over unresolved items
   - **Next action**
5. **Clearly mark anything uncertain** with `> [!warning] Unverified`.
6. Clearly separate user-confirmed facts from assistant recommendations.
7. Do not invent facts. If the brainstorm lacks something, list it under
   Open questions instead of guessing.

Report the path of the created note when done.
