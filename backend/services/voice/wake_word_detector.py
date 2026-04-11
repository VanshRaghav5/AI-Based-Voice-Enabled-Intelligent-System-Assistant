"""
Wake Word Detection Module

Continuously listens for wake word (e.g., "Otto", "Hey Otto") 
to activate voice assistant without button press.
"""

import threading
import time
import re
from difflib import SequenceMatcher
import numpy as np
import scipy.io.wavfile as wavfile
from backend.services.voice.input.recorder import record_audio_fixed
from backend.utils.logger import logger
from backend.utils.assistant_config import assistant_config

try:
    from backend.services.voice.stt.faster_whisper_engine import transcribe_audio
    logger.info("[WakeWord] Using faster-whisper STT")
except ModuleNotFoundError:
    from backend.services.voice.stt.whisper_engine import transcribe_audio
    logger.warning("[WakeWord] faster-whisper unavailable; falling back to whisper_engine")


class WakeWordDetector:
    """
    Detects wake word in background to activate voice assistant.
    
    Uses short audio recordings (1-2 seconds) to minimize latency.
    Continuously monitors for configured wake words.
    """
    
    def __init__(self, callback=None, wake_words=None, on_state_change=None):
        """
        Initialize wake word detector.
        
        Args:
            callback: Function to call when wake word is detected
            wake_words: List of wake words to detect (default from config)
        """
        self.callback = callback
        self.on_state_change = on_state_change
        self.wake_words = wake_words or self._get_wake_words_from_config()
        self.is_active = False
        self.is_paused = False  # Pause during active conversation
        self._thread = None
        self._lock = threading.Lock()
        self._last_error = ""
        self._consecutive_errors = 0
        
        logger.info(f"[WakeWord] Initialized with wake words: {self.wake_words}")
    
    def _get_wake_words_from_config(self):
        """Load wake words from configuration."""
        wake_words = assistant_config.get('wake_word.words', ['otto', 'hey otto', 'ok otto'])
        # Normalize to lowercase for case-insensitive matching
        return [w.lower().strip() for w in wake_words]

    def _build_wake_prompt(self) -> str:
        """Build a wake-word-focused prompt to bias STT toward trigger phrases."""
        words = ", ".join(self.wake_words)
        return (
            "Wake words for this assistant are: "
            f"{words}. "
            "If heard, transcribe exactly as spoken."
        )

    def _audio_rms(self, audio_path: str) -> float:
        """Estimate RMS from WAV for fast silence rejection before STT."""
        try:
            _, audio_data = wavfile.read(audio_path)
            audio = audio_data.astype(np.float32)
            if audio.ndim == 2:
                audio = audio.mean(axis=1)
            return float(np.sqrt(np.mean(np.square(audio)))) if audio.size else 0.0
        except Exception:
            return 0.0

    def _normalize_text(self, text: str) -> str:
        """Normalize transcript text for more robust wake-word matching."""
        if not text:
            return ""
        normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _is_wake_word_match(self, transcript: str):
        """Return matched wake word if transcript appears to contain one."""
        normalized_text = self._normalize_text(transcript)
        if not normalized_text:
            return None

        # Aliases frequently produced by STT for "otto".
        alias_map = {
            "otto": ["otto", "auto", "ottoh", "ot to"],
            "hey otto": ["hey otto", "hi otto", "hey auto"],
            "ok otto": ["ok otto", "okay otto", "ok auto", "okay auto"],
        }

        for wake_word in self.wake_words:
            candidates = alias_map.get(wake_word, [wake_word])
            for candidate in candidates:
                normalized_candidate = self._normalize_text(candidate)

                # Direct containment check first.
                if normalized_candidate and normalized_candidate in normalized_text:
                    return wake_word

                # Fuzzy fallback for near-matches from noisy transcripts.
                ratio = SequenceMatcher(None, normalized_candidate, normalized_text).ratio()
                if ratio >= 0.82:
                    return wake_word

        return None
    
    def start(self):
        """Start wake word detection in background thread."""
        with self._lock:
            if self.is_active:
                logger.warning("[WakeWord] Already active")
                return True
            
            self.is_active = True
            self._thread = threading.Thread(target=self._detection_loop, daemon=True)
            self._thread.start()
            self._notify_state_change()
            logger.info("[WakeWord] Detection started")
            return True
    
    def stop(self):
        """Stop wake word detection."""
        with self._lock:
            if not self.is_active:
                return
            
            self.is_active = False
            logger.info("[WakeWord] Detection stopped")
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self._notify_state_change()
    
    def pause(self):
        """Pause wake word detection (e.g., during active conversation)."""
        self.is_paused = True
        self._notify_state_change()
        logger.debug("[WakeWord] Detection paused")
    
    def resume(self):
        """Resume wake word detection."""
        self.is_paused = False
        self._notify_state_change()
        logger.debug("[WakeWord] Detection resumed")

    def status_snapshot(self):
        """Return detector status for API and diagnostics."""
        thread_alive = bool(self._thread and self._thread.is_alive())
        return {
            "active": bool(self.is_active and thread_alive),
            "configured_active": bool(self.is_active),
            "thread_alive": thread_alive,
            "paused": bool(self.is_paused),
            "wake_words": list(self.wake_words),
            "consecutive_errors": int(self._consecutive_errors),
            "last_error": self._last_error,
        }

    def _notify_state_change(self):
        """Invoke optional lifecycle callback."""
        if not self.on_state_change:
            return
        try:
            self.on_state_change(self.status_snapshot())
        except Exception as e:
            logger.debug(f"[WakeWord] State callback failed: {e}")
    
    def _detection_loop(self):
        """
        Main detection loop - runs continuously in background.
        
        Records short audio chunks and checks for wake word.
        """
        logger.info("[WakeWord] Detection loop started")
        
        # Small delay on startup
        time.sleep(1.0)
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.is_active:
            try:
                poll_interval = float(assistant_config.get('wake_word.poll_interval_seconds', 0.8))

                # Skip if paused (during active conversation)
                if self.is_paused:
                    time.sleep(0.5)
                    continue
                
                # Record short audio chunk for low-latency wake detection.
                duration = float(assistant_config.get('wake_word.listen_duration', 1.8))
                audio_path = record_audio_fixed(duration=duration, warn_on_silence=False)
                
                if not audio_path:
                    logger.debug("[WakeWord] No audio captured")
                    time.sleep(poll_interval)
                    continue

                wake_rms_gate = float(assistant_config.get("wake_word.min_rms_int16", 250.0))
                rms = self._audio_rms(audio_path)
                if rms < wake_rms_gate:
                    logger.debug(
                        f"[WakeWord] Skipping STT for low RMS chunk ({rms:.1f} < {wake_rms_gate:.1f})"
                    )
                    time.sleep(poll_interval)
                    continue
                
                # Transcribe with wake-word-biased prompt.
                # Keep raw text (no corrections) to avoid replacing trigger words.
                text = transcribe_audio(
                    audio_path,
                    language_override="en",
                    initial_prompt_override=self._build_wake_prompt(),
                    apply_corrections=False,
                    min_audio_rms_override=float(assistant_config.get("wake_word.min_audio_rms", 0.0035)),
                    log_prob_threshold_override=float(assistant_config.get("wake_word.log_prob_threshold", -1.25)),
                    log_prefix="[WakeWord/STT]",
                )
                
                if not text:
                    time.sleep(poll_interval)
                    continue
                
                logger.debug(f"[WakeWord] Heard: '{text}'")

                detected_word = self._is_wake_word_match(text)

                if detected_word:
                    logger.info(f"[WakeWord] âœ“ DETECTED: '{detected_word}' in '{text}'")
                    consecutive_errors = 0  # Reset error counter
                    self._consecutive_errors = 0
                    self._last_error = ""
                    
                    # Pause detection to prevent re-triggering
                    self.pause()
                    
                    # Trigger callback
                    if self.callback:
                        try:
                            self.callback(detected_word)
                        except Exception as e:
                            logger.error(f"[WakeWord] Callback error: {e}")
                    
                    # Wait before resuming (allow time for voice command)
                    time.sleep(2.0)
                    self.resume()
                else:
                    # Configurable delay to avoid near-continuous polling
                    time.sleep(poll_interval)
                
            except KeyboardInterrupt:
                logger.info("[WakeWord] Detection interrupted")
                break
            
            except Exception as e:
                consecutive_errors += 1
                self._consecutive_errors = consecutive_errors
                self._last_error = str(e)
                logger.error(f"[WakeWord] Error in detection loop: {e}")
                
                # Stop if too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"[WakeWord] Too many errors ({consecutive_errors}), stopping detection")
                    self.is_active = False
                    self._notify_state_change()
                    break
                
                # Back off on errors
                time.sleep(1.0)
        
        logger.info("[WakeWord] Detection loop stopped")
        self._notify_state_change()


# Global instance
_wake_word_detector = None


def get_wake_word_detector():
    """Get or create global wake word detector instance."""
    global _wake_word_detector
    if _wake_word_detector is None:
        _wake_word_detector = WakeWordDetector()
    return _wake_word_detector
