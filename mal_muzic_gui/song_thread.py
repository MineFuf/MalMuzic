from os import terminal_size
from threading import Thread
import pafy
from time import sleep
from threading import RLock
import concurrent.futures
from typing import List, Tuple
from termcolor import cprint


class SongDownloadThread:
    def __init__(self, youtube_link, filepath, request):
        self.link = youtube_link
        self.path = filepath
        self.running = False
        self.request = request
        
    def run(self, callback, index):
        self.running = True
        
        self.index = index
        self.total_kb = 0
        self.percent = 0
        self.rate = 0
        self.eta = 0
        
        def _cancel():
            print(f'[I] Canceling song download thread {self.index}')
            self.audio.cancel()
            print(f'[I] Succesfully stopped')
            self.running = False
        
        def _callback(total, recvd, ratio, rate, eta):
            # print('[C] Calling callback')
            self.total_kb = round(total/1024.0, 2)
            self.percent = int(ratio*100)
            self.rate = rate
            self.eta = eta
            callback()
        
        try:
            self.yt = pafy.new(self.link)
            self.audio = self.yt.getbestaudio()
            print('[I] Found best audio')
            self.cancel = _cancel
            print('[I] Starting download')
            self.audio.download(filepath=self.path, progress='KB', callback=_callback, quiet=True)
        except Exception as e:
            cprint(f'[E] {e}', 'red')
            self.running = False
        
        print(f'[I] Download {self.index} succesfully ended')
        callback()
        self.running = False
        


was_init = False
threads: List[Tuple[concurrent.futures.Future, SongDownloadThread]] = []
lock = RLock()

def can_be_added():
    if not was_init:
        raise Exception("Not initialized")
    free = [th for th in threads if th is None or not th[1].running]
    return len(free) > 0

def find_free():
    if not was_init:
        raise Exception("Not initialized")
    if can_be_added():
        # find free thread in list
        for i in range(len(threads)):
            if threads[i] is None or not threads[i][1].running:
                return i
    return None

def add_thread(th, future):
    if not was_init:
        raise Exception("Not initialized")
    with lock:
        # wait until free is found, shouldn't wait at all, just precaution
        while not can_be_added():
            sleep(0.01)
        threads[find_free()] = (future, th)    # type: ignore
        
def init(thread_count):
    global was_init
    
    threads.clear()
    threads.extend([None] * thread_count)
    was_init = True

def deinit():
    global was_init
    
    threads.clear()
    was_init = False