import time
from threading import Lock

class RateLimiter:
    def __init__(self, max_calls: int, period_sec: float):
        self.max_calls = max_calls
        self.period_sec = period_sec
        self.call_timestamps = []
        self.lock = Lock()

    def wait_if_needed(self):
        with self.lock:
            now = time.time()
            # Fjern gamle kald der ligger udenfor periode
            self.call_timestamps = [t for t in self.call_timestamps if now - t < self.period_sec]
            if len(self.call_timestamps) >= self.max_calls:
                earliest = self.call_timestamps[0]
                to_wait = self.period_sec - (now - earliest)
                if to_wait > 0:
                    print(f"RateLimiter: Sleeping for {to_wait:.2f} seconds to respect rate limit")
                time.sleep(to_wait)
            self.call_timestamps.append(time.time())
