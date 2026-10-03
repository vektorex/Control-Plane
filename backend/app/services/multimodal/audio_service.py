"""
Audio Transcription and Metadata Service for Step 30: Multimodal AI.
Provides duration enforcement, audio metadata parsing, and pluggable transcription abstractions.
Does NOT fabricate speaker identities.
"""
import abc
import struct
from typing import Any, Dict, List, Optional

from backend.app.core.logging import logger
from backend.app.services.multimodal.errors import (
    CapabilityUnavailableError,
    FileLimitExceededError,
)
from backend.app.services.multimodal.limits import MULTIMODAL_MAX_AUDIO_DURATION
from backend.app.services.multimodal.sanitizer import sanitize_extracted_text
from backend.app.services.multimodal.schemas import AudioTranscriptSegment


class AudioTranscriptionProvider(abc.ABC):
    """
    Abstract provider contract for Audio Speech-to-Text transcription.
    Allows Whisper, Cloud Speech, or local offline transcription engines.
    """
    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @abc.abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
    ) -> List[AudioTranscriptSegment]:
        """Transcribes audio data into time-stamped segments."""
        pass


class MockAudioTranscriptionProvider(AudioTranscriptionProvider):
    """Deterministic mock provider for testing audio transcription."""
    def __init__(self, text: str = "Mock transcription of audio recording discussion."):
        self._text = text

    @property
    def provider_name(self) -> str:
        return "mock_transcriber"

    async def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
    ) -> List[AudioTranscriptSegment]:
        return [
            AudioTranscriptSegment(
                start_seconds=0.0,
                end_seconds=4.5,
                text=self._text,
                speaker="Speaker 1",
            )
        ]



class AudioService:
    """
    Extracts audio metadata, verifies duration limits, and orchestrates transcription.
    """

    def __init__(self, transcription_provider: Optional[AudioTranscriptionProvider] = None):
        self.transcription_provider = transcription_provider

    def extract_audio_metadata(self, data: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Probes audio duration and properties safely.
        """
        duration = 0.0
        sample_rate = 44100
        channels = 2

        if mime_type == "audio/wav" and len(data) >= 44:
            try:
                # Standard WAV header: channels at byte 22, sample rate at byte 24, byte rate at byte 28
                channels = struct.unpack("<H", data[22:24])[0]
                sample_rate = struct.unpack("<I", data[24:28])[0]
                byte_rate = struct.unpack("<I", data[28:32])[0]
                data_size = len(data) - 44
                if byte_rate > 0:
                    duration = round(data_size / float(byte_rate), 2)
            except Exception as e:
                logger.warning(f"[AudioService] WAV header parsing error: {e}")
                duration = round(len(data) / 176400.0, 2)
        else:
            # Fallback estimation based on ~128kbps = 16000 B/s
            duration = round(len(data) / 16000.0, 2)

        if duration > MULTIMODAL_MAX_AUDIO_DURATION:
            raise FileLimitExceededError(
                f"Audio duration of {duration:.1f}s exceeds limit of {MULTIMODAL_MAX_AUDIO_DURATION}s."
            )

        return {
            "duration_seconds": duration,
            "sample_rate": sample_rate,
            "channels": channels,
            "mime_type": mime_type,
        }

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        mime_type: str,
    ) -> List[AudioTranscriptSegment]:
        """
        Executes speech-to-text transcription via the configured provider.
        Raises CapabilityUnavailableError if no transcription engine is registered.
        """
        if not self.transcription_provider:
            raise CapabilityUnavailableError("No audio transcription provider configured on this instance.")

        segments = await self.transcription_provider.transcribe(audio_bytes, mime_type)
        # Sanitize text
        for seg in segments:
            seg.text = sanitize_extracted_text(seg.text)
        return segments

    @classmethod
    def format_transcript_context(cls, segments: List[AudioTranscriptSegment]) -> str:
        """
        Formats transcript segments into clean contextual representation with timestamps.
        Never fabricates speakers.
        """
        lines = []
        for seg in segments:
            m_start, s_start = divmod(int(seg.start_seconds), 60)
            h_start, m_start = divmod(m_start, 60)
            m_end, s_end = divmod(int(seg.end_seconds), 60)
            h_end, m_end = divmod(m_end, 60)

            ts = f"[{h_start:02d}:{m_start:02d}:{s_start:02d} - {h_end:02d}:{m_end:02d}:{s_end:02d}]"
            if seg.speaker:
                lines.append(f"{ts} {seg.speaker}: {seg.text}")
            else:
                lines.append(f"{ts} {seg.text}")

        return "\n".join(lines)
