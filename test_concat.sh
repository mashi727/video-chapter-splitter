#!/bin/bash

# テスト用チャプターファイルの作成
cat > test_chapters.txt << 'CHAPTERS'
0:00:00 オープニング
0:01:00 --CM
0:01:30 第1章
0:03:00 --MC
0:03:30 第2章
0:05:00 エンディング
0:05:30 --その他
CHAPTERS

echo "テスト用チャプターファイル (test_chapters.txt) を作成しました"
echo "内容:"
cat test_chapters.txt
echo ""
echo "使用例:"
echo "  python src/video_chapter_splitter.py --concat your_video.mp4 test_chapters.txt"
echo ""
echo "期待される結果:"
echo "  - your_video_concat.mp4 (結合された動画)"
echo "  - test_chapters_concat.txt (調整されたチャプターファイル)"
