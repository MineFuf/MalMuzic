from jikanpy import Jikan
import jikanpy.exceptions
from requests.sessions import TooManyRedirects
from termcolor import cprint

jikan: Jikan
def get_default_jikan():
    global jikan
    
    if jikan is None:
        print('[I] Created new Jikan instance')
        jikan = jikan()
        
    return jikan

def user_exists(username):
    try:
        jikan.user(username, 'profile')
        return True
    except jikanpy.exceptions.APIException as api_err:
        cprint(f'[E] User {username} does not exists', 'red')
        return False
    except Exception as ex:
        cprint('[E] Some error occured during getting user profile page', 'red')
        return None
    
def get_anime_list_for_page(username, type, page, jikan=None):
    if jikan is None:
        _jikan = get_default_jikan()
    else:
        _jikan = jikan
        
    return jikan.user(username, 'animelist', type, page)['anime']

def get_anime(mal_id, jikan=None):
    if jikan is None:
        _jikan = get_default_jikan()
    else:
        _jikan = jikan
        
    return jikan.anime(mal_id)

def get_songs_from_anime(anime):
    return (len(anime['opening_themes']), len(anime['ending_themes']))


anime_cache = {}
def add_anime(mal_id, title, ops, eds):
    anime_cache[mal_id] = (title, ops, eds)
    
def get_cached(mal_id, jikan=None):
    if mal_id in anime_cache:
        print(f'[I] Found anime {mal_id} in cache')
        return anime_cache[mal_id]
    
    if jikan is None:
        _jikan = get_default_jikan()
    else:
        _jikan = jikan
        
    anime = get_anime(mal_id, _jikan)
    songs = get_songs_from_anime(anime)
    add_anime(mal_id, anime['title'], songs[0], songs[1])
    return anime_cache[mal_id]