from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="video-chapter-splitter",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="動画ファイルをチャプター情報に基づいて分割するツール",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/video-chapter-splitter",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "tqdm>=4.65.0",
    ],
    entry_points={
        "console_scripts": [
            "video-chapter-splitter=src.video_chapter_splitter:main",
        ],
    },
)
