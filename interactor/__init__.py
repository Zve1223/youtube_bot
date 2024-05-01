import asyncio

from youtubesearchpython import VideosSearch
from pytube import YouTube
import moviepy.editor as mp
import os
import cv2
import requests
import subprocess

main_folder = os.path.abspath('./files')
video_path = os.path.join(main_folder, 'video')
video_clip_path = os.path.join(main_folder, 'video_clip')
audio_path = os.path.join(main_folder, 'audio')
audio_clip_path = os.path.join(main_folder, 'audio_clip')
frame_path = os.path.join(main_folder, 'frame')
preview_path = os.path.join(main_folder, 'preview')

directions = [video_path, video_clip_path, audio_path, audio_clip_path, frame_path, preview_path]


# Вспомогательная функция для вычисления размера всех файлов
def get_files_size() -> int:
    total_size = 0
    for path, _, files in os.walk(main_folder):
        for file in files:
            filepath = os.path.join(path, file)
            total_size += os.path.getsize(filepath)
    return total_size


# Проверяет на существоание всех папок, если их нет - создаёт
def check_dirs() -> None:
    print('--Начало проверки на наличие всех рабочих папок')
    for direction in directions:
        if not os.path.exists(direction):
            os.makedirs(direction)
            print(f'----Папка {direction} была успешно создана')
    print('--Все недостающие папки были успешно созданы\n\n')


# Очищает все папки
def clear() -> None:
    print('--Начало очистки всех рабочих папок')
    for direction in directions:
        print(f'----Начало очистки папки по пути {direction}')
        for filename in os.listdir(direction):
            filepath = os.path.join(direction, filename)
            os.remove(filepath)
            print(f'------Файл {filename} по пути {filepath} был успешно удалён')
        print(f'----Папка по пути {direction} была успешно очищена')

    print('--Все рабочие папки были успешно очищены\n\n')


# Вспомогательная функция для перевода временной точки в миллисекунды
def to_ms(hours: int = 0, minutes: int = 0, seconds: int = 0, milliseconds: int = 0) -> int:
    return hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds


# Вспомогательная функция для перевода миллисекунд в строковый вид
def from_ms(ms: int) -> str:
    return f'{ms // 3600000}:{ms % 3600000 // 60000}:{ms % 60000 // 1000}.{ms % 1000}'


# Вспомогательная функция для вычисления приблизительной (неточной!) длительности видео в миллисекундах
def check_duration(video) -> int:
    duration = list(map(int, video['duration'].split(':'))) + [0]
    return to_ms(*([0] * (4 - len(duration)) + duration))


# Вспомогательная функция для проверки, чтобы временные точки не выходили за границы видео,
# и в случае необходимости их подгонки под эти границы
def check_borders(result: str, start: int, end: int, duration: int) -> tuple[str, int, int]:
    if start > end:
        s = f'Начальное значение позиции превышает конечное\n' \
            f'(start = {from_ms(start).replace(".", ":")}, end = {from_ms(end).replace(".", ":")})'
        print('----' + s.replace('\n', ' '))
        result += f'\n\n{s}'

        start, end = end, start

        s = 'Значение позиции начального и последнего кадров были подменены местами'
        print(f'----{s}')
        result += f'\n{s}'

    if start > duration:
        s = f'Значение позиции начального кадра слишком большое\n' \
            f'(start = {from_ms(start).replace(".", ":")}, max = {from_ms(duration).replace(".", ":")})'
        print('----' + s.replace('\n', ' '))
        result += f'\n\n{s}'

        start = max(0, duration - 10000)

        s = f'Значение позиции начального кадра установлено на десять секунд до конца видео'
        print(f'----{s}')
        result += f'\n{s}'

    if end > duration:
        s = f'Значение позиции начального кадра слишком большое\n' \
            f'(end = {from_ms(end).replace(".", ":")}, max = {from_ms(duration).replace(".", ":")})'
        print('----' + s.replace('\n', ' '))
        result += f'\n\n{s}'

        end = duration

        s = 'Значение позиции конечного кадра установлено на конец видео'
        print(f'----{s}')
        result += f'\n{s}'

    return result, start, end


# Хрен знает что делает этот заголовок, но способ скачивания без pytube работает только с ним
headers = {
    'authority': 'downloader.freemake.com',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Yandex";v="22"',
    'dnt': '1',
    'x-cf-country': 'RU',
    'sec-ch-ua-mobile': '?0',
    'x-user-platform': 'Win32',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'x-user-browser': 'YaBrowser',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/98.0.4758.141 YaBrowser/22.3.3.852 Yowser/2.5 Safari/537.36',
    'x-analytics-header': 'UA-18256617-1',
    'x-request-attempt': '1',
    'x-user-id': '94119398-e27a-3e13-be17-bbe7fbc25874',
    'sec-ch-ua-platform': '"Windows"',
    'origin': 'https://www.freemake.com',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.freemake.com/ru/free_video_downloader/',
    'accept-language': 'ru,en;q=0.9,uk;q=0.8',
}


# Скачивает видео в папку по пути video_path с названием в виде id видео в самом YouTube
async def download_video(video) -> tuple[str, int]:
    print(f'--Начало скачивания видео "{video["title"]}"')

    title = video['id'] + '.mp4'
    filepath = os.path.join(video_path, title)

    while os.path.exists(filepath):
        await asyncio.sleep(0.25)

    # Получение ссылки на видео
    response = requests.get(f'https://downloader.freemake.com/api/videoinfo/{video["id"]}', headers=headers).json()
    url = response['qualities'][0]['url']
    req = requests.get(url=url, headers=headers, stream=True)

    # Скачивание видео под тем же названием, что и в YouTube
    with open(filepath, 'wb') as file:
        file.write(req.content)
        file.close()

    print(f'--Видео было успешно сохранено по пути {filepath}\n\n')

    quality = response['qualities'][0]['qualityInfo']['qualityLabel']
    video_clip = mp.VideoFileClip(filepath)
    duration = round(video_clip.duration * 1000)
    video_clip.audio.close()
    video_clip.close()
    del video_clip.reader
    del video_clip
    return 'Видео с разрешением ' + quality, duration


# Вырезает видео-фрагмент и сохраняет в папку по пути video_clip_path с названием в виде id видео в самом YouTube и
# миллисекунд начала и конца фрагмента из оригинального видео
async def download_video_clip(video, start: int, end: int) -> str:
    print(f'--Начало скачивания и обрезки видео "{video["title"]}"')

    title = f'{video["id"]}_{start}-{end}.mp4'
    filepath = os.path.join(video_clip_path, title)

    while os.path.exists(filepath):
        await asyncio.sleep(0.25)

    # Скачивание видео для дальнейшего выреза из него фрагмента
    result, video_duration = await download_video(video)

    result, start, end = check_borders(result, start, end, video_duration)

    subprocess.run(['ffmpeg', '-i', os.path.join(video_path, video['id'] + '.mp4'),
                    '-ss', from_ms(start), '-to', from_ms(end), '-c', 'copy', filepath], check=True)

    print(f'--Видео-фрагмент был успешно сохранён по пути {filepath}\n\n')
    return result


# Скачивает audio в папку по пути video_path с названием в виде id видео в самом YouTube
async def download_audio(video) -> None:
    print(f'--Начало скачивания аудио из видео "{video["title"]}"')

    title = video['id'] + '.mp3'
    filepath = os.path.join(audio_path, title)

    while os.path.exists(filepath):
        await asyncio.sleep(0.25)

    # Скачивание видео для дальнейшего выреза из него аудиодорожки
    await download_video(video)

    # Импорт видео, вырез аудио и его сохранение
    video_clip = mp.VideoFileClip(os.path.join(video_path, video['id'] + '.mp4'))
    video_clip.audio.write_audiofile(filepath)
    video_clip.audio.close()
    video_clip.close()
    del video_clip.reader
    del video_clip

    print(f'--Аудио было успешно сохранено по пути {filepath}\n\n')


# Вырезает аудио-фрагмент и сохраняет в папку по пути audio_clip_path с названием в виде id видео в самом YouTube и
# миллисекунд начала и конца фрагмента из оригинального аудио
async def download_audio_clip(video, start: int, end: int) -> str:
    print(f'--Начало скачивания и обрезки аудио из видео "{video["title"]}"')

    title = f'{video["id"]}_{start}-{end}.mp3'
    filepath = os.path.join(audio_clip_path, title)

    while os.path.exists(filepath):
        await asyncio.sleep(0.25)

    _, video_duration = await download_video(video)

    result, start, end = check_borders('', start, end, video_duration)

    # Импорт видео-фрагмента, вырез и сохранение аудио-фрагмента
    video_clip = mp.VideoFileClip(os.path.join(video_path, video['id'] + '.mp4'))
    video_clip.audio.subclip(start / 1000, end / 1000).write_audiofile(filepath)
    video_clip.audio.close()
    video_clip.close()
    del video_clip.reader
    del video_clip

    print(f'--Аудио-фрагмент был успешно сохранён по пути {filepath}\n\n')

    return result


# Скачивает frame в папку по пути frame_path с названием в виде id видео в самом YouTube
async def download_frame(video, frame_time: int) -> str:
    print(f'--Начало скачивания кадра видео "{video["title"]}"')

    title = f'{video["id"]}_{frame_time}.png'
    filepath = os.path.join(frame_path, title)

    while os.path.exists(filepath):
        await asyncio.sleep(0.25)

    result, video_duration = await download_video(video)

    if frame_time > video_duration:
        s = f'Значение позиции начального кадра слишком большое\n' \
            f'(start = {from_ms(frame_time).replace(".", ":")}, max = {from_ms(video_duration).replace(".", ":")})'
        print('----' + s.replace('\n', ' '))
        result += f'\n\n{s}'

        frame_time = video_duration - 1000

        s = f'Значение позиции начального кадра установлено на секунду до конца видео'
        print(f'----{s}')
        result += f'\n{s}'

    # Скачивание видео для дальнейшего выреза из него кадра

    # Вырезка кадра
    cap = cv2.VideoCapture(os.path.join(video_path, video['id'] + '.mp4'))
    cap.set(cv2.CAP_PROP_POS_MSEC, frame_time)
    success, frame = cap.read()
    cap.release()
    cv2.imwrite(filepath, frame)

    print(f'--Кадр был успешно вырезан и сохранён по пути {filepath}\n\n')

    return 'Кадр с разрешением ' + result.split('\n')[0].split()[-1] + '\n' + '\n'.join(result.split('\n')[1:])


# Скачивает preview в папку по пути preview_path с названием в виде id видео в самом YouTube
async def download_preview(video) -> None:
    print(f'--Начало скачивания превью видео "{video["title"]}"')

    title = video['id'] + '.png'
    filepath = os.path.join(preview_path, title)

    while os.path.exists(filepath):
        await asyncio.sleep(0.25)

    # Ссылка на превью
    thumbnail_url = f'https://i.ytimg.com/vi/{video["id"]}/maxresdefault.jpg'

    # Получение и скачивание превью
    response = requests.get(thumbnail_url)
    with open(filepath, 'wb') as file:
        file.write(response.content)

    print(f'--Превью было успешно скачено по пути {filepath}\n\n')


# Выводит подробную информацию о видео
async def get_info(video) -> str:
    if video['descriptionSnippet']:
        description = ''.join(i['text'] for i in video['descriptionSnippet'])
    else:
        description = 'Отсутствует'

    info = f'''
Название: {video['title']}

ID видео: {video['id']}

Ссылка на видео: {video['link']}

Длительность: {video['duration']}

Время публикации: {YouTube(video['link']).publish_date}

Описание: {description}

Количество просмотров: {video['viewCount']['text']}

Превью: {f'https://i.ytimg.com/vi/{video["id"]}/maxresdefault.jpg'}


Название канала: {video['channel']['name']}

ID канала: {video['channel']['id']}

Ссылка на канал: {video['channel']['link']}
'''
    return info


# Функция, возвращающая словарь, имеющий необходимую функциям информацию о видео
async def link_search(link: str) -> dict:
    # Если на входе дана ссылка, подгоняем result к формату VideoSearch(...).result()['result'][0]
    # Подробнее на https://stackoverflow.com/questions/62779030/youtube-search-on-python-3-8

    video = YouTube(link)
    views = ','.join([str(video.views)[::-1][i:i + 3] for i in range(0, len(str(video.views)), 3)][::-1])
    if video.description:
        description = video.description
    else:
        description = '[Link does not contain information about the description]'

    result = {
        'title': video.title,
        'id': video.video_id,
        'link': link,
        'duration': f'{video.length // 3600}:{video.length % 3600 // 60}:{video.length % 60}',
        'descriptionSnippet': [{'text': description}],
        'viewCount': {'text': views + ' views'},
        'channel': {'name': video.author, 'id': video.channel_id, 'link': video.channel_url}
    }
    return result


# Функция, возвращающая словарь, имеющий необходимую функциям информацию о видео
async def title_search(title: str) -> tuple[list, str]:
    results = VideosSearch(title, limit=10).result()['result']
    table = '\n\n'.join([f'{i + 1}.\n'
                         f'Название: {results[i]["title"]}\n'
                         f'Автор:    {results[i]["channel"]["name"]}' for i in range(len(results))])

    return results, table
