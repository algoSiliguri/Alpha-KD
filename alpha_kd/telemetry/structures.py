import ctypes

class TelemetryHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        (\"magic\", ctypes.c_uint16),
        (\"version\", ctypes.c_uint16),
        (\"timestamp\", ctypes.c_uint64),
        (\"session_id\", ctypes.c_char * 36),
    ]

class DoubleBufferedSnapshot(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        (\"seq_lock\", ctypes.c_uint64),
        (\"active_buffer\", ctypes.c_uint8),
        # Space for user payload or subclassing
    ]
