import os
import shutil
import colorama
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from collections import defaultdict
import re
from colorama import Fore, Back

def format_name(name):
    """Formatea el nombre (capitalización)."""
    return ' '.join(word.capitalize() for word in name.split())

def replace_slashes(text):
    """Reemplaza '/' por '_' en el nombre del artista."""
    return text.replace('/', '_')


def clean_name(name):
    """Elimina caracteres no válidos para rutas de Windows."""
    return re.sub(r'[<>:"/\\|?*]', '', name)


def is_duplicate(destination_folder, file_name):
    """Verifica si el archivo ya existe en el destino."""
    return os.path.exists(os.path.join(destination_folder, file_name))


def organize_music(download_folder, organized_folder):
    """Organiza la música según los requisitos dados."""
    if not os.path.exists(organized_folder):
        os.makedirs(organized_folder)

    albums = defaultdict(list)  # Diccionario para agrupar canciones por álbum
    
    for file_name in os.listdir(download_folder):
        file_path = os.path.join(download_folder, file_name)

        if os.path.isfile(file_path) and file_name.endswith('.mp3'):
            try:
                audio = MP3(file_path, ID3=EasyID3)
                album = format_name(audio.get('album', ['Unknown Album'])[0])
                album = clean_name(album)  # Limpia el nombre del álbum
                artists = [format_name(artist) for artist in re.split(', | / |/ |/', audio.get('artist', ['Unknown Artist'])[0])]
                albums[album].append((file_path, artists))
            except Exception as e:
                print(f"Error leyendo metadatos de {file_name}: {e}")

    # print(f'listado: {albums}')

    for album, tracks in albums.items():
        all_artists = set(artist for _, artists in tracks for artist in artists)

        # Crear un conjunto de artistas comunes presentes en todas las canciones del álbum 
        common_artists = set(tracks[0][1]) 
        for _, track_artists in tracks: 
            common_artists &= set(track_artists)

        # Determinar si el álbum tiene múltiples artistas sin un artista común 
        is_album_songtrack = len(common_artists) == 0 and len(all_artists) > 1 
        is_artista_album = len(common_artists) > 0 and len(tracks) > 1
        is_artista_single = len(tracks) == 1

        # print(f'artistas del albun: {set(artists)}')
        # print(f'Artista comuun: {common_artists}')

        for file_path, artists in tracks:
            file_name = os.path.basename(file_path)

            # Verificar duplicados antes de copiar
            if is_duplicate(organized_folder, file_name):
                print(f'Omitido (duplicado): {file_name}')
                continue
        
            # Caso 1: Álbum con múltiples artistas
            if is_album_songtrack:

                # Copiar todas las canciones al álbum
                album_folder = os.path.join(organized_folder, "Albums", clean_name(replace_slashes(album)))
                os.makedirs(album_folder, exist_ok=True)
                if not is_duplicate(album_folder, file_name):
                    shutil.copy(file_path, os.path.join(album_folder, file_name))
                    print(Fore.RED + Back.LIGHTYELLOW_EX + f'Caso 1 Movido "Albums" (álbum múltiple): {file_name} -> {album_folder}')

                # Copia adicional para artistas individuales
                if len(set(artists)) == 1:
                    single_folder = os.path.join(organized_folder, "Artist", clean_name(replace_slashes(artists[0])), "zSingle")
                    os.makedirs(single_folder, exist_ok=True)
                    if not is_duplicate(single_folder, file_name):
                        shutil.copy(file_path, os.path.join(single_folder, file_name))
                        print(Fore.LIGHTRED_EX + Back.RESET + f'Caso 1 Copia "{artists[0]}" en zSingle: {file_name} -> {single_folder}')
                else:
                    for artist in artists:
                        # Si el artista principal está acompañado de un colaborador
                        collaboration_folder = os.path.join(organized_folder, "Artist", clean_name(replace_slashes(artist)), "zCollaboration")
                        os.makedirs(collaboration_folder, exist_ok=True)
                        if not is_duplicate(collaboration_folder, file_name):
                            shutil.copy(file_path, os.path.join(collaboration_folder, file_name))
                            print(Fore.LIGHTRED_EX + Back.RESET + f'Caso 1 Copia en zCollaboration: {file_name} -> {collaboration_folder}')

            # Caso 2: Canciones de un álbum con un solo artista común 
            elif is_artista_album: 
                main_artist = list(common_artists)[0] 
                artist_folder = os.path.join(organized_folder, "Artist", clean_name(replace_slashes(main_artist))) 
                album_folder = os.path.join(artist_folder, album) 
                os.makedirs(album_folder, exist_ok=True) 
                if not is_duplicate(album_folder, file_name): 
                    shutil.copy(file_path, os.path.join(album_folder, file_name)) 
                    print(Fore.GREEN + Back.RESET + f'Caso 2 Movido "{main_artist}" (álbum único artista común): {file_name} -> {album_folder}')

                # Copia adicional para colaboradores 
                for artist in artists: 
                    if artist != main_artist: 
                        collaboration_folder = os.path.join(organized_folder, "Artist", clean_name(replace_slashes(artist)), "zCollaboration") 
                        os.makedirs(collaboration_folder, exist_ok=True) 
                        if not is_duplicate(collaboration_folder, file_name): 
                            shutil.copy(file_path, os.path.join(collaboration_folder, file_name)) 
                            print(Fore.LIGHTGREEN_EX + Back.RESET + f'Caso 2 Copia en zCollaboration: {file_name} -> {collaboration_folder}')

            # Caso 3: Canciones sin álbum o con un solo track 
            elif is_artista_single: 
                # Copia adicional para artistas individuales 
                if len(set(artists)) == 1: 
                    single_folder = os.path.join(organized_folder, "Artist", clean_name(replace_slashes(artists[0])), "zSingle") 
                    os.makedirs(single_folder, exist_ok=True) 
                    if not is_duplicate(single_folder, file_name): 
                        shutil.copy(file_path, os.path.join(single_folder, file_name)) 
                        print(Fore.BLUE + Back.RESET + f'Caso 3 Copia "{artists[0]}" en zSingle: {file_name} -> {single_folder}') 
                else: 
                    for artist in artists: 
                        # Si el artista principal está acompañado de un colaborador 
                        collaboration_folder = os.path.join(organized_folder, "Artist", clean_name(replace_slashes(artist)), "zCollaboration") 
                        os.makedirs(collaboration_folder, exist_ok=True) 
                        if not is_duplicate(collaboration_folder, file_name): 
                            shutil.copy(file_path, os.path.join(collaboration_folder, file_name)) 
                            print(Fore.LIGHTBLUE_EX + Back.RESET + f'Caso 3 Copia en zCollaboration: {file_name} -> {collaboration_folder}') 
            
            # Caso 4: Canciones sin artista o álbum definido 
            else: 
                random_folder = os.path.join(organized_folder, "Random") 
                os.makedirs(random_folder, exist_ok=True) 
                if not is_duplicate(random_folder, file_name): 
                    shutil.copy(file_path, os.path.join(random_folder, file_name)) 
                    print(f'Movido 4 a Random: {file_name} -> {random_folder}')


    print(Fore.CYAN + Back.LIGHTCYAN_EX + "Organización completa."+ Back.RESET)


# Carpeta de descargas y carpeta organizada
download_folder = "C:/Users/pilon/Downloads/Telegram Desktop"
organized_folder = "C:/Users/pilon/Music/PILON MUSIC"

# Llamar a la función para organizar la música
organize_music(download_folder, organized_folder)
