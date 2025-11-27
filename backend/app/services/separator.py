import os
import tempfile
from pathlib import Path
from typing import Callable, Optional
import torch
import torchaudio

from app.core.config import get_settings


class VocalSeparator:
    """Demucs 人聲分離服務"""

    def __init__(self):
        settings = get_settings()
        self.device = settings.device
        self.model = None

    def _load_model(self):
        """延遲載入模型"""
        if self.model is None:
            from demucs.pretrained import get_model
            self.model = get_model("htdemucs")
            self.model.to(self.device)
            self.model.eval()

    def separate(
        self,
        input_path: str,
        output_dir: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> dict:
        """
        分離音頻中的人聲與伴奏

        Args:
            input_path: 輸入音頻檔案路徑
            output_dir: 輸出目錄
            progress_callback: 進度回調函數 (progress, stage)

        Returns:
            dict: 包含 vocals 和 background 檔案路徑
        """
        from demucs.apply import apply_model

        self._load_model()

        if progress_callback:
            progress_callback(0, "載入音頻中...")

        # Load audio
        wav, sr = torchaudio.load(input_path)

        # Resample if needed
        if sr != self.model.samplerate:
            if progress_callback:
                progress_callback(10, "重新取樣中...")
            resampler = torchaudio.transforms.Resample(sr, self.model.samplerate)
            wav = resampler(wav)

        # Move to device
        wav = wav.to(self.device)

        if progress_callback:
            progress_callback(20, "分離人聲中...")

        # Apply model
        with torch.no_grad():
            sources = apply_model(self.model, wav[None], progress=False)

        if progress_callback:
            progress_callback(80, "儲存結果中...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Demucs output order: drums, bass, other, vocals
        # We want vocals and background (drums + bass + other)
        vocals = sources[0, 3]  # vocals
        background = sources[0, 0] + sources[0, 1] + sources[0, 2]  # drums + bass + other

        # Resample back to original rate if needed
        if sr != self.model.samplerate:
            resampler = torchaudio.transforms.Resample(self.model.samplerate, sr)
            vocals = resampler(vocals.cpu())
            background = resampler(background.cpu())
        else:
            vocals = vocals.cpu()
            background = background.cpu()

        # Save files
        vocals_path = output_path / "vocals.wav"
        background_path = output_path / "background.wav"

        torchaudio.save(str(vocals_path), vocals, sr)
        torchaudio.save(str(background_path), background, sr)

        if progress_callback:
            progress_callback(100, "分離完成")

        return {
            "vocals": str(vocals_path),
            "background": str(background_path),
            "sample_rate": sr
        }


# Global instance
_separator: Optional[VocalSeparator] = None


def get_separator() -> VocalSeparator:
    """取得分離器實例"""
    global _separator
    if _separator is None:
        _separator = VocalSeparator()
    return _separator
