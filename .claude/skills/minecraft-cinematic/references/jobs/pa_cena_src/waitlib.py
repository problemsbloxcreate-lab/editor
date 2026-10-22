import time, os
def when_free(fn, poll=8, max_wait=3600):
    """Retry fn() while another pipeline holds D:/cinecam-run/render.lock (never touches that lock)."""
    t0 = time.time()
    while True:
        try:
            return fn()
        except RuntimeError as e:
            if "another render seems to be running" in str(e) and time.time() - t0 < max_wait:
                time.sleep(poll); continue
            raise
