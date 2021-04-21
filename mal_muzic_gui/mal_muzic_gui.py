from helpers import path_joins
import os
import PySimpleGUI as sg

from os import path
from typing import List
from termcolor import cprint
from pathvalidate import sanitize_filename
from youtubesearchpython import VideosSearch
from concurrent.futures.thread import ThreadPoolExecutor

import muzic_library as ml
import mal_manager as mm
import song_thread as st
from constants import *

def run(window: sg.Window, username, progresses: List[sg.ProgressBar], lists=DEFAULT_LISTS,
                 dupli_mode=0, dir=ml.get_default_dir(), thread_count=5):
    
    # dupli_mode: 0-move, 1-copy, 2-download again
    
    st.init(thread_count=thread_count)
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        for idx_type, list_type in enumerate(lists):
            print(f'[I] Doing list of type "{list_type}"')
            fold = path.join(ml.library_dir, username)
             
            # make anime list folder
            os.makedirs(fold, exist_ok=True)
            print('[I] Created folder of this anime list')

            page_num = 1
            print(f'[I] Doing page number {page_num}')
            anime_list = mm.get_anime_list_for_page(username, list_type, page_num)
            
            while len(anime_list) > 0:
                anime_in_page_done = 0
                for idx_anime, anime in enumerate(anime_list):
                    if anime_in_page_done >= PAGE_LIMIT:
                        print(f'[I] Debug limit ({PAGE_LIMIT}) reached')
                        break
                    
                    mal_id = anime['mal_id']
                    title, ops, eds = mm.get_cached(mal_id)
                    
                    print(f'[I] Got page for "{title} ({mal_id})')
                    
                    to_search = [f'{title} op {i + 1}' for i in range(ops)] + \
                                [f'{title} ed {i + 1}' for i in range(eds)]
                    
                    already_downloaded_in_anime = []        
                    for idx_video, request in enumerate(to_search):
                        
                        filename = request + ' (' + str(mal_id) + ').mp3'
                        filename = str(sanitize_filename(filename))
                        filepath = path.join(fold, filename)
                        
                        if dupli_mode != 3:
                            if filename in ml.files_already_downloaded:
                                _username, _type = ml.files_already_downloaded[filename]
                                if username != _username:
                                    cprint(f'[*] Video found downloaded in folder of different user ({path_joins(_username, _type)}), copying it', 'yellow')
                                    ml.copy(username, list_type, filename)
                                    print('[I] File succesfully copied')
                                    continue
                                    
                                elif dupli_mode == 0:
                                    cprint(f'[*] Video found downloaded in different list ({path_joins(_username, _type)}), moving it', 'yellow')
                                    ml.move(username, list_type, filename)
                                    print('[I] File succesfully moved')
                                    continue
                                    
                                elif dupli_mode == 1:
                                    cprint(f'[*] Video found downloaded in different list ({path_joins(_username, _type)}), copying it', 'yellow')
                                    ml.copy(username, list_type, filename)
                                    print('[I] File succesfully copied')
                                    continue
                        
                        print(f'[I] YT request: "{request}"')
                        search_res = VideosSearch(request, limit=1).result()['result'][0]
                        response, video_title = search_res['link'], search_res['title']

                        if response in already_downloaded_in_anime:
                            cprint(f'[*] Video "{response}" already downloaded, skipping', 'yellow')
                            continue
                        
                        while not st.can_be_added():
                            pass
                        
                        free_index = st.find_free()
                        callback = lambda total_size, percent, rate, eta: None
                        
def main():
    # set program theme
    sg.theme('LightGreen')
    
    # define default values for UI
    default_size_text = (30, 1)
    default_size_input = (50, 1)
    default_size_input_with_button = ((30, 1), (15, 1))
    
    # define file handeling modes for song duplicates
    dupli_mode = {'radio_move': 'Move when in other list', 'radio_copy': 'Copy when in other list', 'radio_download': 'Download again'}
    
    # create progress bars and their labels
    progresses = [[sg.ProgressBar()]]
    
    # make layout
    layout = [
        [
            sg.Text('Username: ', size=default_size_text),
            sg.Input('', key='input_username', size=default_size_input, enable_events=True)],
        [
            sg.Text('Anime Music Dir: ', size=default_size_text),
            sg.Input(ml.library_dir, key='input_dir', size=default_size_input_with_button[0], readonly=True, enable_events=True),
            sg.FolderBrowse(initial_folder=ml.get_default_dir(), size=default_size_input_with_button[1])],
        [sg.Radio(dupli_mode[key], group_id='dupli', key=key, enable_events=True) for i, key in enumerate(dupli_mode)]
    ]
    
    # make window
    window = sg.Window("MalMuzic", layout, finalize=True)
    
    # set default values to UI
    layout[2][0].update(value=True)
    
    # make UI element variables
    input_username: sg.Input = window.find_element('input_username')
    
    # UI loop
    while True:
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED or event is None:
            break
        
    window.close()
    
# run program
if __name__ == '__main__':
    main()