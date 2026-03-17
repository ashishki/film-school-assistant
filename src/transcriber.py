import logging
from pathlib import Path

import whisper


LOGGER = logging.getLogger(__name__)


def transcribe(wav_path: str, model_name: str = "small") -> str:
    wav_name = Path(wav_path).name
    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(wav_path)
        transcript = result["text"].strip()
    except Exception:
        LOGGER.exception("Local Whisper transcription failed for file=%s", wav_name)
        raise

    LOGGER.info("Completed local Whisper transcription for file=%s using model=%s", wav_name, model_name)
    return transcript
