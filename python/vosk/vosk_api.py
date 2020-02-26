import wave
import json
import pyaudio
import logging

from .vosk import KaldiRecognizer, Model, SpkModel
from . import utils

def load_model(name=None, spk_model_names={'spk-model'}):
    if not name:
        logging.error("name cannot be empty")
        return False

    model_dir = utils.download(name)

    try:
        if name in spk_model_names:
            loaded_model = SpkModel(model_dir)
        else:
            loaded_model = Model(model_dir)

        return loaded_model

    except Exception as ex:
        logging.exception(ex, exc_info=True)
        return False
        
class Recognizer:
    recognizer = None
    def __init__(self, model, sample_rate, spk_model=None, grammar=None):
        # For wav pcm files, sample_rate and frame_rate mean the samething.
        if spk_model is None:
            if grammar:
                self.recognizer = KaldiRecognizer(model, sample_rate, grammar)
            else:
                self.recognizer = KaldiRecognizer(model, sample_rate)
        else:
            if grammar:
                self.recognizer = KaldiRecognizer(model, spk_model, sample_rate, grammar)
            else:
                self.recognizer = KaldiRecognizer(model, spk_model, sample_rate)
    
    def recognize(self, path_to_wav, recognise_from_microphone=False, return_audio=False, include_final_result=True, n_frames=1000):
        if recognise_from_microphone:
            p = pyaudio.PyAudio()
            wav_f = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        
        else:
            wav_f = wave.open(path_to_wav, 'rb')
        
        if wav_f.getnchannels() != 1 or wav_f.getsampwidth() != 2 or wav_f.getcomptype() != "NONE":
            logging.error("Only PCM format wav files with single channel are supported.")
            return False
        
        while True:
            current_data = wav_f.readframes(n_frames)
            
            if len(current_data) == 0:
                #processing done
                break
            
            current_res = None
            if self.recognizer.AcceptWaveform(current_data):
                current_res = self.recognizer.Result()
            else:
                current_res = self.recognizer.PartialResult()
            
            current_res = json.loads(current_res)

            yield current_res

        if include_final_result:
            yield json.loads(self.recognizer.FinalResult())
        