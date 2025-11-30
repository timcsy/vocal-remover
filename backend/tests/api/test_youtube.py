"""
YouTube API Tests
Feature: 005-frontend-processing / User Story 4

測試 YouTube 代理 API 端點
"""
import pytest
from unittest.mock import patch, MagicMock


class TestYouTubeInfo:
    """測試 /api/v1/youtube/info 端點"""

    def test_get_info_valid_url(self, client):
        """應該成功取得影片資訊"""
        mock_info = {
            'title': '測試影片',
            'duration': 180,
            'thumbnail': 'https://example.com/thumb.jpg',
            'video_id': 'dQw4w9WgXcQ'
        }

        with patch('app.api.v1.youtube.get_youtube_downloader') as mock_get_dl:
            mock_dl = MagicMock()
            mock_dl.is_valid_url.return_value = True
            mock_dl.get_video_info.return_value = mock_info
            mock_get_dl.return_value = mock_dl

            response = client.get(
                '/api/v1/youtube/info',
                params={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}
            )

        assert response.status_code == 200
        data = response.json()
        assert data['title'] == '測試影片'
        assert data['duration'] == 180
        assert 'thumbnail' in data

    def test_get_info_invalid_url(self, client):
        """無效網址應該回傳 400"""
        with patch('app.api.v1.youtube.get_youtube_downloader') as mock_get_dl:
            mock_dl = MagicMock()
            mock_dl.is_valid_url.return_value = False
            mock_get_dl.return_value = mock_dl

            response = client.get(
                '/api/v1/youtube/info',
                params={'url': 'not-a-youtube-url'}
            )

        assert response.status_code == 400
        assert 'message' in response.json()

    def test_get_info_missing_url(self, client):
        """缺少網址參數應該回傳 422"""
        response = client.get('/api/v1/youtube/info')
        assert response.status_code == 422


class TestYouTubeDownload:
    """測試 /api/v1/youtube/download 端點"""

    def test_download_valid_url(self, client):
        """應該成功下載並回傳 WAV 音訊"""
        mock_wav_data = b'RIFF' + (b'\x00' * 40) + b'data' + (b'\x00' * 100)

        with patch('app.api.v1.youtube.get_youtube_downloader') as mock_get_dl, \
             patch('app.api.v1.youtube.extract_audio_from_video') as mock_extract:

            mock_dl = MagicMock()
            mock_dl.is_valid_url.return_value = True
            mock_dl.get_video_info.return_value = {
                'title': '測試影片',
                'duration': 180,
                'thumbnail': 'https://example.com/thumb.jpg',
            }
            mock_dl.download.return_value = '/tmp/test_video.mp4'
            mock_get_dl.return_value = mock_dl

            mock_extract.return_value = mock_wav_data

            response = client.post(
                '/api/v1/youtube/download',
                json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}
            )

        assert response.status_code == 200
        assert response.headers.get('content-type') == 'audio/wav'
        assert 'X-Video-Title' in response.headers
        assert 'X-Video-Duration' in response.headers

    def test_download_invalid_url(self, client):
        """無效網址應該回傳 400"""
        with patch('app.api.v1.youtube.get_youtube_downloader') as mock_get_dl:
            mock_dl = MagicMock()
            mock_dl.is_valid_url.return_value = False
            mock_get_dl.return_value = mock_dl

            response = client.post(
                '/api/v1/youtube/download',
                json={'url': 'not-a-youtube-url'}
            )

        assert response.status_code == 400

    def test_download_video_too_long(self, client):
        """超過時長限制應該回傳 400"""
        with patch('app.api.v1.youtube.get_youtube_downloader') as mock_get_dl:
            mock_dl = MagicMock()
            mock_dl.is_valid_url.return_value = True
            mock_dl.get_video_info.return_value = {
                'title': '超長影片',
                'duration': 9999,  # 超過限制
            }
            mock_dl.max_duration = 600
            mock_get_dl.return_value = mock_dl

            response = client.post(
                '/api/v1/youtube/download',
                json={'url': 'https://www.youtube.com/watch?v=test123'}
            )

        assert response.status_code == 400
        assert '超過' in response.json()['message'] or 'duration' in response.json()['message'].lower()
