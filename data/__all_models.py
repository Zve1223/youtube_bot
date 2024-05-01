from __future__ import annotations
from sqlalchemy import Column, String, Integer
from .db_session import SqlAlchemyBase


class Video(SqlAlchemyBase):
    __tablename__ = 'videos'

    yt_id = Column(String, nullable=False, primary_key=True)
    tg_id = Column(String, nullable=False)
    res = Column(Integer, nullable=False)

    @staticmethod
    def create(yt_id: str, tg_id: str, res: int) -> Video:
        video = Video()
        video.yt_id = yt_id
        video.tg_id = tg_id
        video.res = res
        return video


class VideoClip(SqlAlchemyBase):
    __tablename__ = 'video_clips'

    yt_id = Column(String, nullable=False, primary_key=True)
    tg_id = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    res = Column(Integer, nullable=False)

    @staticmethod
    def create(yt_id: str, tg_id: str, start: int, end: int, res: int) -> VideoClip:
        video_clip = VideoClip()
        video_clip.yt_id = yt_id
        video_clip.tg_id = tg_id
        video_clip.start = start
        video_clip.end = end
        video_clip.res = res
        return video_clip


class Audio(SqlAlchemyBase):
    __tablename__ = 'audios'

    yt_id = Column(String, nullable=False, primary_key=True)
    tg_id = Column(String, nullable=False)

    @staticmethod
    def create(yt_id: str, tg_id: str) -> Audio:
        audio = Audio()
        audio.yt_id = yt_id
        audio.tg_id = tg_id
        return audio


class AudioClip(SqlAlchemyBase):
    __tablename__ = 'audio_clips'

    yt_id = Column(String, nullable=False, primary_key=True)
    tg_id = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)

    @staticmethod
    def create(yt_id: str, tg_id: str, start: int, end: int) -> AudioClip:
        audio_clip = AudioClip()
        audio_clip.yt_id = yt_id
        audio_clip.tg_id = tg_id
        audio_clip.start = start
        audio_clip.end = end
        return audio_clip


class Frame(SqlAlchemyBase):
    __tablename__ = 'frames'

    yt_id = Column(String, nullable=False, primary_key=True)
    tg_id = Column(String, nullable=False)
    time = Column(Integer, nullable=False)
    res = Column(Integer, nullable=False)

    @staticmethod
    def create(yt_id: str, tg_id: str, time: int, res: int) -> Frame:
        frame = Frame()
        frame.yt_id = yt_id
        frame.tg_id = tg_id
        frame.time = time
        frame.res = res
        return frame
