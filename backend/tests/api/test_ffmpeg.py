"""
FFmpeg API Tests
Feature: 005-frontend-processing / User Story 4

測試 FFmpeg 代理 API 端點
"""
import io
import pytest
from unittest.mock import patch, MagicMock


def create_mock_video_file():
    """建立模擬的影片檔案"""
    # 最小有效的 MP4 檔案結構（僅用於測試）
    return io.BytesIO(b'\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d' + b'\x00' * 100)


def create_mock_wav_file():
    """建立模擬的 WAV 檔案"""
    # RIFF + WAV header
    header = b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE'
    fmt = b'fmt ' + b'\x10\x00\x00\x00' + b'\x01\x00\x02\x00' + b'\x44\xac\x00\x00' + b'\x10\xb1\x02\x00' + b'\x04\x00\x10\x00'
    data = b'data' + b'\x00\x00\x00\x00' + b'\x00' * 100
    return io.BytesIO(header + fmt + data)


class TestExtractAudio:
    """測試 /api/v1/ffmpeg/extract-audio 端點"""

    def test_extract_audio_success(self, client):
        """應該成功提取音頻"""
        mock_wav_data = b'RIFF' + (b'\x00' * 40) + b'data' + (b'\x00' * 100)

        with patch('app.api.v1.ffmpeg.extract_audio_ffmpeg') as mock_extract:
            mock_extract.return_value = (mock_wav_data, 180.0)

            response = client.post(
                '/api/v1/ffmpeg/extract-audio',
                files={'video': ('test.mp4', create_mock_video_file(), 'video/mp4')}
            )

        assert response.status_code == 200
        assert response.headers.get('content-type') == 'audio/wav'
        assert 'X-Video-Duration' in response.headers
        assert float(response.headers['X-Video-Duration']) == 180.0

    def test_extract_audio_no_file(self, client):
        """缺少檔案應該回傳 422"""
        response = client.post('/api/v1/ffmpeg/extract-audio')
        assert response.status_code == 422

    def test_extract_audio_invalid_format(self, client):
        """非影片格式應該回傳 400"""
        with patch('app.api.v1.ffmpeg.extract_audio_ffmpeg') as mock_extract:
            mock_extract.side_effect = ValueError('不支援的檔案格式')

            response = client.post(
                '/api/v1/ffmpeg/extract-audio',
                files={'video': ('test.txt', io.BytesIO(b'not a video'), 'text/plain')}
            )

        assert response.status_code == 400


class TestMerge:
    """測試 /api/v1/ffmpeg/merge 端點"""

    def test_merge_mp4_success(self, client):
        """應該成功合併為 MP4"""
        mock_mp4_data = b'\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d' + b'\x00' * 100

        with patch('app.api.v1.ffmpeg.merge_video_audio_ffmpeg') as mock_merge:
            mock_merge.return_value = mock_mp4_data

            response = client.post(
                '/api/v1/ffmpeg/merge',
                files={
                    'video': ('test.mp4', create_mock_video_file(), 'video/mp4'),
                    'audio': ('mixed.wav', create_mock_wav_file(), 'audio/wav'),
                },
                data={'format': 'mp4'}
            )

        assert response.status_code == 200
        assert response.headers.get('content-type') == 'video/mp4'

    def test_merge_m4a_success(self, client):
        """應該成功合併為 M4A"""
        mock_m4a_data = b'\x00\x00\x00\x1c\x66\x74\x79\x70\x4d\x34\x41\x20' + b'\x00' * 100

        with patch('app.api.v1.ffmpeg.merge_video_audio_ffmpeg') as mock_merge:
            mock_merge.return_value = mock_m4a_data

            response = client.post(
                '/api/v1/ffmpeg/merge',
                files={
                    'video': ('test.mp4', create_mock_video_file(), 'video/mp4'),
                    'audio': ('mixed.wav', create_mock_wav_file(), 'audio/wav'),
                },
                data={'format': 'm4a'}
            )

        assert response.status_code == 200
        assert response.headers.get('content-type') == 'audio/mp4'

    def test_merge_invalid_format(self, client):
        """不支援的格式應該回傳 400"""
        response = client.post(
            '/api/v1/ffmpeg/merge',
            files={
                'video': ('test.mp4', create_mock_video_file(), 'video/mp4'),
                'audio': ('mixed.wav', create_mock_wav_file(), 'audio/wav'),
            },
            data={'format': 'flv'}
        )

        assert response.status_code == 400

    def test_merge_missing_video(self, client):
        """缺少影片應該回傳 422"""
        response = client.post(
            '/api/v1/ffmpeg/merge',
            files={
                'audio': ('mixed.wav', create_mock_wav_file(), 'audio/wav'),
            },
            data={'format': 'mp4'}
        )

        assert response.status_code == 422

    def test_merge_missing_audio(self, client):
        """缺少音訊應該回傳 422"""
        response = client.post(
            '/api/v1/ffmpeg/merge',
            files={
                'video': ('test.mp4', create_mock_video_file(), 'video/mp4'),
            },
            data={'format': 'mp4'}
        )

        assert response.status_code == 422
