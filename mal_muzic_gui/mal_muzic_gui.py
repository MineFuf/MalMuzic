from helpers import path_joins
import os
import PySimpleGUIQt as sg

from os import path
from time import sleep
from yaspin import yaspin
from termcolor import cprint
from random import choice
from typing import List, Tuple
from threading import Thread, Event
from requests import ConnectionError
from yaspin.spinners import Spinners
from pathvalidate import sanitize_filename
from youtubesearchpython import VideosSearch
from concurrent.futures.thread import ThreadPoolExecutor

import muzic_library as ml
import mal_manager as mm
import song_thread as st
from constants import *

def run(window: sg.Window, username, progresses: List[Tuple[sg.Text, sg.ProgressBar]], column: sg.Column, lists=DEFAULT_LISTS,
                 dupli_mode=0, dir=ml.get_default_dir(), thread_count=5):
    
    library_thread = Thread(target=ml.init_library, args=(dir,))
    library_thread.start()
    print('[E] Library thread started')
    
    for i in range(len(progresses)):
        progresses[i][0].update(visible=False)
        progresses[i][1].update(visible=False)
    
    print('[I] Updating visibility')
    for i in range(thread_count):
        progresses[i][0].update(visible=True)
        progresses[i][1].update(visible=True)
        
    # window.finalize()
    # window['progresses_column'].update(visible=True)
    
    window.VisibilityChanged()
    
    print('[I] Visibility updated')
    
    stopped = Event()
    
    run_thread = Thread(target=run_, args=(window, username, progresses, stopped),
                        kwargs={'lists': lists, 'dupli_mode': dupli_mode, 'dir': dir, 'thread_count': thread_count})
    
    library_thread.join()
    print('[E] Library thread joined')
    
    run_thread.start()
    
    return (stopped, run_thread)
    
    # run_(window, username, progresses, lists, dupli_mode, dir, thread_count)

def run_(window: sg.Window, username, progresses: List[Tuple[sg.Text, sg.ProgressBar]], stopped: Event, lists=DEFAULT_LISTS,
                 dupli_mode=0, dir=ml.get_default_dir(), thread_count=5):
    
    # dupli_mode: 0-move, 1-copy, 2-download again
    
    def progress_callback():
        window['--PROGRESS_UPDATE--'].click()
    
    st.init(thread_count=thread_count)
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        try:
            for idx_type, list_type in enumerate(lists):
                if stopped.is_set():
                    break
                
                print(f'[I] Doing list of type "{list_type}"')
                fold = path_joins(ml.library_dir, username, list_type)
                
                # make anime list folder
                os.makedirs(fold, exist_ok=True)
                print('[I] Created folder of this anime list')

                page_num = 1
                print(f'[I] Doing page number {page_num}')
                was_con_err_list = True
                while was_con_err_list:
                    try:
                        anime_list = mm.get_anime_list_for_page(username, list_type, page_num)
                        was_con_err_list = False
                    except ConnectionError as ce:
                        cprint('[E] Was connection error, retrying')
                    
                
                anime_list = anime_list      # type: ignore
                while len(anime_list) > 0:
                    if stopped.is_set():
                        break
                    
                    anime_in_page_done = 0
                    for idx_anime, anime in enumerate(anime_list):
                        if stopped.is_set():
                            break
                        
                        if PAGE_LIMIT > 0 >= PAGE_LIMIT and anime_in_page_done:
                            print(f'[I] Debug limit ({PAGE_LIMIT}) reached')
                            break
                        
                        mal_id = anime['mal_id']
                        title, ops, eds = mm.get_cached(mal_id)
                        
                        print(f'[I] Got page for "{title} ({mal_id})')
                        
                        to_search = [f'{title} op {i + 1}' for i in range(ops)] + \
                                    [f'{title} ed {i + 1}' for i in range(eds)]
                        
                        already_downloaded_in_anime = []        
                        for idx_video, request in enumerate(to_search):
                            if stopped.is_set():
                                break
                            
                            print(f'[I] YT request: "{request}"')
                            search_res = VideosSearch(request, limit=1).result()['result'][0]
                            response, video_title, video_id = search_res['link'], search_res['title'], search_res['id']
                            
                            filename = f'{request} ({str(mal_id)}) - {video_id}.mp3'
                            filename = str(sanitize_filename(filename))
                            filepath = path_joins(fold, filename)
                            
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

                            if response in already_downloaded_in_anime:
                                cprint(f'[*] Video "{response}" already downloaded, skipping', 'yellow')
                                continue
                            
                            print('[I] Waiting for free thread')
                            while not st.can_be_added() and not stopped.is_set():
                                sleep(0.1)
                                # print(st.threads)
                            print('[I] Found free')
                            
                            if stopped.is_set():
                                break
                            
                            free_index = st.find_free()
                            
                            song_thread = st.SongDownloadThread(response, filepath, request)
                            future = executor.submit(song_thread.run, progress_callback, free_index)
                            st.add_thread(song_thread, future)
                            sleep(0.001)
                            # cprint(f'[D] threads: {st.threads}')
                    
                        anime_in_page_done += 1      
                        
                    page_num += 1
                    print(f'[I] Doing page number {page_num}')
                    was_con_err_list = True
                    while was_con_err_list:
                        try:
                            anime_list = mm.get_anime_list_for_page(username, list_type, page_num)
                            was_con_err_list = False
                        except ConnectionError as ce:
                            cprint('[E] Was connection error, retrying')
            
        except Exception as e:
            cprint('[E] ' + str(e), 'red')
            stopped.set()
        
        if stopped.is_set():
            for song_thread in st.threads:
                if song_thread is not None:
                    song_thread[1].cancel()
        
def main():
    # set program theme
    theme_name = 'DarkPurple4'
    sg.theme(theme_name)
    
    os.system('color')
    
    # define default values for UI
    default_size_text = (30, 1)
    default_size_input = (50, 1)
    default_size_input_with_button = ((30, 1), (15, 1))
    
    # define file handeling modes for song duplicates
    dupli_mode = {'radio_move': 'Move when in other list',
                  'radio_copy': 'Copy when in other list',
                  'radio_download': 'Download again'}
    
    # create progress bars and their labels
    progresses = [(sg.Text(f'ProgBar {key}: None', key=f'-{key}_text', visible=False),
                   sg.ProgressBar(100, key=f'-{key}_progressbar', visible=False)) for key in range(1, 51)]
    # make layout
    layout = [
        [
            sg.Text('Username: '),
            sg.Input('', key='username_input', enable_events=True),
            sg.Button('Check', key='username_button')],
        [
            sg.Text('Anime Music Dir: '),
            sg.Input(ml.library_dir, key='dir_input', disabled=True, enable_events=True),
            sg.FolderBrowse(initial_folder=ml.get_default_dir(), key='dir_browse')],
        
        [sg.Radio(dupli_mode[key], group_id='dupli', key=key, enable_events=True) for i, key in enumerate(dupli_mode)],
        [sg.Text('Thread count: '), sg.Combo(list(range(1, 51)), default_value=1, key='thread_count_combo', enable_events=True)],
        [sg.Column(progresses, scrollable=True, key='progresses_column', size=(700, 200))],
        [sg.Button('Download', key='download_button')],
        [sg.Button('', visible=False, key='--PROGRESS_UPDATE--')]
    ]
    
    to_disable = ['download_button', 'username_input', 'username_button',
                  'dir_input', 'dir_browse', 'radio_move', 'radio_copy', 'radio_download']
    
    # make window
    window = sg.Window("MalMuzic", layout, finalize=True, resizable=False)
    
    # for x in range(50):
    #     progresses[x][1].UpdateBar(50)
    
    # set default values to UI
    layout[2][0].update(value=True)
    
    # set more variables
    input_default_color = sg.LOOK_AND_FEEL_TABLE[theme_name]['INPUT']
    run_thread_running = False
    run_thread: Tuple[Event, Thread] = None    # type: ignore
    to_close = False
    
    # helper function for main
    def check_username():
        print(f'[I] Looking for mal user "{values["username_input"]}"')
        exists = mm.user_exists(values["username_input"])
        print('[I] Username exists' if exists else '[I] Username doesn\'t exists')
        if not exists:
            window['username_input'].update(background_color='#FF7777')
        else:
            window['username_input'].update(background_color=input_default_color)
        return exists
    
    def get_dupli_mode():
        for i, key in enumerate(dupli_mode):
            if window[key].get():
                return i
    
    # UI loop
    while not to_close:
        event, values = window.read()    # type: ignore
        if event == sg.WIN_CLOSED or event is None:
            to_close = True
            if run_thread is not None:
                run_thread[0].set()
            continue
        # print('[I]', event, values[event] if event in values else '')
        if event == 'username_button':
            check_username()
        if event == 'download_button':
            if not run_thread_running:
                print('[I] Checking username')
                if not check_username():
                    continue
                
                ml.library_dir = values['dir_input']
                
                window['download_button'](text=window['download_button'].ButtonText + ' Disabled')
                for dis in to_disable:
                    window[dis](disabled=True)
                
                run_thread = run(window, values["username_input"], progresses, window['progresses_column'],
                    dir=ml.library_dir, thread_count=values['thread_count_combo'])
            else:
                cprint('[E] Download already running', 'red')
            
        if event == 'thread_count_combo':
            print(f'[I] User choose {values[event]} threads to run async')
        if event in dupli_mode:
            print(f'[I] User choose: "{dupli_mode[event]}"')
        if event == '--PROGRESS_UPDATE--':
            # progresses[values[event][0]][1].UpdateBar(values[event][2])
            for i in range(len(st.threads)):
                if st.threads[i] is not None:
                    if hasattr(st.threads[i][1], 'percent'):
                        progresses[i][1].UpdateBar(st.threads[i][1].percent)
                        progresses[i][0].update(value=st.threads[i][1].request + ': ' + str(st.threads[i][1].total_kb) + 'kB, ' + str(round(st.threads[i][1].rate, 1)) + 'kB/s')
            
    if run_thread is not None:
        print('[I] Download thread still running, joining with it.')
        run_thread[1].join()
        
    window.close()
    print('[!] Exiting program')
    
# run program
if __name__ == '__main__':
    main()