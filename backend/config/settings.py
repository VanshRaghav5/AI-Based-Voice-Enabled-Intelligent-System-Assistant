from backend.config.assistant_config import assistant_config


# ==============================
# Voice Recording Settings
# ==============================

RECORD_DURATION = int(assistant_config.get("recording.record_duration", 4))
SAMPLE_RATE = int(assistant_config.get("recording.sample_rate", 16000))
RECORDING_INPUT_DEVICE = assistant_config.get("recording.input_device", None)
RECORDING_MIN_AUDIO_LEVEL = int(assistant_config.get("recording.min_audio_level_int16", 80))
RECORDING_NOISE_CALIBRATION_SECONDS = float(
	assistant_config.get("recording.noise_calibration_seconds", 0.35)
)
RECORDING_DYNAMIC_SILENCE_MULTIPLIER = float(
	assistant_config.get("recording.dynamic_silence_multiplier", 2.6)
)
RECORDING_DYNAMIC_SILENCE_MIN = int(
	assistant_config.get("recording.dynamic_silence_min_int16", 140)
)
RECORDING_DYNAMIC_SILENCE_MAX = int(
	assistant_config.get("recording.dynamic_silence_max_int16", 2200)
)


# ==============================
# Whisper Settings
# ==============================

WHISPER_MODEL = assistant_config.get("stt.model", "base.en")
WHISPER_LANGUAGE = assistant_config.get("stt.language", "en")
WHISPER_BEAM_SIZE = int(assistant_config.get("stt.beam_size", 1))
WHISPER_BEST_OF = int(assistant_config.get("stt.best_of", 3))
WHISPER_NO_SPEECH_THRESHOLD = float(assistant_config.get("stt.no_speech_threshold", 0.45))
WHISPER_LOG_PROB_THRESHOLD = float(assistant_config.get("stt.log_prob_threshold", -1.1))
WHISPER_COMPRESSION_RATIO_THRESHOLD = float(assistant_config.get("stt.compression_ratio_threshold", 2.0))
WHISPER_MIN_AUDIO_RMS = float(assistant_config.get("stt.min_audio_rms", 0.01))
WHISPER_VAD_MIN_SILENCE_MS = int(assistant_config.get("stt.vad_min_silence_ms", 500))
WHISPER_MAX_AUDIO_SECONDS = float(assistant_config.get("stt.max_audio_seconds", 8.0))
FASTER_WHISPER_COMPUTE_TYPE = assistant_config.get("stt.compute_type", "int8")
WHISPER_INITIAL_PROMPT = assistant_config.get("stt.initial_prompt", "")
WHISPER_TEXT_CORRECTIONS = dict(assistant_config.get("stt.text_corrections", {}))
WHISPER_ENABLE_DENOISE = bool(assistant_config.get("stt.enable_denoise", True))
WHISPER_DENOISE_NOISE_PERCENTILE = float(
	assistant_config.get("stt.denoise_noise_percentile", 20.0)
)
WHISPER_DENOISE_GATE_MULTIPLIER = float(
	assistant_config.get("stt.denoise_gate_multiplier", 1.5)
)
WHISPER_PREEMPHASIS_ALPHA = float(assistant_config.get("stt.preemphasis_alpha", 0.97))
WHISPER_NORMALIZE_TARGET_PEAK = float(assistant_config.get("stt.normalize_target_peak", 0.92))


# ==============================
# Assistant Settings
# ==============================

EXIT_COMMANDS = list(assistant_config.get("assistant.exit_commands", ["exit", "quit", "shutdown", "stop assistant"]))


# ==============================
# TTS Settings
# ==============================

TTS_LENGTH_SCALE = str(assistant_config.get("tts.length_scale", 0.9))
TTS_NOISE_SCALE = str(assistant_config.get("tts.noise_scale", 0.667))
TTS_NOISE_W = str(assistant_config.get("tts.noise_w", 0.8))
TTS_TIMEOUT_SECONDS = int(assistant_config.get("tts.timeout_seconds", 10))
TTS_ACTIVE_VOICE = str(assistant_config.get("tts.active_voice", "danny"))
TTS_ACTIVE_ACCENT = str(assistant_config.get("tts.active_accent", "en_US"))
TTS_ALLOW_ACCENT_FALLBACK = bool(assistant_config.get("tts.allow_accent_fallback", True))
TTS_VOICE_CATALOG = dict(assistant_config.get("tts.voice_catalog", {}))


# ==============================
# LLM Settings
# ==============================

LLM_MODEL = assistant_config.get("llm.model", "qwen2.5:7b-instruct-q4_0")
LLM_TIMEOUT_SECONDS = int(assistant_config.get("llm.timeout_seconds", 15))
LLM_FAST_ROUTER_ENABLED = bool(assistant_config.get("llm.fast_router_enabled", True))
LLM_MAX_AGENT_ITERATIONS = int(assistant_config.get("llm.max_agent_iterations", 3))


# ==============================
# Assistant Persona Settings
# ==============================

ASSISTANT_PERSONA_MODE = assistant_config.get("assistant.active_persona", "butler")
ASSISTANT_USER_TITLE = assistant_config.get("assistant.user_title", "sir")
ASSISTANT_PERSONAS = dict(assistant_config.get("personas", {}))

