"""
ユーティリティ関数群
"""

import re
import subprocess
from typing import Optional, List


def time_to_seconds(time_str: str) -> float:
    """
    時間文字列を秒数に変換
    
    対応フォーマット:
    - HH:MM:SS
    - HH:MM:SS.sss
    - MM:SS
    - MM:SS.sss
    
    Args:
        time_str: 時間を表す文字列
        
    Returns:
        秒数（float）
        
    Raises:
        ValueError: 無効な時間フォーマットの場合
    """
    # 正規表現パターン: 時間は省略可能、分と秒は必須、ミリ秒は省略可能
    pattern = r'^(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)$'
    match = re.match(pattern, time_str.strip())
    
    if not match:
        # フォールバック: コロンで分割して処理
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            try:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            except ValueError:
                pass
        raise ValueError(f"無効な時間フォーマット: {time_str}")
    
    hours = float(match.group(1)) if match.group(1) else 0.0
    minutes = float(match.group(2))
    seconds = float(match.group(3))
    
    # 妥当性チェック
    if minutes >= 60:
        raise ValueError(f"分の値が無効です: {minutes}")
    if seconds >= 60:
        raise ValueError(f"秒の値が無効です: {seconds}")
    
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_time_str(seconds: float, include_ms: bool = False) -> str:
    """
    秒数を時間文字列に変換
    
    Args:
        seconds: 秒数
        include_ms: ミリ秒を含めるかどうか
        
    Returns:
        HH:MM:SS または HH:MM:SS.sss 形式の文字列
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if include_ms:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    else:
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d}"


def get_video_duration(video_file: str) -> float:
    """
    動画の長さを秒数で取得
    
    Args:
        video_file: 動画ファイルパス
        
    Returns:
        動画の長さ（秒）
        
    Raises:
        RuntimeError: FFprobeの実行に失敗した場合
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                video_file
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        duration_str = result.stdout.strip()
        if not duration_str:
            raise RuntimeError("動画の長さを取得できませんでした")
            
        return float(duration_str)
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFprobeの実行に失敗しました: {e.stderr}")
    except ValueError:
        raise RuntimeError(f"動画の長さの解析に失敗しました: {duration_str}")


def get_stream_bitrate(input_file: str, stream_type: str) -> Optional[int]:
    """
    ストリームのビットレートを取得
    
    Args:
        input_file: 入力ファイル
        stream_type: ストリームタイプ ("v" for video, "a" for audio)
        
    Returns:
        ビットレート（kbps）。取得できない場合はNone
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", f"{stream_type}:0",
                "-show_entries", "stream=bit_rate",
                "-of", "csv=p=0",
                input_file
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        bitrate_str = result.stdout.strip()
        if bitrate_str and bitrate_str.isdigit():
            return int(bitrate_str) // 1000  # bps to kbps
            
    except Exception:
        pass
    
    return None


def safe_filename(filename: str, max_length: int = 200) -> str:
    """
    ファイル名として安全な文字列に変換
    
    Args:
        filename: 元のファイル名
        max_length: 最大長
        
    Returns:
        安全なファイル名
    """
    # 使用できない文字を置換
    safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 連続するアンダースコアを1つに
    safe_chars = re.sub(r'_+', '_', safe_chars)
    
    # 前後の空白とピリオドを削除
    safe_chars = safe_chars.strip('. ')
    
    # 長さ制限
    if len(safe_chars) > max_length:
        safe_chars = safe_chars[:max_length].rstrip('. ')
    
    # 空の場合のフォールバック
    if not safe_chars:
        safe_chars = "untitled"
    
    return safe_chars


def run_ffmpeg_command(command: List[str]) -> bool:
    """
    FFmpegコマンドを実行
    
    Args:
        command: コマンドリスト
        
    Returns:
        成功した場合True
    """
    try:
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return process.returncode == 0
    except Exception:
        return False


def parse_progress_output(line: str) -> Optional[float]:
    """
    FFmpegのプログレス出力から現在時刻を取得
    
    Args:
        line: FFmpegの出力行
        
    Returns:
        現在の処理時刻（秒）。解析できない場合はNone
    """
    if "out_time_ms=" in line:
        try:
            time_value = line.split('=')[1].strip()
            if time_value.isdigit():
                return int(time_value) / 1_000_000  # マイクロ秒から秒へ
        except:
            pass
    
    return None


def check_ffmpeg_installed() -> bool:
    """FFmpegがインストールされているか確認"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except:
        return False


def check_ffprobe_installed() -> bool:
    """FFprobeがインストールされているか確認"""
    try:
        subprocess.run(
            ["ffprobe", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except:
        return False


def validate_environment() -> None:
    """実行環境を検証"""
    errors = []
    
    if not check_ffmpeg_installed():
        errors.append("FFmpegがインストールされていません")
    
    if not check_ffprobe_installed():
        errors.append("FFprobeがインストールされていません")
    
    if errors:
        raise RuntimeError("環境エラー:\n" + "\n".join(f"  - {e}" for e in errors))
