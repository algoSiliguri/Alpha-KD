import mmap
import ctypes
import numpy as np
import dearpygui.dearpygui as dpg
from alpha_kd.telemetry.structures import TelemetryHeader, DoubleBufferedSnapshot
from alpha_kd.telemetry.seqlock import SeqLock
from alpha_kd.ui.views.logger import log_message

class NativeUIReader:
    def __init__(self, ring_mmap: mmap.mmap, snap_mmap: mmap.mmap):
        self.ring_mmap = ring_mmap
        self.snap_mmap = snap_mmap
        self.snapshot_mem = DoubleBufferedSnapshot.from_buffer(snap_mmap)
        
        self.header_size = ctypes.sizeof(TelemetryHeader)
        self.max_frames = len(ring_mmap) // self.header_size
        
        header_dtype = np.dtype([
            ("seqlock", np.uint64),
            ("timestamp_ns", np.int64),
            ("strategy_id", np.uint32),
            ("status_flag", np.uint8),
            ("current_price", np.float32),
            ("position_size", np.float32),
            ("unrealized_pnl", np.float32),
            ("realized_pnl", np.float32),
            ("allocated_capital", np.float32),
            ("payload_length", np.uint32)
        ])
        
        # Stride directly over the binary map
        self.mmap_array = np.ndarray(shape=(self.max_frames,), dtype=header_dtype, buffer=ring_mmap)
        
        # Pre-allocate X axis for Dear PyGui
        self.x_axis = np.arange(self.max_frames, dtype=np.float32)
        
        self.last_seqlock = 0
        self.head_index = 0

    def render_tick(self):
        def _read_snap():
            idx = self.snapshot_mem.active_index
            buf = self.snapshot_mem.buffers[idx]
            return {
                "sequence_id": buf.sequence_id,
                "unrealized_pnl": buf.unrealized_pnl,
                "allocated_capital": buf.allocated_capital
            }
            
        try:
            active_snap = SeqLock.read_retry(self.snapshot_mem, _read_snap, field_name="seqlock")
        except TimeoutError:
            return
            
        current_seq = active_snap["sequence_id"]
        if current_seq == 0:
            return
            
        self.head_index = current_seq % self.max_frames
        
        if current_seq > self.last_seqlock + self.max_frames:
            log_message("[Warning] UI was lapped by execution engine. Fast forwarding.")
            self.last_seqlock = current_seq - 1
            
        if self.head_index == 0:
            return
            
        # 1. Update Metrics Grid
        dpg.set_value("metric_sequence_id", str(current_seq))
        dpg.set_value("metric_upnl", f"{active_snap['unrealized_pnl']:.2f}")
        dpg.set_value("metric_capital", f"{active_snap['allocated_capital']:.2f}")
        
        # 2. Update Equity Curve via Zero-Copy Numpy Slice
        y_slice = self.mmap_array['allocated_capital'][0:self.head_index]
        x_slice = self.x_axis[0:self.head_index]
        
        dpg.set_value("series_capital", [x_slice, y_slice])
        self.last_seqlock = current_seq
