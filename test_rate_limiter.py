from rate_limiter import RateLimiter
import time

"""
  This test demonstrates how the RateLimiter enforces a maximum number of calls 
  within a given time period.

  Expected behavior:
  - The first 'max_calls' happen immediately without delay.
  - When the limit is reached, the RateLimiter will sleep to enforce the time window.
  - After waiting, further calls proceed immediately.
  
  In this example:
  - max_calls = 3 per 5 seconds.
  - Calls 1-3 print immediately.
  - Call 4 triggers a sleep of 5 seconds before proceeding.
  - Calls 5-6 continue after the wait.
  """

def test_rate_limiter():
    limiter = RateLimiter(max_calls=3, period_sec=5)  # max 3 kald pr 5 sekunder
    start = time.time()
    for i in range(6):
        print(f"Call {i+1} at {time.time()-start:.2f} seconds")
        limiter.wait_if_needed()
    print("Test done.")

if __name__ == "__main__":
    test_rate_limiter()
