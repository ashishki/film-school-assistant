import logging
from pathlib import Path

import whisper


LOGGER = logging.getLogger(__name__)
_whisper_model = None


def transcribe(wav_path: str, model_name: str = "small") -> str:
    wav_name = Path(wav_path).name
    try:
        global _whisper_model
        if _whisper_model is None:
            _whisper_model = whisper.load_model(model_name)
        result = _whisper_model.transcribe(wav_path)
        transcript = result["text"].strip()
    except Exception:
        LOGGER.exception("Local Whisper transcription failed for file=%s", wav_name)
        raise

    LOGGER.info("Completed local Whisper transcription for file=%s using model=%s", wav_name, model_name)
    return transcript
