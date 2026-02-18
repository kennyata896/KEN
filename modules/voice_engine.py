import speech_recognition as sr
import pyttsx3
import pygame
import asyncio
import os
import io
import torch
from faster_whisper import WhisperModel

class KenVoice:
    def __init__(self):
        print("🔊 Voice Engine: Loading Faster-Whisper (Optimized GPU)...")
        
        # 1. SETUP GPU ENGINE
        # 'float16' is crucial for RTX 4060 speed.
        model_size = "medium.en" # 'medium' is much smarter than 'small'. Since we use faster-whisper, it fits!
        
        try:
            self.model = WhisperModel(model_size, device="cuda", compute_type="float16")
            print(f"   (Model '{model_size}' loaded on GPU)")
        except Exception as e:
            print(f"⚠️ GPU Error: {e}. Falling back to CPU (Slow).")
            self.model = WhisperModel("small.en", device="cpu", compute_type="int8")

        # 2. CONTEXT PRIMING (The "Smart" Hack)
        # We tell the model what words to expect. This fixes 90% of typos.
        self.context_prompt = (
            "Ken, Aider, Python, Code, config.py, main.py, reptile.py, "
            "scheduler, async, await, debug, fix, function, variable."
        )

        # 3. MICROPHONE SETUP
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6 

        # 4. TTS SETUP
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)
        pygame.mixer.init()

    def listen(self):
        """
        Direct-to-Memory Transcription with Context Injection.
        """
        with sr.Microphone() as source:
            try:
                # Capture Audio
                audio_data = self.recognizer.listen(source, timeout=None, phrase_time_limit=10)
                
                # OPTIMIZATION: Don't save to disk. Use RAM (BytesIO).
                wav_bytes = audio_data.get_wav_data()
                wav_stream = io.BytesIO(wav_bytes)
                
                # Transcribe using Faster-Whisper
                # beam_size=5 makes it check 5 possibilities for every word (smarter)
                segments, info = self.model.transcribe(
                    wav_stream, 
                    beam_size=5, 
                    initial_prompt=self.context_prompt, # <--- Fixes technical jargon
                    vad_filter=True # <--- Filters out heavy breathing/static
                )
                
                # Combine segments
                text = " ".join([segment.text for segment in segments]).strip()
                
                if not text: return None
                return text.lower()
                
            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                # print(f"Ear Error: {e}") 
                return None

    async def speak(self, text):
        if not text: return
        clean_text = text.replace("[DEPLOY_CODER]", "").replace("[CHECK_STATUS]", "").replace("*", "")
        if not clean_text.strip(): return

        file_path = "temp_speech.wav"
        await asyncio.to_thread(self._save_audio, clean_text, file_path)
        
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"❌ Audio Error: {e}")

    def _save_audio(self, text, filename):
        self.engine.save_to_file(text, filename)
        self.engine.runAndWait()