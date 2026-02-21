import threading
import time
import jlogger as jlog

logger = jlog.getLogger("thread-demo")


def worker(worker_id: int):
    wlog = logger.with_value("worker_id", worker_id)

    for i in range(3):
        wlog.info().with_value("step", i).msg("processing")
        time.sleep(0.01)


if __name__ == "__main__":
    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(4)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()