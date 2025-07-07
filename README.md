# Video Chapter Splitter

動画ファイルをチャプター情報に基づいて自動分割するPythonツールです。

## 特徴

- 🎬 MP4動画をチャプターごとに分割
- 🎵 音声の無劣化コピー対応（デフォルト）
- 📊 進捗バー表示
- 🎯 柔軟な時間フォーマット対応
- ⚡ GPU エンコーディング対応（Apple VideoToolbox）
- 🔍 チャプターファイルの自動検出（動画名.txt）
- 📦 pip インストール対応（`video-chapter-splitter`コマンド）

## 必要要件

- Python 3.7+
- FFmpeg（システムにインストール済みであること）

## インストール

```bash
# PyPIからインストール（公開後）
pip install video-chapter-splitter

# GitHubから直接インストール
pip install git+https://github.com/yourusername/video-chapter-splitter.git

# 開発用（リポジトリをクローン後）
git clone https://github.com/yourusername/video-chapter-splitter.git
cd video-chapter-splitter
pip install -e .
```

## 使い方

### 基本的な使用方法

```bash
# pip インストール後
video-chapter-splitter input.mp4 chapters.txt

# チャプターファイルを省略（input.txt を自動的に使用）
video-chapter-splitter input.mp4

# 開発時（リポジトリから直接実行）
python src/video_chapter_splitter.py input.mp4
```

### チャプターファイルの形式

チャプターファイルは、動画と同じ名前で拡張子を`.txt`にしたファイルを自動的に検出します。
例: `video.mp4` → `video.txt`

ファイル内容の形式：
```
00:00:00 オープニング
00:03:45 第1章 - はじめに
00:15:30 第2章 - メインコンテンツ
00:45:00 第3章 - まとめ
01:00:00 エンディング
```

### コマンドラインオプション

```bash
# 基本使用（チャプターファイル自動検出）
video-chapter-splitter input.mp4

# チャプターファイルを明示的に指定
video-chapter-splitter input.mp4 chapters.txt

# ビデオコーデックを指定
video-chapter-splitter input.mp4 --video-codec libx264

# 音声を再エンコード（ビットレート指定）
video-chapter-splitter input.mp4 --audio-codec aac --audio-bitrate 256k

# 出力ディレクトリを指定
video-chapter-splitter input.mp4 --output-dir my_chapters
```

## 設定オプション

| オプション | 説明 | デフォルト |
|-----------|------|------------|
| `--video-codec` | ビデオコーデック | `hevc_videotoolbox` |
| `--video-bitrate` | ビデオビットレート(kbps) | 元のビットレート |
| `--audio-codec` | オーディオコーデック | `copy`（無劣化） |
| `--audio-bitrate` | オーディオビットレート(kbps) | 192k |
| `--output-dir` | 出力ディレクトリ | 入力ファイル名 |

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 貢献

プルリクエストを歓迎します！大きな変更を行う場合は、まずissueを開いて変更内容について議論してください。

## 作者

Your Name (@yourusername)
