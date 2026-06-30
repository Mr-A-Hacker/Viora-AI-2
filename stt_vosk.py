import logging
import queue
import threading
import sys
import json
import pyaudio

logger = logging.getLogger(__name__)
from vosk import Model, KaldiRecognizer

# --- CONFIGURATION ---
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LOCAL_DIR = os.environ.get("LOCAL_DIR", "./models")
MODEL_PATH = os.environ.get("VOSK_MODEL", os.path.join(LOCAL_DIR, "vosk-model-small-en-us-0.15"))

CHUNK_SIZE = 4000           # Frames per buffer
FORMAT = pyaudio.paInt16    # 16-bit PCM
CHANNELS = 1                # Mono
RATE = 16000                # Vosk standard sample rate
import numpy as np
try:
    import scipy.signal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ---------------------

class STTEngine:
    def __init__(self):
        self.model = None
        self.recognizer = None
        self.listening = False
        self.audio_queue = queue.Queue()
        self.thread = None
        self.stream = None
        self.p = pyaudio.PyAudio()
        self.final_text = ""
        self.current_rate = RATE
        self.device_index = None

    def load_model(self):
        if self.model is None:
            logger.debug("Loading Vosk model from '%s'...", MODEL_PATH)
            try:
                self.model = Model(MODEL_PATH)
                self.recognizer = KaldiRecognizer(self.model, RATE)
                logger.debug("Vosk model loaded successfully.")
            except Exception as e:
                logger.error("Error loading model: %s", e)
                logger.error("Please double-check that this exact path contains the model files (like 'am', 'conf', 'graph', etc.): %s", MODEL_PATH)
                sys.exit(1)

    def _get_input_device_index(self):
        """Find the best available input device that supports our target rate, or any rate."""
        # First, try to find a device that supports 16000Hz directly
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev.get('maxInputChannels') > 0:
                try:
                    if self.p.is_format_supported(RATE, input_device=i, input_channels=CHANNELS, input_format=FORMAT):
                        logger.debug("Using device %d: %s (Supports %dHz)", i, dev.get('name'), RATE)
                        return i, RATE
                except Exception:
                    continue
        
        # If not, find the default input device and get its default rate
        try:
            default_dev = self.p.get_default_input_device_info()
            idx = default_dev.get('index')
            rate = int(default_dev.get('defaultSampleRate'))
            logger.debug("Using default device %d: %s (Default rate: %dHz)", idx, default_dev.get('name'), rate)
            return idx, rate
        except Exception:
            pass

        # Last resort: just find any input device
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev.get('maxInputChannels') > 0:
                rate = int(dev.get('defaultSampleRate'))
                logger.debug("Falling back to device %d: %s (Rate: %dHz)", i, dev.get('name'), rate)
                return i, rate
                
        return None, None

    def _mic_callback(self, in_data, frame_count, time_info, status):
        """Puts live audio frames into a queue for the background thread."""
        if self.listening:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start_listening(self, callback=None):
        if self.listening: 
            return
        
        if not self.model: 
            self.load_model()
            
        self.device_index, self.current_rate = self._get_input_device_index()
        if self.device_index is None:
            logger.error("No input device found.")
            return

        self.listening = True
        self.callback = callback
        self.audio_queue = queue.Queue() # Clear the queue
        self.final_text = ""
        
        logger.debug("Opening Vosk stream: %dHz, %d channels", self.current_rate, CHANNELS)
        self.stream = self.p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=self.current_rate,
                        input=True,
                        input_device_index=self.device_index,
                        frames_per_buffer=CHUNK_SIZE,
                        stream_callback=self._mic_callback)
        
        self.thread = threading.Thread(target=self._process_audio, daemon=True)
        self.thread.start()

    def stop_listening(self):
        self.listening = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.thread:
            self.thread.join()
        
        return self.final_text

    def _process_audio(self):
        """Background loop that continuously passes the audio queue to Vosk."""
        accumulated_text = []

        while self.listening or not self.audio_queue.empty():
            try:
                data = self.audio_queue.get(timeout=0.1)
                
                # Resample if necessary
                if self.current_rate != RATE:
                    audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                    if HAS_SCIPY:
                        num_samples = int(len(audio_np) * RATE / self.current_rate)
                        audio_np = scipy.signal.resample(audio_np, num_samples)
                    else:
                        num_samples = int(len(audio_np) * RATE / self.current_rate)
                        audio_np = np.interp(
                            np.linspace(0, len(audio_np), num_samples),
                            np.arange(len(audio_np)),
                            audio_np
                        )
                    data = audio_np.astype(np.int16).tobytes()

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        accumulated_text.append(text)
                        if self.callback:
                            full = ' '.join(accumulated_text)
                            try:
                                self.callback(full, is_partial=False)
                            except TypeError:
                                self.callback(full)
                
                else:
                    partial_result = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_result.get("partial", "")
                    if partial_text:
                        current_live = ' '.join(accumulated_text + [partial_text])
                        if self.callback:
                            try:
                                self.callback(current_live, is_partial=True)
                            except TypeError:
                                self.callback(current_live)

            except queue.Empty:
                pass

        # Flush any remaining audio in the buffer when stopped
        final_result = json.loads(self.recognizer.FinalResult())
        final_text = final_result.get("text", "")
        if final_text:
            accumulated_text.append(final_text)

        self.final_text = ' '.join(accumulated_text).strip()
        if self.callback:
            try:
                self.callback(self.final_text, is_partial=False)
            except TypeError:
                self.callback(self.final_text)

    def terminate(self):
        self.p.terminate()

if __name__ == "__main__":
    def _print_transcript(text, is_partial=False):
        """Print transcription in real time; partial overwrites the line, final prints newline."""
        end = "\r" if is_partial else "\n"
        print(text, end=end, flush=True)

    engine = STTEngine()
    try:
        engine.load_model()
        while True:
            input("\nPress Enter to Start Recording...")
            engine.start_listening(callback=_print_transcript)
            print("Listening... (Press Enter to stop)")
            input()
            final_text = engine.stop_listening()
            print(f"--- Captured: {final_text} ---")
    except KeyboardInterrupt:
        engine.terminate()
