# Python Quality & Package Standards

- Strict Prohibition: NEVER write or allow wildcard imports (`from X import *`). All imports must explicitly name symbols.
- Package Discipline: Do not introduce module names that shadow common pip packages (e.g., our local MetaTrader5.py collision).
- Absolute Path Hygiene: Eradicate `sys.path.append` hacks. All references must resolve cleanly via explicit python package modules.
