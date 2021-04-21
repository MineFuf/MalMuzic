from jikanpy import Jikan
import jikanpy.exceptions
from os import path
import os
from shutil import rmtree
import pafy
from youtubesearchpython import VideosSearch
from termcolor import cprint
from progress.bar import Bar
from pathvalidate import sanitize_filename
import argparse as arp

# enable colors in windows shell
os.system('color')

# all anime list types avaible
default_lists = ['watching', 'completed', 'onhold', 'dropped', 'ptw']

# argument parsing
parser = arp.ArgumentParser(prog='MalMusic', description='Downloads all or not music from your mal account to different folder based on if completed etc.')
parser.add_argument('username', type=str, help='Name of your Mal Account')
parser.add_argument('-dir', type=lambda string: string if os.path.isdir(string) else exec('raise arp.ArgumentTypeError("Is not valid path to folder")'), default='.',
                    help='Directory of your mal music library, folder for individual username will be created so this shouldn\'t include it. Defaults to current dir.')
parser.add_argument('-lists-include', type=lambda string: [s for s in string.split(',') if s in default_lists] if type(string) == str else exec('raise arp.ArgumentTypeError("Is not valid list type comma-separated list.")'),
                    help='Anime lists to download, comma-separated list of types: ptw,watching,completed; avaible types are: watching, completed, onhold, dropped, ptw')
parser.add_argument('-m', default=False, action='store_true', help='If downloaded song is found in other directory then we\'r downloading new one, should we move downloaded one without downloading again.')
parser.add_argument('-debug-page-lim', type=int, help='DEBUG  Number of anime to download from one page of anime list', default=0)

args = parser.parse_args()
print(args)

 # define "constants"
jikan = Jikan()
lists = args.lists_include if args.lists_include is not None else default_lists
page_lim = args.debug_page_lim # for simpleler debugging
page_lim_enable = page_lim > 0
move_to_other_fold = args.m

# where music will be stored and other data
music_folder = args.dir
# music_folder = r'C:\Users\Host\Music\Mal'
username = args.username
main_fold = path.join(music_folder, username)

cprint('[I] Starting program', 'green')

# check if profile exist or some other error like lacking internet occurs
try:
    jikan.user(username, 'profile')
except jikanpy.exceptions.APIException as api_err:
    cprint('[E] Error occured, maybe lacking internet connection or username provided doesn\'t exists', 'red')
    exit()
    
# find all already downloaded files in user's music folder
downloaded_files = dict()
for list in lists:
    p = path.join(main_fold, list)
    if path.isdir(p):
        downloaded_files.update({file:list for file in os.listdir(p)})

# loop over all types of lists
for idx_type, list_type in enumerate(lists):
    print('[I] Doing list of type "' + list_type + '"')
    fold = path.join(main_fold, list_type)
    
    # make anime list folder
    os.makedirs(fold, exist_ok=True)
    print('[I] Created folder of this anime list')
    
    # get page data
    page_num = 1
    print('[I] Doing page number ' + str(page_num))
    page = jikan.user(username, 'animelist', list_type, page_num)
    anime_list = page['anime']
    
    while len(anime_list) > 0:
        anime_in_page_done = 0
        for idx_anime, anime in enumerate(anime_list):
            if page_lim_enable and anime_in_page_done >= page_lim:
                print('[I] Debug limit (' + str(page_lim) + ') reached')
                break # break if page limit exceeded
            
            mal_id = anime['mal_id']
            anime_page = jikan.anime(mal_id)
            title = anime_page['title']
            
            to_search = [title + ' op ' + str(i + 1) for i in range(len(anime_page['opening_themes']))]
            to_search.extend([title + ' ed ' + str(i + 1) for i in range(len(anime_page['ending_themes']))])
            
            print('[I] Got page for "' + title + '" (' + str(mal_id) + ')')
            
            already_downloaded = []
            for idx_video, request in enumerate(to_search):
                print('[I] YT request: "' + request + '"')
                search_res = VideosSearch(request, limit=1).result()['result'][0]
                response, video_title = search_res['link'], search_res['title']
                
                if response in already_downloaded:
                    cprint('[*] Video "' + response + '" already downloaded, skipping', 'yellow')
                    continue
                
                print('[I] Found video "' + response + '", "' + video_title + '"')
                already_downloaded.append(response)
                
                audio_stream = pafy.new(response).getbestaudio()
                
                filename = request + ' (' + str(mal_id) + ').mp3'
                filename = sanitize_filename(filename)
                filepath = path.join(fold, filename)
                
                #check if song was already downloaded, then we can just ignore it
                if filename in os.listdir(fold):
                    cprint('[*] Video "' + filename + '" found in folder, skipping it', 'yellow')
                    continue
                elif move_to_other_fold and filename in downloaded_files:
                    cprint('[*] Video downloaded in "' + downloaded_files[filename] + '", moving it to this folder.', 'yellow')
                    old_dir = path.join(main_fold, downloaded_files[filename])
                    old_path = path.join(old_dir, filename)
                    os.rename(old_path, filepath)
                    print('[I] File succesfully moved')
                    continue
                
                with Bar(f'[P] type: {idx_type + 1}/{len(lists)} [{list_type}], page: {page_num}/?, anime: {idx_anime + 1}/{len(anime_list)}, song: {idx_video + 1}/{len(to_search)}', max=100) as bar:
                    callback = lambda *data: bar.next(int(data[2] * 100) - bar.index)
                    audio_stream.download(quiet=True, filepath=filepath, callback=callback)
                    
              
            anime_in_page_done += 1
            
        page_num += 1
        print('[I] Doing page number ' + str(page_num))
        page = jikan.user(username, 'animelist', list_type, page_num)
        anime_list = page['anime']
        
    print('[I] Done "' + list_type + '"')
