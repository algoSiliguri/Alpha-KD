class SeqLock:
    \"\"\"
    A pure Python implementation of a sequential lock (seqlock).
    \"\"\"
    def __init__(self):
        # We use a simple integer for sequence, keeping in mind Python integers are arbitrary precision,
        # but conceptually it's treated as a uint64.
        self._sequence = 0

    def write_lock(self):
        \"\"\"
        Context manager for acquiring a write lock.
        Increments the sequence number to an odd value before write,
        and to an even value after write.
        \"\"\"
        class WriteLockContext:
            def __init__(self, seqlock):
                self.seqlock = seqlock

            def __enter__(self):
                self.seqlock._sequence += 1
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.seqlock._sequence += 1

        return WriteLockContext(self)

    def read_begin(self) -> int:
        \"\"\"
        Returns the current sequence number before reading.
        \"\"\"
        return self._sequence

    def read_retry(self, start_seq: int) -> bool:
        \"\"\"
        Returns True if the read must be retried.
        Returns False if the read was successful (no concurrent writes).
        \"\"\"
        # If start_seq is odd, a write was in progress when we started.
        if start_seq & 1:
            return True
        # If the sequence changed, a write happened during our read.
        if self._sequence != start_seq:
            return True
        return False
