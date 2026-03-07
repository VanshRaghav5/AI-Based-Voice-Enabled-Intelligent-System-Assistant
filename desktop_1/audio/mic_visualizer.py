import pyaudio
import numpy as np
import threading
import time


class MicVisualizer:
    """
    Captures microphone audio in a background thread and sends
    normalised amplitude values (0.0 – 1.0) to a UI callback.
    """

    def __init__(self, callback, chunk_size=1024, rate=44100):
        """
        Args:
            callback: Function called with a single float (0.0 – 1.0)
                      representing the current amplitude.
            chunk_size: Number of frames per audio read.
            rate: Sampling rate in Hz.
        """
        self.callback = callback
        self.chunk_size = chunk_size
        self.rate = rate

        self._pa = pyaudio.PyAudio()
        self._stream = None
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    # ── public API ──────────────────────────────────────────────

    def start(self):
        """Open the mic stream and begin capturing in a daemon thread."""
        with self._lock:
            if self._running:
                return

            try:
                self._stream = self._pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk_size,
                )
            except Exception as e:
                print(f"[MicVisualizer] Error opening mic: {e}")
                return

            self._running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Signal the capture thread to stop and close the stream."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        # Wait for thread to finish (outside lock to avoid deadlock)
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None

        self._close_stream()
        # Send a final zero-amplitude so the orb returns to idle
        try:
            self.callback(0.0)
        except Exception:
            pass

    # ── internals ───────────────────────────────────────────────

    def _capture_loop(self):
        """Background loop: read audio → compute RMS → invoke callback."""
        while self._running:
            try:
                data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float64)

                # RMS amplitude
                rms = np.sqrt(np.mean(samples ** 2))

                # Normalise: typical speech peaks ~3 000–5 000 out of 32 768
                normalised = min(1.0, rms / 4000.0)

                self.callback(normalised)

            except Exception as e:
                if self._running:          # only log if not intentionally stopped
                    print(f"[MicVisualizer] Capture error: {e}")
                break

    def _close_stream(self):
        """Safely close the PyAudio stream."""
        if self._stream is not None:
            try:
                if self._stream.is_active():
                    self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def __del__(self):
        self.stop()
        try:
            self._pa.terminate()
        except Exception:
            pass
