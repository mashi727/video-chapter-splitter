"""utils.pyのユニットテスト"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.utils import (
    time_to_seconds,
    seconds_to_time_str,
    safe_filename,
    check_ffmpeg_installed,
    check_ffprobe_installed
)


class TestTimeConversion(unittest.TestCase):
    """時間変換関数のテスト"""
    
    def test_time_to_seconds_basic(self):
        """基本的な時間フォーマットのテスト"""
        self.assertEqual(time_to_seconds("00:00:00"), 0.0)
        self.assertEqual(time_to_seconds("00:00:30"), 30.0)
        self.assertEqual(time_to_seconds("00:01:00"), 60.0)
        self.assertEqual(time_to_seconds("01:00:00"), 3600.0)
        self.assertEqual(time_to_seconds("01:23:45"), 5025.0)
    
    def test_time_to_seconds_without_hours(self):
        """時間を省略したフォーマットのテスト"""
        self.assertEqual(time_to_seconds("00:00"), 0.0)
        self.assertEqual(time_to_seconds("01:30"), 90.0)
        self.assertEqual(time_to_seconds("59:59"), 3599.0)
    
    def test_time_to_seconds_with_milliseconds(self):
        """ミリ秒を含むフォーマットのテスト"""
        self.assertAlmostEqual(time_to_seconds("00:00:00.500"), 0.5)
        self.assertAlmostEqual(time_to_seconds("00:00:01.234"), 1.234)
        self.assertAlmostEqual(time_to_seconds("01:23:45.678"), 5025.678)
    
    def test_time_to_seconds_invalid(self):
        """無効なフォーマットのテスト"""
        with self.assertRaises(ValueError):
            time_to_seconds("invalid")
        with self.assertRaises(ValueError):
            time_to_seconds("12:60:00")  # 無効な分
        with self.assertRaises(ValueError):
            time_to_seconds("12:00:60")  # 無効な秒
    
    def test_seconds_to_time_str(self):
        """秒数から時間文字列への変換テスト"""
        self.assertEqual(seconds_to_time_str(0), "00:00:00")
        self.assertEqual(seconds_to_time_str(30), "00:00:30")
        self.assertEqual(seconds_to_time_str(90), "00:01:30")
        self.assertEqual(seconds_to_time_str(3661), "01:01:01")
        self.assertEqual(seconds_to_time_str(5025.5), "01:23:45")
    
    def test_seconds_to_time_str_with_ms(self):
        """ミリ秒を含む変換テスト"""
        self.assertEqual(seconds_to_time_str(1.234, include_ms=True), "00:00:01.234")
        self.assertEqual(seconds_to_time_str(61.5, include_ms=True), "00:01:01.500")


class TestSafeFilename(unittest.TestCase):
    """ファイル名変換のテスト"""
    
    def test_safe_filename_basic(self):
        """基本的な変換テスト"""
        self.assertEqual(safe_filename("normal_filename"), "normal_filename")
        self.assertEqual(safe_filename("file with spaces"), "file with spaces")
    
    def test_safe_filename_invalid_chars(self):
        """無効な文字の置換テスト"""
        self.assertEqual(safe_filename("file<>name"), "file__name")
        self.assertEqual(safe_filename("path/to/file"), "path_to_file")
        self.assertEqual(safe_filename("file:name|test"), "file_name_test")
    
    def test_safe_filename_consecutive_underscores(self):
        """連続するアンダースコアの処理テスト"""
        self.assertEqual(safe_filename("file___name"), "file_name")
        self.assertEqual(safe_filename("test////file"), "test_file")
    
    def test_safe_filename_trim(self):
        """前後のトリミングテスト"""
        self.assertEqual(safe_filename("  filename  "), "filename")
        self.assertEqual(safe_filename("...filename..."), "filename")
        self.assertEqual(safe_filename(".  .filename.  ."), "filename")
    
    def test_safe_filename_length_limit(self):
        """長さ制限のテスト"""
        long_name = "a" * 300
        result = safe_filename(long_name, max_length=100)
        self.assertEqual(len(result), 100)
        self.assertEqual(result, "a" * 100)
    
    def test_safe_filename_empty(self):
        """空文字列の処理テスト"""
        self.assertEqual(safe_filename(""), "untitled")
        self.assertEqual(safe_filename("   "), "untitled")
        self.assertEqual(safe_filename("..."), "untitled")


class TestEnvironmentChecks(unittest.TestCase):
    """環境チェック関数のテスト"""
    
    @patch('subprocess.run')
    def test_check_ffmpeg_installed_success(self, mock_run):
        """FFmpegが正常にインストールされている場合"""
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(check_ffmpeg_installed())
    
    @patch('subprocess.run')
    def test_check_ffmpeg_installed_failure(self, mock_run):
        """FFmpegがインストールされていない場合"""
        mock_run.side_effect = Exception("Command not found")
        self.assertFalse(check_ffmpeg_installed())
    
    @patch('subprocess.run')
    def test_check_ffprobe_installed_success(self, mock_run):
        """FFprobeが正常にインストールされている場合"""
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(check_ffprobe_installed())


class TestCommandLineArgs(unittest.TestCase):
    """コマンドライン引数のテスト"""
    
    def test_auto_chapter_file_detection(self):
        """チャプターファイルの自動検出ロジックのテスト"""
        # このテストは実際のファイルシステムに依存しないように
        # モックを使用するか、一時ファイルを作成して行う
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_path = video_file.name
            expected_chapter_path = os.path.splitext(video_path)[0] + '.txt'
            
            # チャプターファイルのパスが正しく生成されることを確認
            self.assertTrue(expected_chapter_path.endswith('.txt'))
            self.assertEqual(
                os.path.splitext(os.path.basename(video_path))[0],
                os.path.splitext(os.path.basename(expected_chapter_path))[0]
            )
        
        # クリーンアップ
        os.unlink(video_path)


if __name__ == "__main__":
    unittest.main()
