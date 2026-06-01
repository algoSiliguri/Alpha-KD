# Strategies — Signal Definitions

7x LI_2023_02_* clones + Cci + ZScore. Copy-paste debt — converge on one interface.

## Rules
- Uniform contract: every strategy exposes the same interface (e.g. get_features / get_entry / get_exit). No bespoke per-file signatures.
- Eliminate clones: shared logic (RSI/SMA/ATR helpers) lives in one util, not duplicated across LI_2023_02_* files.
- No `import *` from Quantreo — import the named engine symbols a strategy actually uses.
- Strategies are pure signal logic: no broker calls, no live order side effects here.
- New strategy = implement the interface + register; do not fork an existing file as a template clone.
- Keep Live_EURUSD_* wrappers thin; they configure, they do not redefine strategy logic.
