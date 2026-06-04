# P1 MASTER SCAFFOLDING PLAN

**Epic Summary:** Establish the definitive zero-slop directory layout and scaffolding required to bring the Alpha-KD telemetry and execution planes to life, adhering to all ADRs.

## The Definitive Directory Tree

```text
Alpha-KD/
├── scripts/
│   └── run_alpha.py                # The Master Orchestrator (Idempotent clean-slate, SIGINT traps, process spawner)
├── alpha_kd/
│   ├── execution/                  # Isolated Engine Domain
│   │   ├── engine.py               # ExecutionEngine (hot path, IPC polling, seqlock writer)
│   │   ├── datafeed.py             # AbstractDataFeed, HistoricalFeed, LiveFeed
│   │   └── portfolio.py            # Global capital state & position sizing calculator
│   ├── telemetry/                  # IPC & Synchronization Domain
│   │   ├── structures.py           # ctypes definitions (TelemetryHeader, DoubleBufferedSnapshot)
│   │   ├── seqlock.py              # Pure Python read/write seqlock handlers
│   │   └── mmap_manager.py         # Abstraction for allocating/mapping the memory buffers
│   ├── strategies/                 # Strategy Domain (Zero-Allocation)
│   │   ├── base.py                 # BaseStrategy ABC (memoryview on_tick signature)
│   │   └── cci_strategy.py         # Refactored CciStrategy using pre-allocated numpy buffers
│   ├── inference/                  # Zero-Slop ML Domain
│   │   ├── onnx_runtime.py         # ONNX I/O Binding session handlers
│   │   └── m2cgen_models.py        # Transpiled NumPy/Python scalar model functions
│   └── ui/                         # Native Desktop Domain
│       ├── app.py                  # Dear PyGui / PyQt6 application entry point
│       ├── render_loop.py          # 60fps NativeUI reader (Seqlock polling, lapping reset)
│       └── views/                  # UI panels (Equity curve, order book, logs)
└── docs/
    ├── ADRs/                       # Architectural Decision Records (001 to 005)
    └── plans/                      # Execution Contracts
```

## Execution Checklist for Claude Code
- [ ] **Task 1:** Create all empty directories and `__init__.py` files per the tree above.
- [ ] **Task 2:** Move legacy files (`Quantreo/`, `LiveTrading/`, `Strategies/`) into a temporary `_legacy_archive/` directory to clear the workspace and prevent cross-contamination.
- [ ] **Task 3:** Implement the core scaffolding files defined in `P1_STEP1_Core_Implementation.md` into the new `alpha_kd/` directories.
- [ ] **Task 4:** Create `scripts/run_alpha.py` with the boilerplate `unlink()` clean-slate ritual.

## Narrative Report
*(To be generated upon completion)*
