import ctypes
import mmap
import os
import errno
import gc
import resource
from typing import List
from alpha_kd.telemetry.structures import TelemetryHeader, DoubleBufferedSnapshot
from alpha_kd.telemetry.seqlock import SeqLock

class ExecutionEngine:
    def __init__(
        self, 
        strategies: List, 
        data_feed, 
        ipc_pipe_fd: int, 
        ring_mmap: mmap.mmap, 
        snap_mmap: mmap.mmap,
        tick_rate: int = 0
    ):
        self.strategies = strategies
        self.data_feed = data_feed
        self.tick_rate = tick_rate
        
        if ipc_pipe_fd is not None:
            os.set_blocking(ipc_pipe_fd, False)
            
        self.ipc_pipe_fd = ipc_pipe_fd
        
        self.ring_mmap = ring_mmap
        self.ring_offset = 0
        self.ring_size = len(ring_mmap)
        
        self.snapshot_mem = DoubleBufferedSnapshot.from_buffer(snap_mmap)
        self.tick_sequence = 0
        self.header_size = ctypes.sizeof(TelemetryHeader)

    def poll_ipc_commands(self) -> bytes:
        if self.ipc_pipe_fd is None:
            return b""
        try:
            return os.read(self.ipc_pipe_fd, 4096)
        except OSError as e:
            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return b""
            raise

    def process_commands(self, raw_bytes: bytes):
        pass # Handle Pause, Stop, etc.

    def run_loop(self):
        start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        tick_interval = 1.0 / self.tick_rate if self.tick_rate > 0 else 0
        import time
        last_tick_time = time.perf_counter()
        
        for tick in self.data_feed:
            self.tick_sequence += 1
            
            if tick_interval > 0:
                now = time.perf_counter()
                elapsed = now - last_tick_time
                if elapsed < tick_interval:
                    time.sleep(tick_interval - elapsed)
                last_tick_time = time.perf_counter()
                
            if self.tick_sequence % 50000 == 0:
                current_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                print(f"[ExecutionEngine] Tick {self.tick_sequence} | RSS: {current_mem / 1024 / 1024:.2f} MB | GC: {gc.get_stats()}")
            
            raw_cmds = self.poll_ipc_commands()
            if raw_cmds:
                self.process_commands(raw_cmds)

            for strategy in self.strategies:
                # Calculate maximum remaining space in ring
                remaining_space = self.ring_size - self.ring_offset - self.header_size
                if remaining_space <= 0:
                    self._handle_wraparound()
                    remaining_space = self.ring_size - self.ring_offset - self.header_size
                
                # Sliced memoryview for variable payload
                payload_buffer = memoryview(self.ring_mmap)[self.ring_offset + self.header_size : self.ring_offset + self.header_size + remaining_space]
                
                # Strategy logic evaluates here in pure-function manner
                payload_len = strategy.on_tick(tick, {}, payload_buffer)
                
                total_frame_size = self.header_size + payload_len
                
                # Double check boundaries if strategy lied about payload length
                if self.ring_offset + total_frame_size > self.ring_size:
                    self._handle_wraparound()
                    # Re-run after wraparound (in reality, should be properly structured to avoid double compute)
                    payload_buffer = memoryview(self.ring_mmap)[self.ring_offset + self.header_size : self.ring_offset + self.header_size + (self.ring_size - self.ring_offset - self.header_size)]
                    payload_len = strategy.on_tick(tick, {}, payload_buffer)
                    total_frame_size = self.header_size + payload_len

                # Frame construction & Seqlock
                header = TelemetryHeader.from_buffer(self.ring_mmap, self.ring_offset)
                
                with SeqLock.write_lock(header, "seqlock"):
                    header.timestamp_ns = tick.timestamp_ns
                    header.strategy_id = strategy.id
                    header.status_flag = strategy.status
                    header.current_price = tick.close
                    header.position_size = getattr(strategy, 'position_size', 0.0)
                    header.unrealized_pnl = strategy.unrealized_pnl
                    header.realized_pnl = 0.0
                    header.allocated_capital = getattr(strategy, 'allocated_capital', 10000.0)
                    header.payload_length = payload_len
                
                self.ring_offset += total_frame_size
                
                # Snapshot Update
                with SeqLock.write_lock(self.snapshot_mem, "seqlock"):
                    inactive_idx = 1 - self.snapshot_mem.active_index
                    target_buf = self.snapshot_mem.buffers[inactive_idx]
                    
                    target_buf.sequence_id = self.tick_sequence
                    target_buf.is_active = True
                    target_buf.unrealized_pnl = strategy.unrealized_pnl
                    target_buf.allocated_capital = header.allocated_capital
                    
                    self.snapshot_mem.active_index = inactive_idx

    def _handle_wraparound(self):
        # Insert FLAG_WRAPAROUND frame
        header = TelemetryHeader.from_buffer(self.ring_mmap, self.ring_offset)
        with SeqLock.write_lock(header, "seqlock"):
            header.status_flag = 0xFF # 0xFF = WRAPAROUND
            header.payload_length = 0
            
        self.ring_offset = 0
