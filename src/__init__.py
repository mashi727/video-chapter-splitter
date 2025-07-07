"""Video Chapter Splitter - 動画をチャプターごとに分割するツール"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .video_chapter_splitter import VideoChapterSplitter
from .utils import time_to_seconds, seconds_to_time_str

__all__ = ["VideoChapterSplitter", "time_to_seconds", "seconds_to_time_str"]
