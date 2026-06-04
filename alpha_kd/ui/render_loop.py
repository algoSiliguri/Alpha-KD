import mmap
import ctypes
import numpy as np
from alpha_kd.telemetry.structures import TelemetryHeader, DoubleBufferedSnapshot
from alpha_kd.telemetry.seqlock import SeqLock

class NativeUIReader:
    def __init__(self, ring_mmap: mmap.mmap, snap_mmap: mmap.mmap):
        self.ring_mmap = ring_mmap
        self.snap_mmap = snap_mmap
        self.snapshot_mem = DoubleBufferedSnapshot.from_buffer(snap_mmap)
        
        self.header_size = ctypes.sizeof(TelemetryHeader)
        self.read_offset = 0
        self.last_seqlock = 0

    def render_tick(self):
        # 1. Read header with Seqlock
        header = TelemetryHeader.from_buffer(self.ring_mmap, self.read_offset)
        
        def _read():
            return {
                "status_flag": header.status_flag,
                "payload_length": header.payload_length,
                "current_price": header.current_price,
                "allocated_capital": header.allocated_capital
            }
            
        try:
            frame_data = SeqLock.read_retry(header.seqlock, _read)
            
            # Lapping Discontinuity Check
            if header.seqlock > self.last_seqlock + 10:
                # We were lapped! Fast forward to head
                self._fast_forward_to_head()
                return None
                
            self.last_seqlock = header.seqlock
            
            if frame_data["status_flag"] == 0xFF:
                # Wraparound flag
                self.read_offset = 0
                return None
                
            total_size = self.header_size + frame_data["payload_length"]
            self.read_offset += total_size
            return frame_data
            
        except Exception:
            return None

    def _fast_forward_to_head(self):
        # Read from DoubleBufferedSnapshot to find current sequence
        def _read_snap():
            idx = self.snapshot_mem.active_index
            return self.snapshot_mem.buffers[idx].sequence_id
            
        SeqLock.read_retry(self.snapshot_mem.seqlock, _read_snap)
        # In a real implementation, we'd need the Engine to export its current 
        # ring_offset atomically into the snapshot so the UI can jump there.
        self.read_offset = 0 
