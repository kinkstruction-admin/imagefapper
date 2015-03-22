import os
import shutil
import queue
import requests
import threading

from .watcher import Watcher


class Grabber(object):

    def __init__(self, url_list, directory, num_threads=10):

        self.num_threads = num_threads
        self.directory = directory

        num_digits = len(str(len(url_list)))
        prefix_format = "{:0" + str(num_digits) + "d}"

        prefixes = [prefix_format.format(i) for i in range(len(url_list))]

        file_names = [
            os.path.join(directory, "{}-{}".format(prefixes[i], url.split("/")[-1]))
            for i, url in enumerate(url_list)
        ]

        self.queue = queue.Queue()

        for i, url in enumerate(url_list):
            self.queue.put_nowait((url, file_names[i]))

        for i in range(num_threads):
            self.queue.put_nowait((None, None))

        self.lock = threading.Lock()

        self.threads = [threading.Thread(target=self.worker) for i in range(self.num_threads)]

        self.url_list = url_list

    def grab(self):

        watcher = Watcher(self, len(self.url_list))

        for t in self.threads:
            t.daemon = True
            t.start()

        watcher.daemon = True
        watcher.start()

        self.queue.join()
        watcher.join()

    def worker(self):

        while True:

            try:
                url, file_name = self.queue.get()

                if url is None or file_name is None:
                    self.is_done = True
                    return

                response = requests.get(url, stream=True)

                if response.status_code != 200:
                    # warn("Trying to grab image at '{}', got status code of {}".format(
                    #     url, response.status_code))
                    continue

                with self.lock:
                    with open(file_name, "wb") as f:
                        shutil.copyfileobj(response.raw, f)
            except queue.Empty:
                continue
            finally:
                self.queue.task_done()
