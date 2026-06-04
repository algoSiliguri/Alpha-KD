import ctypes
import numpy as np
import mmap
import os
from abc import ABC, abstractmethod

class TickData(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("timestamp_ns", ctypes.c_int64),
        ("open", ctypes.c_float),
        ("high", ctypes.c_float),
        ("low", ctypes.c_float),
        ("close", ctypes.c_float),
        ("volume", ctypes.c_float)
    ]

class AbstractDataFeed(ABC):
    @abstractmethod
    def __iter__(self):
        pass

class HistoricalFeed(AbstractDataFeed):
    """
    Reads directly from a pre-compiled `.bin` file mapped into memory.
    Yields references to the TickData C-struct memory directly.
    """
    def __init__(self, bin_file_path: str):
        self.bin_file_path = bin_file_path
        self._mmap = None
        self._fd = None
        
        if not os.path.exists(bin_file_path):
            # Create a dummy bin file for testing if it doesn't exist
            with open(bin_file_path, "wb") as f:
                dummy_array = np.zeros(100, dtype=np.dtype([
                    ('timestamp_ns', np.int64),
                    ('open', np.float32),
                    ('high', np.float32),
                    ('low', np.float32),
                    ('close', np.float32),
                    ('volume', np.float32)
                ]))
                f.write(dummy_array.tobytes())
                
        self._fd = os.open(bin_file_path, os.O_RDONLY)
        self._size = os.path.getsize(bin_file_path)
        self._mmap = mmap.mmap(self._fd, self._size, prot=mmap.PROT_READ)
        
        self.tick_size = ctypes.sizeof(TickData)
        self.total_ticks = self._size // self.tick_size

    def __iter__(self):
        for i in range(self.total_ticks):
            offset = i * self.tick_size
            yield TickData.from_buffer(self._mmap, offset)

    def close(self):
        if self._mmap:
            self._mmap.close()
        if self._fd is not None:
            os.close(self._fd)
