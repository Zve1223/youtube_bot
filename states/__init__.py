from aiogram.dispatcher.filters.state import State, StatesGroup


class GeneralSteps(StatesGroup):
    GET_BY_TITLE = State()
    CHOOSE_OPTION = State()


class VideoSteps(StatesGroup):
    GET_LINK = State()
    GET_BY_TITLE = State()


class VideoClipSteps(StatesGroup):
    GET_LINK = State()
    GET_BY_TITLE = State()
    GET_TIME_FROM = State()
    GET_TIME_TO = State()


class AudioSteps(StatesGroup):
    GET_LINK = State()
    GET_BY_TITLE = State()


class AudioClipSteps(StatesGroup):
    GET_LINK = State()
    GET_BY_TITLE = State()
    GET_TIME_FROM = State()
    GET_TIME_TO = State()


class FrameSteps(StatesGroup):
    GET_LINK = State()
    GET_BY_TITLE = State()
    GET_FRAME_TIME = State()


class PreviewSteps(StatesGroup):
    GET_LINK = State()
    GET_BY_TITLE = State()


class InfoSteps(StatesGroup):
    GET_LINK = State()
    GET_BY_TITLE = State()
