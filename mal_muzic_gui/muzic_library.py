from typing import Dict, Tuple
from os import path
import os
from constants import *
import shutil
from helpers import path_joins

def get_default_dir():
    test_file = DEFAULT_DIR_FILE_TEST
    if test_file in os.listdir('.'):
        return '..'
    else:
        return '.'
    
def make_list_folder(user, type):
    p = path.join(library_dir, type)
    os.makedirs(p, exist_ok=True)
    
def is_downloaded(user, name):
    return name in files_already_downloaded

def copy(user, type, name):
    _user, _type = files_already_downloaded[name]
    shutil.copy2(path_joins(_user, _type, name), path_joins(user, type, name))

def move(user, type, name):
    _user, _type = files_already_downloaded[name]
    os.rename(path_joins(_user, _type, name), path_joins(user, type, name))
    
    
library_dir = get_default_dir()

# getting data about all downloaded files
files_already_downloaded: Dict[str, Tuple[str, str]] = {}
already_downloaded_count = 0
usernames = []

def init_library(dir=None):
    global library_dir, already_downloaded_count, files_already_downloaded, usernames
    if dir is not None:
        library_dir = dir
    # loop throught all users
    print('[I] Looking for downloaded files')
    for user in os.listdir(library_dir):
        user_dir = path.join(library_dir, user)
        usernames.append(user)
        # loop throught all lists that we can download to
        for list in DEFAULT_LISTS:
            p = path.join(user_dir, list)
            if path.isdir(p):
                files = os.listdir(p)
                already_downloaded_count += len(files)
                files_already_downloaded.update({file:(user, list) for file in files})
    print(f'[I] Found {already_downloaded_count} files')