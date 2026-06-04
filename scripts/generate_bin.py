import numpy as np
import ctypes

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

def generate():
    num_ticks = 100000
    arr = np.zeros(num_ticks, dtype=[
        ('timestamp_ns', np.int64),
        ('open', np.float32),
        ('high', np.float32),
        ('low', np.float32),
        ('close', np.float32),
        ('volume', np.float32)
    ])
    
    price = 100.0
    for i in range(num_ticks):
        price += np.random.normal(0, 0.01)
        arr[i]['timestamp_ns'] = 1600000000000000000 + (i * 1000000000)
        arr[i]['open'] = price
        arr[i]['high'] = price + 0.05
        arr[i]['low'] = price - 0.05
        arr[i]['close'] = price
        arr[i]['volume'] = 100.0

    with open("market_data_test.bin", "wb") as f:
        f.write(arr.tobytes())
    print("Generated 100,000 synthetic ticks in market_data_test.bin")

if __name__ == "__main__":
    generate()
