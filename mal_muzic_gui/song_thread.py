from os import terminal_size
from threading import Thread
import pafy
from threading import RLock
import concurrent.futures
from typing import List

was_init = False
threads: List[concurrent.futures.Future] = []
lock = RLock()

def can_be_added():
    if not was_init:
        raise Exception("Not initialized")
    with lock:
        free = [th for th in threads if not th.running]
    return len(free) > 0

def find_free():
    if not was_init:
        raise Exception("Not initialized")
    if can_be_added():
        with lock:
            # find free thread in list
            for i in range(len(threads)):
                if not threads[i].running:
                    return i
    return None

def add_thread(th):
    if not was_init:
        raise Exception("Not initialized")
    with lock:
        # wait until free is found, shouldn't wait at all, just precaution
        while not can_be_added():
            pass
        threads[find_free()] = th
        
def init(thread_count):
    threads.extend([None] * thread_count)
    was_init = True

class SongDownloadThread:
    def __init__(self, youtube_link, filepath):
        self.link = youtube_link
        self.path = filepath
        self.yt = pafy.new(self.link)
        
    def run(self, callback):
        def _int_callback(total, recvd, ratio, rate, eta):
            callback(round(total/1024.0, 2), int(ratio*100), rate, eta)
        
        audio = self.yt.getbestaudio()
        audio.download(quiet=True, filepath=self.path, progress='KB', callback=_int_callback)
        self.cancel = audio.cancel