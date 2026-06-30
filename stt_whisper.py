import collections
import logging
import queue
import threading
import numpy as np
import pyaudio
import time
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
MODEL_SIZE = "tiny"         # Tiny is fastest for Pi 5
DEVICE = "cpu"              # Pi 5 uses CPU
COMPUTE_TYPE = "int8"       # Optimized for ARM CPUs
CHUNK_SIZE = 1024           # Frames per buffer
FORMAT = pyaudio.paInt16    # 16-bit PCM
CHANNELS = 1                # Mono
RATE = 16000                # Whisper expects 16kHz
SILENCE_THRESHOLD = 500     # Adjust based on your mic sensitivity
# ---------------------

class STTEngine:
    def __init__(self):
        self.model = None
        self.listening = False
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue() # For passing text back to main thread
        self.thread = None
        self.stream = None
        self.p = pyaudio.PyAudio()
        self.live_thread = None
        self.audio_frames = []
        self.audio_buffer = []
        self.current_rate = RATE
        self.current_channels = CHANNELS

    def load_model(self):
        if self.model is None:
            logger.info("Loading Whisper model '%s'...", MODEL_SIZE)
            self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE, cpu_threads=4)
            logger.info("Whisper model loaded.")

    def _mic_callback(self, in_data, frame_count, time_info, status):
        if self.listening:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start_listening(self):
        if self.listening:
            return
        
        # Ensure model is loaded (this might block if not preloaded, so best to preload)
        if not self.model:
            self.load_model()
            
        self.listening = True
        self.audio_queue = queue.Queue() # Clear queue
        
        device_index = self._get_input_device_index() or 0
        self.stream = self.p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=CHUNK_SIZE,
                        stream_callback=self._mic_callback)
        
        self.thread = threading.Thread(target=self._process_audio, daemon=True)
        self.thread.start()
        logger.info("STT Started Listening")

    def stop_listening(self):
        self.listening = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        # We don't join the thread immediately to avoid UI blocking, it will exit loop
        logger.info("STT Stopped Listening")

    def _process_audio(self):
        audio_buffer = []
        
        while self.listening:
            try:
                data = self.audio_queue.get(timeout=0.5)
                audio_buffer.append(data)
                
                while not self.audio_queue.empty():
                    audio_buffer.append(self.audio_queue.get())
            except queue.Empty:
                continue

        if audio_buffer:
            self.audio_buffer = audio_buffer

    def transcribe_accumulated(self):
        if not self.audio_buffer:
            return ""
        text = self._transcribe_buffer(self.audio_buffer)
        self.audio_buffer = []
        return text

    # RETHINKING IMPLEMENTATION FOR USER REQUEST:
    # "press it, it start to transcribe... press it again it stops... then that transcription is sent"
    
    def _get_input_device_index(self):
        """Find the best available input device that supports our target rate, or any rate."""
        # First, try to find a device that supports 16000Hz directly
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev.get('maxInputChannels') > 0:
                try:
                    if self.p.is_format_supported(RATE, input_device=i, input_channels=CHANNELS, input_format=FORMAT):
                        logger.info("Using device %d: %s (Supports %dHz)", i, dev.get('name'), RATE)
                        return i
                except Exception:
                    continue
        
        # If not, find the default input device
        try:
            default_dev = self.p.get_default_input_device_info()
            idx = default_dev.get('index')
            logger.info("Using default device %d: %s", idx, default_dev.get('name'))
            return idx
        except Exception:
            pass

        # Last resort: just find any input device
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev.get('maxInputChannels') > 0:
                logger.info("Falling back to device %d: %s", i, dev.get('name'))
                return i
                
        return None

    def start_capture(self):
        if self.listening: return True
        
        device_index = self._get_input_device_index()
        if device_index is None:
            logger.error("No input device found.")
            return False

        # Whisper needs exactly 16000Hz and Mono
        self.current_rate = RATE
        self.current_channels = CHANNELS
        
        logger.info("Opening stream for Whisper: %dHz, %d channels", self.current_rate, self.current_channels)

        self.listening = True
        self.audio_frames = []
        
        if not self.model: self.load_model()

        try:
            self.stream = self.p.open(format=FORMAT,
                            channels=self.current_channels,
                            rate=self.current_rate,
                            input=True,
                            input_device_index=device_index,
                            frames_per_buffer=CHUNK_SIZE,
                            stream_callback=self._capture_callback)
        except Exception as e:
            logger.error("Failed to open PyAudio stream natively at %dHz: %s", self.current_rate, e)
            self.listening = False
            return False
        logger.info("Capture Started")
        return True

    def _capture_callback(self, in_data, frame_count, time_info, status):
        if self.listening:
            self.audio_frames.append(in_data)
        return (None, pyaudio.paContinue)

    def stop_and_transcribe(self):
        self.listening = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        logger.info("Capture Stopped. Frames: %d", len(self.audio_frames))
        if not self.audio_frames:
            return ""
        
        # Process
        return self._transcribe_buffer(self.audio_frames)

    def _transcribe_buffer(self, frames):
        start_t = time.time()
        current_audio = b''.join(frames)
        
        # Convert to float32
        audio_np = np.frombuffer(current_audio, dtype=np.int16).astype(np.float32) / 32768.0

        # Transcribe
        segments, _ = self.model.transcribe(audio_np, beam_size=1, language="en", vad_filter=True)
        
        text = " ".join([s.text for s in segments]).strip()
        logger.info("Transcription (%.2fs): %s", time.time() - start_t, text)
        return text

    def terminate(self):
        self.p.terminate()


if __name__ == "__main__":
    # Test
    engine = STTEngine()
    engine.load_model()
    try:
        while True:
            input("Press Enter to Start Recording...")
            engine.start_capture()
            input("Press Enter to Stop and Transcribe...")
            text = engine.stop_and_transcribe()
            print(f"Final Text: {text}")
    except KeyboardInterrupt:
        engine.terminate()