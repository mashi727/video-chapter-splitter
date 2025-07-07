# Video Chapter Splitter

動画ファイルをチャプター情報に基づいて自動分割するPythonツールです。

## 特徴

- 🎬 MP4動画をチャプターごとに分割
- 🎵 音声の無劣化コピー対応
- 📊 進捗バー表示
- 🎯 正確なカットモード（デフォルトで有効）
- ⚡ GPU エンコーディング対応（デフォルトで自動検出）
- 🔍 チャプターファイルの自動検出（動画名.txt）
- 📦 pip インストール対応（`video-chapter-splitter`コマンド）
- 🚫 "--"で始まるチャプターの自動除外機能

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
# pip インストール後（デフォルトで正確なカット + GPU自動検出）
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
00:15:30 --CM 
00:16:30 第2章 - メインコンテンツ
00:45:00 第3章 - まとめ
00:50:00 --エンドロール
01:00:00 エンディング
```

**注意**: `--`で始まるタイトルのチャプター（例: `--CM`、`--エンドロール`）は自動的に除外されます。

### コマンドラインオプション

```bash
# 基本使用（デフォルト: 正確なカット + GPU自動検出）
video-chapter-splitter input.mp4

# チャプターファイルを明示的に指定
video-chapter-splitter input.mp4 chapters.txt

# 高速モード（正確なカットを無効化）
video-chapter-splitter --no-accurate input.mp4

# GPUを使用しない（CPUのみ）
video-chapter-splitter --gpu none input.mp4

# 特定のGPUを指定
video-chapter-splitter --gpu videotoolbox input.mp4  # macOS
video-chapter-splitter --gpu nvenc input.mp4         # NVIDIA
video-chapter-splitter --gpu qsv input.mp4           # Intel
video-chapter-splitter --gpu amf input.mp4           # AMD

# ビデオコーデックを指定
video-chapter-splitter --video-codec libx264 input.mp4

# 音声を再エンコード（ビットレート指定）
video-chapter-splitter --audio-codec aac --audio-bitrate 256k input.mp4

# 出力ディレクトリを指定
video-chapter-splitter --output-dir my_chapters input.mp4

# 複数のオプションを組み合わせる
video-chapter-splitter --no-accurate --output-dir chapters input.mp4 chapters.txt
```

## 設定オプション

| オプション | 説明 | デフォルト |
|-----------|------|------------|
| `--video-codec` | ビデオコーデック | `copy`（無劣化） |
| `--video-bitrate` | ビデオビットレート(kbps) | 元のビットレート |
| `--audio-codec` | オーディオコーデック | `copy`（無劣化） |
| `--audio-bitrate` | オーディオビットレート(kbps) | 192k |
| `--output-dir` | 出力ディレクトリ | 入力ファイル名 |
| `--accurate` | 正確なカットモード | **有効** |
| `--no-accurate` | 高速カットモード（正確なカットを無効化） | - |
| `--gpu` | GPUアクセラレーション | **auto**（自動検出） |

### デフォルト動作

このツールは、デフォルトで以下の設定で動作します：

1. **正確なカットモード**: より正確な位置でチャプターを分割（`--accurate`）
2. **GPU自動検出**: 利用可能なGPUを自動的に検出して使用（`--gpu auto`）

高速処理を優先する場合は、`--no-accurate`オプションを使用してください。

### GPUアクセラレーション

`--gpu`オプションで高速なハードウェアエンコーディングが可能：

- **auto**（デフォルト）: 利用可能なGPUを自動検出
- **videotoolbox**: Apple Silicon Mac（M1/M2/M3）やIntel Mac
- **nvenc**: NVIDIA GPU（GeForce、Quadro）
- **qsv**: Intel Quick Sync Video
- **amf**: AMD GPU
- **none**: GPUを使用しない（CPUのみ）

### 処理モードの違い

1. **正確モード**（デフォルト）
   - より正確なカット位置
   - 指定時刻により近い位置でカット
   - GPUを使用する場合でも高品質を維持

2. **高速モード**（`--no-accurate`）
   - 最速処理、ストリームコピーを使用
   - キーフレームの位置により数フレームのずれが発生する可能性
   - 大量のファイルを処理する場合に有用

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 貢献

プルリクエストを歓迎します！大きな変更を行う場合は、まずissueを開いて変更内容について議論してください。

## 作者

MASAMI MASHINO (mashi.zzz@gmail.com)
