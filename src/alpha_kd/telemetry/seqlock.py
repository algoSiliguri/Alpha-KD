from contextlib import contextmanager
import time

class SeqLock:
    @staticmethod
    @contextmanager
    def write_lock(obj, field_name="seqlock"):
        """
        Increments the target struct field to an odd number before yielding,
        and to an even number afterwards. 
        Because this runs on a single writer process with x86-64 TSO, 
        Python's GIL and strong memory ordering provide the necessary fences.
        """
        seq = getattr(obj, field_name)
        setattr(obj, field_name, seq + 1)
        try:
            yield
        finally:
            seq = getattr(obj, field_name)
            setattr(obj, field_name, seq + 1)

    @staticmethod
    def read_retry(obj, read_func, field_name="seqlock", max_retries=1000):
        for _ in range(max_retries):
            seq1 = getattr(obj, field_name)
            if seq1 & 1: # Odd means write in progress
                time.sleep(0.000001) # Yield
                continue

            result = read_func()

            seq2 = getattr(obj, field_name)
            if seq1 == seq2:
                return result

        raise TimeoutError("SeqLock read_retry maxed out.")
