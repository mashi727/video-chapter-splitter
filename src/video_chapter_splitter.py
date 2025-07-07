#!/usr/bin/env python3
"""
Video Chapter Splitter

動画ファイルをチャプター情報に基づいて分割するツール
"""

import argparse
import os
import sys
import platform
import subprocess
from typing import List, Tuple, Optional, Dict, Any

from tqdm import tqdm

from .utils import (
    time_to_seconds,
    seconds_to_time_str,
    get_video_duration,
    get_stream_bitrate,
    safe_filename,
    run_ffmpeg_command,
    parse_progress_output
)


class VideoChapterSplitter:
    """動画をチャプターごとに分割するクラス"""
    
    def __init__(self, 
                 video_codec: str = "hevc_videotoolbox",
                 video_bitrate: Optional[int] = None,
                 audio_codec: str = "copy",
                 audio_bitrate: int = 192,
                 accurate: bool = True,
                 gpu: Optional[str] = "auto"):
        """
        Args:
            video_codec: 使用するビデオコーデック
            video_bitrate: ビデオビットレート (kbps)。Noneの場合は元のビットレートを使用
            audio_codec: 使用するオーディオコーデック。"copy"で無劣化コピー
            audio_bitrate: オーディオビットレート (kbps)。audio_codecが"copy"以外の場合に使用
            accurate: 正確なカットを行うかどうか
            gpu: GPU アクセラレーションタイプ ('auto', 'videotoolbox', 'nvenc', 'qsv', 'amf')
        """
        self.video_codec = video_codec
        self.video_bitrate = video_bitrate
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.accurate = accurate
        self.gpu = gpu
        self.gpu_encoder = None
        
        # GPUエンコーダーの設定
        if gpu:
            self._configure_gpu_encoder()
    
    def _configure_gpu_encoder(self):
        """GPUエンコーダーを設定"""
        if self.gpu == 'none':
            # GPU使用を明示的に無効化
            self.gpu_encoder = None
            print("GPU使用を無効化しました。CPUエンコーディングを使用します。")
            return
        
        if self.gpu == 'auto':
            # 自動検出
            self.gpu_encoder = self._detect_gpu_encoder()
            if self.gpu_encoder:
                print(f"GPU エンコーダーを自動検出: {self.gpu_encoder['name']}")
            else:
                print("GPUエンコーダーが検出されませんでした。CPUエンコーディングを使用します。")
        else:
            # 指定されたGPUエンコーダー
            encoder_configs = {
                'videotoolbox': {
                    'name': 'VideoToolbox (macOS)',
                    'encoder': 'hevc_videotoolbox',
                    'params': ['-profile:v', 'main']
                },
                'nvenc': {
                    'name': 'NVIDIA NVENC',
                    'encoder': 'hevc_nvenc',
                    'params': ['-preset', 'p4', '-tune', 'hq']
                },
                'qsv': {
                    'name': 'Intel Quick Sync',
                    'encoder': 'hevc_qsv',
                    'params': ['-preset', 'medium']
                },
                'amf': {
                    'name': 'AMD AMF',
                    'encoder': 'hevc_amf',
                    'params': ['-quality', 'balanced']
                }
            }
            
            if self.gpu in encoder_configs:
                encoder_config = encoder_configs[self.gpu]
                if self._test_encoder(encoder_config['encoder']):
                    self.gpu_encoder = encoder_config
                    print(f"GPU エンコーダーを使用: {encoder_config['name']}")
                else:
                    print(f"{encoder_config['name']} は利用できません。CPUエンコーディングを使用します。")
    
    def _detect_gpu_encoder(self) -> Optional[Dict[str, Any]]:
        """利用可能なGPUエンコーダーを自動検出"""
        # プラットフォーム別の検出順序
        if platform.system() == 'Darwin':  # macOS
            encoders = [
                {
                    'name': 'VideoToolbox (macOS)',
                    'encoder': 'hevc_videotoolbox',
                    'params': ['-profile:v', 'main']
                }
            ]
        elif platform.system() == 'Windows':
            encoders = [
                {
                    'name': 'NVIDIA NVENC',
                    'encoder': 'hevc_nvenc',
                    'params': ['-preset', 'p4', '-tune', 'hq']
                },
                {
                    'name': 'AMD AMF',
                    'encoder': 'hevc_amf',
                    'params': ['-quality', 'balanced']
                },
                {
                    'name': 'Intel Quick Sync',
                    'encoder': 'hevc_qsv',
                    'params': ['-preset', 'medium']
                }
            ]
        else:  # Linux
            encoders = [
                {
                    'name': 'NVIDIA NVENC',
                    'encoder': 'hevc_nvenc',
                    'params': ['-preset', 'p4', '-tune', 'hq']
                },
                {
                    'name': 'Intel Quick Sync',
                    'encoder': 'hevc_qsv',
                    'params': ['-preset', 'medium']
                }
            ]
        
        # 各エンコーダーをテスト
        for encoder in encoders:
            if self._test_encoder(encoder['encoder']):
                return encoder
        
        return None
    
    def _test_encoder(self, encoder: str) -> bool:
        """特定のエンコーダーが利用可能かテスト"""
        try:
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', 'color=c=black:s=320x240:d=1',
                '-c:v', encoder,
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            return result.returncode == 0
        except:
            return False
    
    def parse_chapter_file(self, chapter_file: str, video_file: str) -> List[Tuple[str, str, str]]:
        """
        チャプターファイルをパースして、チャプター情報のリストを返す
        "--" で始まる行（例: "--MC"）は無視される
        
        Args:
            chapter_file: チャプター情報が記載されたファイルパス
            video_file: 動画ファイルパス
            
        Returns:
            [(開始時刻, 終了時刻, タイトル), ...] のリスト
        """
        video_duration = get_video_duration(video_file)
        full_duration_str = seconds_to_time_str(video_duration)
        
        with open(chapter_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        chapters = []
        valid_lines = []
        
        # まず有効な行だけを抽出（"--"で始まる行はスキップ）
        for line in lines:
            try:
                parts = line.split(maxsplit=1)
                if len(parts) >= 2:
                    time_str, title = parts[0], parts[1]
                    # タイトルが "--" で始まる行は無視（例: "0:15:58.744 --MC"）
                    if title.startswith("--"):
                        continue
                    valid_lines.append((time_str, title))
            except:
                continue
        
        # チャプター情報を構築
        for i, (time_str, title) in enumerate(valid_lines):
            start_time = time_str
            
            # 次のチャプターの開始時刻を終了時刻とする
            if i + 1 < len(valid_lines):
                end_time = valid_lines[i + 1][0]
            else:
                end_time = full_duration_str
            
            chapters.append((start_time, end_time, title))
        
        return chapters
    
    def display_chapters(self, chapters: List[Tuple[str, str, str]]) -> None:
        """チャプター情報を表示"""
        print("\n=== チャプター情報 ===")
        print(f"{'No.':<5} {'開始時間':<12} {'終了時間':<12} {'タイトル'}")
        print("-" * 80)
        for i, (start_time, end_time, title) in enumerate(chapters, start=1):
            print(f"{i:<5} {start_time:<12} {end_time:<12} {title}")
    
    def split_chapter(self, 
                     input_file: str,
                     output_file: str,
                     start_seconds: float,
                     duration: float,
                     video_bitrate: int) -> bool:
        """
        単一のチャプターを分割
        
        Returns:
            成功した場合True
        """
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-progress", "pipe:1"
        ]
        
        if self.accurate:
            # 正確なモード: 入力後にシーク
            ffmpeg_command.extend([
                "-i", input_file,
                "-ss", str(start_seconds)
            ])
        else:
            # 通常モード: 高速シーク
            ffmpeg_command.extend([
                "-ss", str(start_seconds),
                "-i", input_file
            ])
        
        # ビデオコーデックの設定
        if self.gpu_encoder and (self.accurate or self.video_codec != "copy"):
            # GPUエンコーダーを使用
            ffmpeg_command.extend(["-c:v", self.gpu_encoder['encoder']])
            ffmpeg_command.extend(self.gpu_encoder['params'])
            ffmpeg_command.extend(["-b:v", f"{video_bitrate}k"])
        elif self.accurate and self.video_codec == "copy":
            # accurateモードでコピーは使用できないため、デフォルトコーデックを使用
            ffmpeg_command.extend([
                "-c:v", "libx265",
                "-crf", "23",
                "-preset", "medium"
            ])
        elif self.video_codec == "copy":
            ffmpeg_command.extend(["-c:v", "copy"])
        else:
            ffmpeg_command.extend([
                "-c:v", self.video_codec,
                "-b:v", f"{video_bitrate}k"
            ])
        
        # オーディオコーデックの設定
        if self.audio_codec == "copy":
            ffmpeg_command.extend(["-c:a", "copy"])
        else:
            ffmpeg_command.extend([
                "-c:a", self.audio_codec,
                "-b:a", f"{self.audio_bitrate}k"
            ])
        
        # その他のオプション
        ffmpeg_command.extend(["-movflags", "+faststart"])
        
        # 継続時間の設定
        if duration > 0:
            ffmpeg_command.extend(["-t", str(duration)])
        
        ffmpeg_command.append(output_file)
        
        return run_ffmpeg_command(ffmpeg_command)
    
    def split_video(self, input_file: str, chapter_file: str, output_dir: Optional[str] = None) -> List[str]:
        """
        動画をチャプターごとに分割
        
        Args:
            input_file: 入力動画ファイル
            chapter_file: チャプター情報ファイル
            output_dir: 出力ディレクトリ（Noneの場合は入力ファイル名から生成）
            
        Returns:
            生成されたファイルのリスト
        """
        # 出力ディレクトリの設定
        if output_dir is None:
            base_filename = os.path.splitext(os.path.basename(input_file))[0]
            output_dir = base_filename
        os.makedirs(output_dir, exist_ok=True)
        
        # チャプター情報の取得
        chapters = self.parse_chapter_file(chapter_file, input_file)
        if not chapters:
            raise ValueError("有効なチャプター情報が見つかりませんでした")
        
        self.display_chapters(chapters)
        
        # ビットレートの取得
        if self.video_bitrate is None:
            detected_bitrate = get_stream_bitrate(input_file, "v")
            video_bitrate = detected_bitrate if detected_bitrate else 5000
            print(f"\nビデオビットレート: {video_bitrate}k (自動検出)")
        else:
            video_bitrate = self.video_bitrate
            print(f"\nビデオビットレート: {video_bitrate}k (指定)")
        
        # 処理モードの表示
        if self.accurate:
            print("処理モード: 正確なカット")
        else:
            print("処理モード: 高速カット (--no-accurate)")
        
        if self.gpu_encoder:
            print(f"エンコーダー: {self.gpu_encoder['name']}")
        
        # 全体の進捗計算
        total_duration = sum(
            time_to_seconds(end) - time_to_seconds(start)
            for start, end, _ in chapters
        )
        
        output_files = []
        
        # 分割処理
        print(f"\n処理開始: {len(chapters)} チャプター")
        with tqdm(total=total_duration, desc="全体進捗", unit="秒") as pbar:
            elapsed_total = 0.0
            
            for i, (start_time, end_time, track_name) in enumerate(chapters):
                start_seconds = time_to_seconds(start_time)
                end_seconds = time_to_seconds(end_time)
                duration = end_seconds - start_seconds
                
                # 出力ファイル名
                safe_name = safe_filename(track_name)
                output_file = os.path.join(output_dir, f"{i + 1:03d}_{safe_name}.mp4")
                output_files.append(output_file)
                
                # チャプター名を表示
                tqdm.write(f"処理中: [{i+1}/{len(chapters)}] {track_name}")
                
                # FFmpegコマンドの実行（プログレス付き）
                success = self.split_chapter_with_progress(
                    input_file, output_file, start_seconds, duration,
                    video_bitrate, pbar, elapsed_total
                )
                
                if not success:
                    tqdm.write(f"エラー: チャプター {i + 1} の分割に失敗しました: {track_name}")
                
                elapsed_total += duration
                pbar.n = elapsed_total
                pbar.refresh()
        
        return output_files
    
    def split_chapter_with_progress(self,
                                  input_file: str,
                                  output_file: str,
                                  start_seconds: float,
                                  duration: float,
                                  video_bitrate: int,
                                  pbar: tqdm,
                                  elapsed_total: float) -> bool:
        """プログレス表示付きでチャプターを分割"""
        import subprocess
        
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-progress", "pipe:1"
        ]
        
        if self.accurate:
            # 正確なモード
            ffmpeg_command.extend([
                "-i", input_file,
                "-ss", str(start_seconds)
            ])
        else:
            # 高速モード
            ffmpeg_command.extend([
                "-ss", str(start_seconds),
                "-i", input_file
            ])
        
        # ビデオコーデックの設定
        if self.gpu_encoder and (self.accurate or self.video_codec != "copy"):
            ffmpeg_command.extend(["-c:v", self.gpu_encoder['encoder']])
            ffmpeg_command.extend(self.gpu_encoder['params'])
            ffmpeg_command.extend(["-b:v", f"{video_bitrate}k"])
        elif self.accurate and self.video_codec == "copy":
            ffmpeg_command.extend([
                "-c:v", "libx265",
                "-crf", "23",
                "-preset", "medium"
            ])
        elif self.video_codec == "copy":
            ffmpeg_command.extend(["-c:v", "copy"])
        else:
            ffmpeg_command.extend([
                "-c:v", self.video_codec,
                "-b:v", f"{video_bitrate}k"
            ])
        
        if self.audio_codec == "copy":
            ffmpeg_command.extend(["-c:a", "copy"])
        else:
            ffmpeg_command.extend([
                "-c:a", self.audio_codec,
                "-b:a", f"{self.audio_bitrate}k"
            ])
        
        ffmpeg_command.extend(["-movflags", "+faststart"])
        
        if duration > 0:
            ffmpeg_command.extend(["-t", str(duration)])
        
        ffmpeg_command.append(output_file)
        
        process = subprocess.Popen(
            ffmpeg_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            current_time = parse_progress_output(line)
            if current_time is not None:
                pbar.n = elapsed_total + min(current_time, duration)
                pbar.refresh()
        
        process.wait()
        return process.returncode == 0


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="動画をチャプター情報に基づいて分割します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
チャプターファイルの形式:
  00:00:00 オープニング
  00:03:45 第1章
  00:15:30 --CM (この行は無視されます)
  00:16:30 第2章
  ...

"--" で始まるタイトルのチャプターは除外されます。

チャプターファイルを省略した場合:
  動画ファイルと同じ名前の.txtファイルを自動的に使用します
  例: video.mp4 → video.txt
        """
    )
    
    parser.add_argument("input_file", help="分割する動画ファイル")
    parser.add_argument("chapter_file", nargs="?", help="チャプター情報ファイル（省略可）")
    parser.add_argument("--output-dir", "-o", help="出力ディレクトリ")
    
    # ビデオオプション
    video_group = parser.add_argument_group("ビデオオプション")
    video_group.add_argument("--video-codec", "-vc", 
                           default="copy",
                           help="ビデオコーデック (デフォルト: copy で無劣化コピー)")
    video_group.add_argument("--video-bitrate", "-vb",
                           type=int,
                           help="ビデオビットレート (kbps)。未指定の場合は元のビットレートを使用")
    
    # オーディオオプション
    audio_group = parser.add_argument_group("オーディオオプション")
    audio_group.add_argument("--audio-codec", "-ac",
                           default="copy",
                           help="オーディオコーデック (デフォルト: copy で無劣化コピー)")
    audio_group.add_argument("--audio-bitrate", "-ab",
                           type=int,
                           default=192,
                           help="オーディオビットレート (kbps) (デフォルト: 192)")
    
    # 処理オプション
    process_group = parser.add_argument_group("処理オプション")
    process_group.add_argument("--accurate",
                             action="store_true",
                             default=True,  # デフォルトをTrueに
                             help="より正確なカット（デフォルト: 有効）。--no-accurateで無効化")
    process_group.add_argument("--gpu",
                             choices=['auto', 'none', 'videotoolbox', 'nvenc', 'qsv', 'amf'],
                             default="auto",
                             help="GPU アクセラレーションを使用（デフォルト: auto で自動検出）")
    
    args = parser.parse_args()
    
    # ファイルの存在確認
    if not os.path.exists(args.input_file):
        print(f"エラー: 入力ファイルが見つかりません: {args.input_file}")
        sys.exit(1)
    
    # チャプターファイルの決定
    if args.chapter_file is None:
        # チャプターファイルが省略された場合、動画ファイル名.txtを使用
        base_name = os.path.splitext(args.input_file)[0]
        chapter_file = base_name + ".txt"
        print(f"チャプターファイルが指定されていないため、{chapter_file} を使用します")
    else:
        chapter_file = args.chapter_file
    
    if not os.path.exists(chapter_file):
        print(f"エラー: チャプターファイルが見つかりません: {chapter_file}")
        sys.exit(1)
    
    # 分割実行
    splitter = VideoChapterSplitter(
        video_codec=args.video_codec,
        video_bitrate=args.video_bitrate,
        audio_codec=args.audio_codec,
        audio_bitrate=args.audio_bitrate,
        accurate=args.accurate,
        gpu=args.gpu
    )
    
    try:
        output_files = splitter.split_video(
            args.input_file,
            chapter_file,
            args.output_dir
        )
        
        print("\n=== 完了 ===")
        print(f"生成されたファイル数: {len(output_files)}")
        for f in output_files:
            print(f"  {f}")
            
    except Exception as e:
        print(f"\nエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
