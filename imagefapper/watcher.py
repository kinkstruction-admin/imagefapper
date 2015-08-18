import threading
import sys
import time


class Unbuffered(object):
    """
    A wrapper class for getting unbuffered output.
    """

    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


class Watcher(threading.Thread):
    """
    A thread specifically for reporting progress and updating the progress bar.
    """

    def __init__(self, grabber, num_urls, sleep_sec=0.5):

        self.grabber = grabber
        self.out = Unbuffered(sys.stdout)
        self.num_urls = num_urls
        self.done = False
        self.progress_bar = None
        self.sleep_sec = sleep_sec

        threading.Thread.__init__(self)

    def refresh_progress_bar(self):

        num_left = self.grabber.queue.qsize()

        if num_left == 0:
            self.done = True
            pct = 100
            num_bars = 20
        else:
            pct = int(100 * float(self.num_urls - num_left) / float(self.num_urls))

            num_bars = int(20 * float(pct) / 100)

        bar = "#" * num_bars + " " * (20 - num_bars)

        self.progress_bar = "|{}| {}%".format(bar, pct)

    def run(self):

        while True:

            old_bar = self.progress_bar

            self.refresh_progress_bar()

            if old_bar is not None:
                self.out.write("\r")
                self.out.write(" " * len(old_bar))
                self.out.write("\r")

            self.out.write(self.progress_bar)

            if self.done:
                self.out.write("\n")
                return

            time.sleep(self.sleep_sec)
