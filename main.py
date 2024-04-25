from interactor import *
from states import *

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InputFile, \
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import re

MEMORY_STORAGE = MemoryStorage()

TOKEN = '6187836302:AAE7-3Eue2LrEZYHK89FzaUvHTqy7FRB3bQ'
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MEMORY_STORAGE)

OPTIONS = '''/video — Скачать видео из YouTube
/audio — Скачать аудио-дорожку
/v_clip — Скачать видео-клип
/a_clip — Скачать аудио-клип
/preview — Скачать превью видео
/frame — Скачать кадр из видео
/info — Получить инфо о видео

/back - Отменить все действия'''

main_keyboard = ReplyKeyboardMarkup()
main_keyboard.row(KeyboardButton('/help'))
main_keyboard.row(KeyboardButton('/video'),
                  KeyboardButton('/audio'),
                  KeyboardButton('/preview'))
main_keyboard.row(KeyboardButton('/v_clip'),
                  KeyboardButton('/a_clip'),
                  KeyboardButton('/frame'))
main_keyboard.add(KeyboardButton('/info'))

help_keyboard = InlineKeyboardMarkup()
help_keyboard.row(InlineKeyboardButton('🖥 /video', callback_data='/video'),
                  InlineKeyboardButton('🎹 /audio', callback_data='/audio'),
                  InlineKeyboardButton('🖼 /preview', callback_data='/preview'))
help_keyboard.row(InlineKeyboardButton('📼✂ /v_clip', callback_data='/v_clip'),
                  InlineKeyboardButton('🎧✂ /a_clip', callback_data='/a_clip'),
                  InlineKeyboardButton('🎞✂ /frame', callback_data='/frame'))
help_keyboard.add(InlineKeyboardButton('ℹ /info', callback_data='/info'))

back_keyboard = InlineKeyboardMarkup()
back_keyboard.add(InlineKeyboardButton('🔙 /back', callback_data='/back'))


async def start_command(message: Message) -> None:
    with open('users.txt', 'r', encoding='UTF-8') as file:
        users = file.read()

    if str(message.from_id) not in users.split('\n'):
        users += '\n' + str(message.from_id)
        await message.answer('Вот, что я могу:\n\n' + OPTIONS, reply_markup=main_keyboard)

    with open('users.txt', 'w', encoding='UTF-8') as file:
        file.write(users.strip())


async def help_command(message: Message) -> None:
    await message.answer('Вот, что я могу:\n\n' + OPTIONS, reply_markup=help_keyboard)


# ----------------Блок функций для команд админов----------------


async def count_command(message: Message) -> None:
    if await is_admin(message.from_id):
        with open('users.txt', 'r') as file:
            await message.answer(f'Участников, опробовавших бота: {len(file.readlines())}')


async def size_command(message: Message) -> None:
    if await is_admin(message.from_id):
        await message.answer(f'Размер всех временных файлов на текущий момент: {get_files_size()} байт')


async def clear_command(message: Message) -> None:
    if await is_admin(message.from_id):
        clear()
        await message.answer('Все временные файлы были успешно удалены')


# ----------------Блок вспомогательных функций----------------


# Вспомогательная функция для проверки является ли пользователь админом по его id
async def is_admin(user_id: int) -> bool:
    async with open('admins.txt', 'r') as file:
        return str(user_id) in map(lambda s: s.split('#')[0].strip(), file.read().split('\n'))


# Вспомогательная функция для вычисления способа поиска видео (ссылка/название)
async def get_video(message: str) -> dict | tuple[list, str]:
    if '/'.join(message.split('/')[:3]) in ['https://www.youtube.com', 'https://youtu.be', 'https://youtube.com']:
        video = await link_search(message)
        return video
    else:
        results, table = await title_search(message)
        return results, table


# Вспомогательная функция для проверки корректности сообщения (содержит ли оно число от 1 до 10 включительно)
async def is_correct(message: Message, limit: int) -> bool:
    if not message.text.strip().isdigit():
        await message.answer(f'"{message.text.strip()}" не является целым числом, попробуйте снова',
                             reply_markup=back_keyboard)
        return False

    n = int(message.text.strip()) - 1

    if n not in range(limit):
        await message.answer('Число превышает допустимое значение (от 1 до 10 включительно), попробуйте снова',
                             reply_markup=back_keyboard)
        return False

    return True


# ----------------Блок функций для команды /video----------------


async def send_video(message: Message, video: dict) -> None:
    temp = await message.answer('Начало скачивания видео...')

    try:
        result, _ = await download_video(video)

        filename = video['id'] + '.mp4'
        filepath = os.path.join(video_path, filename)
        filename = video['title'] + '.mp4'
        file = InputFile(filepath, filename=filename)
    except ValueError:
        await temp.delete()
        await message.answer('Что-то пошло не так...')
        return

    await message.answer_video(file)
    await temp.delete()
    await message.answer(result)

    os.remove(filepath)


async def video_command(message: Message) -> None:
    await VideoSteps.GET_LINK.set()
    await message.answer('Введите ссылку или название видео',
                         reply_markup=back_keyboard)


async def video_get_link(message: Message, state: FSMContext) -> None:
    try:
        result = await get_video(message.text)
    except ValueError:
        await message.answer('При поиске видео возникли проблемы, попробуйте снова',
                             reply_markup=back_keyboard)
        return

    if isinstance(result, dict):
        await send_video(message, result)
        await state.finish()
    else:
        await VideoSteps.GET_BY_TITLE.set()

        videos, table = result
        temp = await message.answer('Выберите видео (введите его номер):\n\n' + table,
                                    reply_markup=back_keyboard)
        async with state.proxy() as data:
            data['videos'] = videos
            data['temp'] = temp


async def video_get_by_title(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if await is_correct(message, len(data['videos'])) is False:
            return

    n = int(message.text.strip()) - 1

    async with state.proxy() as data:
        video = data['videos'][n]

    await send_video(message, video)

    async with state.proxy() as data:
        await data['temp'].delete()
        await message.delete()

    await state.finish()


# ----------------Блок функций для команды /v_clip----------------


async def send_v_clip(message: Message, m: list) -> None:
    temp = await message.answer('Начало скачивания видео-клипа...')

    video, start, end = m

    try:
        start = to_ms(*map(int, start.split(':')))
        end = to_ms(*map(int, end.split(':')))
        result = await download_video_clip(video, start, end)

        filename = video['id'] + '_' + str(start) + '-' + str(end) + '.mp4'
        filepath = os.path.join(video_clip_path, filename)
        filename = video['title'] + '_' + str(start) + '-' + str(end) + '.mp4'
        file = InputFile(filepath, filename=filename)
    except ValueError:
        await temp.delete()
        await message.answer('Что-то пошло не так...')
        return

    await message.answer_video(file)
    await temp.delete()
    await message.answer(result)

    os.remove(filepath)
    os.remove(os.path.join(video_path, video['id'] + '.mp4'))


async def v_clip_command(message: Message) -> None:
    await VideoClipSteps.GET_LINK.set()
    await message.answer('Введите ссылку или название видео',
                         reply_markup=back_keyboard)


async def v_clip_next_state(message: Message, state: FSMContext, video: dict) -> None:
    async with state.proxy() as data:
        data['video'] = video

    await VideoClipSteps.GET_TIME_FROM.set()
    await message.answer('Теперь введите время, от которого будет начинаться клип, формата [ЧЧ:ММ:СС:МС]\n'
                         'Пример: 0:1:22:30',
                         reply_markup=back_keyboard)


async def v_clip_get_link(message: Message, state: FSMContext) -> None:
    try:
        result = await get_video(message.text.strip())
    except ValueError:
        await message.answer('При поиске видео возникли некоторые проблемы...')
        return

    if isinstance(result, dict):
        await v_clip_next_state(message, state, result)
    else:
        await VideoClipSteps.GET_BY_TITLE.set()
        videos, table = result
        temp = await message.answer('Выберите видео (введите его номер):\n\n' + table,
                                    reply_markup=back_keyboard)
        async with state.proxy() as data:
            data['videos'] = videos
            data['temp'] = temp


async def v_clip_get_by_title(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if await is_correct(message, len(data['videos'])) is False:
            return

        n = int(message.text.strip()) - 1

        await v_clip_next_state(message, state, data['videos'][n])

    async with state.proxy() as data:
        await data['temp'].delete()
        await message.delete()


async def v_clip_get_time_from(message: Message, state: FSMContext) -> None:
    if not re.match(r'\d{1,2}:\d{1,2}:\d{1,2}:\d{1,3}', message.text.strip()):
        await message.answer('Вы ввели некорректный формат времени, попробуйте ещё раз',
                             reply_markup=back_keyboard)
        return

    async with state.proxy() as data:
        data['time_from'] = message.text.strip()

    await VideoClipSteps.GET_TIME_TO.set()
    await message.answer('А теперь введите время, до которого будет идти клип, формата [ЧЧ:ММ:СС:МС]\n'
                         'Пример: 0:23:34:0',
                         reply_markup=back_keyboard)


async def v_clip_get_time_to(message: Message, state: FSMContext) -> None:
    if not re.match(r'\d{1,2}:\d{1,2}:\d{1,2}:\d{1,3}', message.text.strip()):
        await message.answer('Вы ввели некорректный формат времени, попробуйте ещё раз',
                             reply_markup=back_keyboard)
        return

    async with state.proxy() as data:
        await send_v_clip(message, [data['video'], data['time_from'], message.text.strip()])

    await state.finish()


# ----------------Блок функций для команды /audio----------------


async def send_audio(message: Message, video: dict) -> None:
    temp = await message.answer('Начало скачивания аудио...')

    try:
        await download_audio(video)

        filename = video['id'] + '.mp3'
        filepath = os.path.join(audio_path, filename)
        filename = video['title'] + '.mp3'
        file = InputFile(filepath, filename=filename)
    except ValueError:
        await temp.delete()
        await message.answer('Что-то пошло не так...')
        return

    await message.answer_audio(file)
    await temp.delete()

    os.remove(filepath)
    os.remove(os.path.join(video_path, video['id'] + '.mp4'))


async def audio_command(message: Message) -> None:
    await AudioSteps.GET_LINK.set()
    await message.answer('Введите ссылку или название видео',
                         reply_markup=back_keyboard)


async def audio_get_link(message: Message, state: FSMContext) -> None:
    try:
        result = await get_video(message.text.strip())
    except ValueError:
        await message.answer('При поиске видео возникли некоторые проблемы, попробуйте снова',
                             reply_markup=back_keyboard)
        return

    if isinstance(result, dict):
        await send_audio(message, result)
        await state.finish()
    else:
        await AudioSteps.GET_BY_TITLE.set()

        videos, table = result
        temp = await message.answer('Выберите видео (введите его номер):\n\n' + table,
                                    reply_markup=back_keyboard)
        async with state.proxy() as data:
            data['videos'] = videos
            data['temp'] = temp


async def audio_get_by_title(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if await is_correct(message, len(data['videos'])) is False:
            return

        n = int(message.text.strip()) - 1

        video = data['videos'][n]

    await send_audio(message, video)

    async with state.proxy() as data:
        await data['temp'].delete()
        await message.delete()

    await state.finish()


# ----------------Блок функций для команды /a_clip----------------


async def send_a_clip(message: Message, m: list) -> None:
    temp = await message.answer('Начало скачивания аудио-клипа...')

    video, start, end = m

    try:
        start = to_ms(*map(int, start.split(':')))
        end = to_ms(*map(int, end.split(':')))
        await download_audio_clip(video, start, end)

        filename = video['id'] + '_' + str(start) + '-' + str(end) + '.mp3'
        filepath = os.path.join(audio_clip_path, filename)
        filename = video['title'] + '_' + str(start) + '-' + str(end) + '.mp3'
        file = InputFile(filepath, filename=filename)
    except ValueError:
        await temp.delete()
        await message.answer('Что-то пошло не так...')
        return

    await message.answer_audio(file)
    await temp.delete()

    os.remove(filepath)
    os.remove(os.path.join(video_path, video['id'] + '.mp4'))


async def a_clip_command(message: Message) -> None:
    await AudioClipSteps.GET_LINK.set()
    await message.answer('Введите ссылку или название видео',
                         reply_markup=back_keyboard)


async def a_clip_next_state(message: Message, state: FSMContext, video: dict) -> None:
    async with state.proxy() as data:
        data['video'] = video

    await AudioClipSteps.GET_TIME_FROM.set()
    await message.answer('Теперь введите время, от которого будет начинаться клип, формата [ЧЧ:ММ:СС:МС]\n'
                         'Пример: 0:1:22:30',
                         reply_markup=back_keyboard)


async def a_clip_get_link(message: Message, state: FSMContext) -> None:
    try:
        result = await get_video(message.text.strip())
    except ValueError:
        await message.answer('При поиске видео возникли некоторые проблемы, попробуйте снова',
                             reply_markup=back_keyboard)
        return

    if isinstance(result, dict):
        await a_clip_next_state(message, state, result)
    else:
        await AudioClipSteps.GET_BY_TITLE.set()

        videos, table = result
        temp = await message.answer('Выберите видео (введите его номер):\n\n' + table,
                                    reply_markup=back_keyboard)
        async with state.proxy() as data:
            data['videos'] = videos
            data['temp'] = temp


async def a_clip_get_by_title(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if await is_correct(message, len(data['videos'])) is False:
            return

        n = int(message.text.strip()) - 1

        await a_clip_next_state(message, state, data['videos'][n])

        await data['temp'].delete()
        await message.delete()


async def a_clip_get_time_from(message: Message, state: FSMContext) -> None:
    if not re.match(r'\d{1,2}:\d{1,2}:\d{1,2}:\d{1,3}', message.text.strip()):
        await message.answer('Вы ввели некорректный формат времени, попробуйте ещё раз',
                             reply_markup=back_keyboard)
        return

    async with state.proxy() as data:
        data['time_from'] = message.text.strip()

    await AudioClipSteps.GET_TIME_TO.set()
    await message.answer('А теперь введите время, до которого будет идти клип, формата [ЧЧ:ММ:СС:МС]\n'
                         'Пример: 0:23:34:0',
                         reply_markup=back_keyboard)


async def a_clip_get_time_to(message: Message, state: FSMContext) -> None:
    if not re.match(r'\d{1,2}:\d{1,2}:\d{1,2}:\d{1,3}', message.text.strip()):
        await message.answer('Вы ввели некорректный формат времени, попробуйте ещё раз',
                             reply_markup=back_keyboard)
        return

    async with state.proxy() as data:
        await send_a_clip(message, [data['video'], data['time_from'], message.text.strip()])

    await state.finish()


# ----------------Блок функций для команды /frame----------------


async def send_frame(message: Message, m: list) -> None:
    temp = await message.answer('Начало скачивания кадра...')

    video, frame_time = m

    try:
        frame_time = to_ms(*map(int, frame_time.split(':')))
        result = await download_frame(video, frame_time)

        filename = video['id'] + '_' + str(frame_time) + '.png'
        filepath = os.path.join(frame_path, filename)
        filename = video['title'] + '_' + str(frame_time) + '.png'
        file = InputFile(filepath, filename=filename)
    except ValueError:
        await temp.delete()
        await message.answer('Что-то пошло не так...')
        return

    await message.answer_photo(file)
    await temp.delete()
    await message.answer(result)

    os.remove(filepath)
    os.remove(os.path.join(video_path, video['id'] + '.mp4'))


async def frame_command(message: Message) -> None:
    await FrameSteps.GET_LINK.set()
    await message.answer('Введите ссылку или название видео',
                         reply_markup=back_keyboard)


async def frame_next_state(message: Message, state: FSMContext, video: dict) -> None:
    async with state.proxy() as data:
        data['video'] = video

    await FrameSteps.GET_FRAME_TIME.set()
    await message.answer('Теперь введите время кадра формата [ЧЧ:ММ:СС:МС]\n'
                         'Пример: 00:0:32:512',
                         reply_markup=back_keyboard)


async def frame_get_link(message: Message, state: FSMContext) -> None:
    try:
        result = await get_video(message.text.strip())
    except ValueError:
        await message.answer('При поиске видео возникли некоторые проблемы, попробуйте снова',
                             reply_markup=back_keyboard)
        return

    if isinstance(result, dict):
        await frame_next_state(message, state, result)
    else:
        await FrameSteps.GET_BY_TITLE.set()

        videos, table = result
        temp = await message.answer('Выберите видео (введите его номер):\n\n' + table,
                                    reply_markup=back_keyboard)
        async with state.proxy() as data:
            data['videos'] = videos
            data['temp'] = temp


async def frame_get_by_title(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if await is_correct(message, len(data['videos'])) is False:
            return

        n = int(message.text.strip()) - 1

        await frame_next_state(message, state, data['videos'][n])

        await data['temp'].delete()
        await message.delete()


async def frame_get_frame_time(message: Message, state: FSMContext) -> None:
    if not re.match(r'\d{1,2}:\d{1,2}:\d{1,2}:\d{1,3}', message.text.strip()):
        await message.answer('Вы ввели некорректный формат времени, попробуйте ещё раз',
                             reply_markup=back_keyboard)
        return

    async with state.proxy() as data:
        await send_frame(message, [data['video'], message.text.strip()])

    await state.finish()


# ----------------Блок функций для команды /preview----------------


async def send_preview(message: Message, video: dict) -> None:
    temp = await message.answer('Начало скачивания превью...')

    try:
        await download_preview(video)

        filename = video['id'] + '.png'
        filepath = os.path.join(preview_path, filename)
        filename = video['title'] + '.png'
        file = InputFile(filepath, filename=filename)
    except ValueError:
        await temp.delete()
        await message.answer('Что-то пошло не так...')
        return

    await message.answer_photo(file)
    await temp.delete()

    os.remove(filepath)


async def preview_command(message: Message) -> None:
    await PreviewSteps.GET_LINK.set()
    await message.answer('Введите ссылку или название видео',
                         reply_markup=back_keyboard)


async def preview_get_link(message: Message, state: FSMContext) -> None:
    try:
        result = await get_video(message.text.strip())
    except ValueError:
        await message.answer('При поиске видео возникли некоторые проблемы, попробуйте снова',
                             reply_markup=back_keyboard)
        return

    if isinstance(result, dict):
        await send_preview(message, result)
        await state.finish()
    else:
        await PreviewSteps.GET_BY_TITLE.set()

        videos, table = result
        temp = await message.answer('Выберите видео (введите его номер):\n\n' + table,
                                    reply_markup=back_keyboard)
        async with state.proxy() as data:
            data['videos'] = videos
            data['temp'] = temp


async def preview_get_by_title(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if await is_correct(message, len(data['videos'])) is False:
            return

        n = int(message.text.strip()) - 1

        video = data['videos'][n]

        await send_preview(message, video)

        await data['temp'].delete()
        await message.delete()

    await state.finish()


# ----------------Блок функций для команды /info----------------


async def send_info(message: Message, video) -> None:
    temp = await message.answer('Начало получения информации...')

    result = await get_info(video)

    await temp.delete()
    await message.answer(result)


async def info_command(message: Message) -> None:
    await InfoSteps.GET_LINK.set()
    await message.answer('Введите ссылку или название видео',
                         reply_markup=back_keyboard)


async def info_get_link(message: Message, state: FSMContext) -> None:
    try:
        result = await get_video(message.text.strip())
    except ValueError:
        await message.answer('При поиске видео возникли некоторые проблемы, попробуйте снова',
                             reply_markup=back_keyboard)
        return

    if isinstance(result, dict):
        await send_info(message, result)
        await state.finish()
    else:
        await InfoSteps.GET_BY_TITLE.set()

        videos, table = result
        temp = await message.answer('Выберите видео (введите его номер):\n\n' + table,
                                    reply_markup=back_keyboard)
        async with state.proxy() as data:
            data['videos'] = videos
            data['temp'] = temp


async def info_get_by_title(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if await is_correct(message, len(data['videos'])) is False:
            return

        n = int(message.text.strip()) - 1

        video = data['videos'][n]

        await send_info(message, video)

        await data['temp'].delete()
        await message.delete()

    await state.finish()


async def choose_by_button(call: CallbackQuery, state: FSMContext) -> None:
    await back_command(call.message, state)
    match call.data:
        case '/video':
            await video_command(call.message)
        case '/v_clip':
            await v_clip_command(call.message)
        case '/audio':
            await audio_command(call.message)
        case '/a_clip':
            await a_clip_command(call.message)
        case '/frame':
            await frame_command(call.message)
        case '/preview':
            await preview_command(call.message)
        case '/info':
            await info_command(call.message)
        case '/help':
            await help_command(call.message)
    await call.answer()


# ----------------Блок функций для общего случая (когда отправляют название/ссылку просто так)----------------


async def general_get_link(message: Message, state: FSMContext) -> None:
    try:
        result = await get_video(message.text.strip())
    except ValueError:
        await message.answer('При поиске видео возникли некоторые проблемы, попробуйте снова',
                             reply_markup=back_keyboard)
        return

    if isinstance(result, dict):
        await GeneralSteps.CHOOSE_OPTION.set()
        await message.answer('Выберите действие:\n\n' + OPTIONS, reply_markup=help_keyboard)
        async with state.proxy() as data:
            data['video'] = result
    else:
        await GeneralSteps.GET_BY_TITLE.set()

        videos, table = result
        temp = await message.answer('Выберите видео (введите его номер):\n\n' + table,
                                    reply_markup=back_keyboard)
        async with state.proxy() as data:
            data['videos'] = videos
            data['temp'] = temp


async def general_get_by_title(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if await is_correct(message, len(data['videos'])) is False:
            return

        n = int(message.text.strip()) - 1

        video = data['videos'][n]

        await GeneralSteps.CHOOSE_OPTION.set()
        await message.answer('Выберите действие:\n\n' + OPTIONS, reply_markup=help_keyboard)

        data['video'] = video

        await data['temp'].delete()
        await message.delete()


async def general_choose(command: str, message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        match command:
            case '/video':
                await send_video(message, data['video'])
                await state.finish()
            case '/v_clip':
                await VideoClipSteps.GET_TIME_FROM.set()
            case '/audio':
                await send_audio(message, data['video'])
                await state.finish()
            case '/a_clip':
                await AudioClipSteps.GET_TIME_FROM.set()
            case '/frame':
                await FrameSteps.GET_FRAME_TIME.set()
            case '/preview':
                await send_preview(message, data['video'])
                await state.finish()
            case '/info':
                await send_info(message, data['video'])
                await state.finish()


async def general_message_choose(message: Message, state: FSMContext) -> None:
    await general_choose(message.text, message, state)


async def general_button_choose(call: CallbackQuery, state: FSMContext) -> None:
    await general_choose(call.data, call.message, state)
    await call.answer()


# Функция для возврата к первоначальному машинному состоянию
async def back_command(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.delete()
        return
    await state.finish()
    await message.answer('Все действия успешно отменены')
    await message.delete()


# ----------------Блок стартовых функций----------------


# Функция для регистрации всех хендлеров
def register_all_handlers() -> None:
    dp.register_message_handler(start_command, commands=['start'], state=None)

    dp.register_message_handler(back_command, commands=['back'], state='*')

    dp.register_message_handler(help_command, commands=['help'], state=None)

    dp.register_message_handler(count_command, commands=['count'], state=None)
    dp.register_message_handler(size_command, commands=['size'], state=None)
    dp.register_message_handler(clear_command, commands=['clear'], state=None)

    dp.register_message_handler(video_command, commands=['video'], state=None)
    dp.register_message_handler(video_get_link, state=VideoSteps.GET_LINK)
    dp.register_message_handler(video_get_by_title, state=VideoSteps.GET_BY_TITLE)

    dp.register_message_handler(v_clip_command, commands=['v_clip'], state=None)
    dp.register_message_handler(v_clip_get_link, state=VideoClipSteps.GET_LINK)
    dp.register_message_handler(v_clip_get_by_title, state=VideoClipSteps.GET_BY_TITLE)
    dp.register_message_handler(v_clip_get_time_from, state=VideoClipSteps.GET_TIME_FROM)
    dp.register_message_handler(v_clip_get_time_to, state=VideoClipSteps.GET_TIME_TO)

    dp.register_message_handler(audio_command, commands=['audio'], state=None)
    dp.register_message_handler(audio_get_link, state=AudioSteps.GET_LINK)
    dp.register_message_handler(audio_get_by_title, state=AudioSteps.GET_BY_TITLE)

    dp.register_message_handler(a_clip_command, commands=['a_clip'], state=None)
    dp.register_message_handler(a_clip_get_link, state=AudioClipSteps.GET_LINK)
    dp.register_message_handler(a_clip_get_by_title, state=AudioClipSteps.GET_BY_TITLE)
    dp.register_message_handler(a_clip_get_time_from, state=AudioClipSteps.GET_TIME_FROM)
    dp.register_message_handler(a_clip_get_time_to, state=AudioClipSteps.GET_TIME_TO)

    dp.register_message_handler(frame_command, commands=['frame'], state=None)
    dp.register_message_handler(frame_get_link, state=FrameSteps.GET_LINK)
    dp.register_message_handler(frame_get_by_title, state=FrameSteps.GET_BY_TITLE)
    dp.register_message_handler(frame_get_frame_time, state=FrameSteps.GET_FRAME_TIME)

    dp.register_message_handler(preview_command, commands=['preview'], state=None)
    dp.register_message_handler(preview_get_link, state=PreviewSteps.GET_LINK)
    dp.register_message_handler(preview_get_by_title, state=PreviewSteps.GET_BY_TITLE)

    dp.register_message_handler(info_command, commands=['info'], state=None)
    dp.register_message_handler(info_get_link, state=InfoSteps.GET_LINK)
    dp.register_message_handler(info_get_by_title, state=InfoSteps.GET_BY_TITLE)

    dp.register_message_handler(general_get_link, state=None)
    dp.register_message_handler(general_get_by_title, state=GeneralSteps.GET_BY_TITLE)
    dp.register_message_handler(general_message_choose, state=GeneralSteps.CHOOSE_OPTION)

    dp.register_callback_query_handler(general_button_choose, state=GeneralSteps.CHOOSE_OPTION)

    dp.register_callback_query_handler(choose_by_button, state='*')


async def start_bot() -> None:
    check_dirs()
    clear()
    register_all_handlers()
    try:
        await dp.start_polling()
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(start_bot())
