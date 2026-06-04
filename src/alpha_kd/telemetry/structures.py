import ctypes

class TelemetryHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("seqlock", ctypes.c_uint64),
        ("timestamp_ns", ctypes.c_int64),
        ("strategy_id", ctypes.c_uint32),
        ("status_flag", ctypes.c_uint8),
        ("current_price", ctypes.c_float),
        ("position_size", ctypes.c_float),
        ("unrealized_pnl", ctypes.c_float),
        ("realized_pnl", ctypes.c_float),
        ("allocated_capital", ctypes.c_float),
        ("payload_length", ctypes.c_uint32)
    ]

class StrategySnapshot(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("sequence_id", ctypes.c_uint64),
        ("is_active", ctypes.c_bool),
        ("unrealized_pnl", ctypes.c_float),
        ("allocated_capital", ctypes.c_float)
    ]

class DoubleBufferedSnapshot(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("seqlock", ctypes.c_uint64),
        ("active_index", ctypes.c_uint8),
        ("buffers", StrategySnapshot * 2)
    ]
