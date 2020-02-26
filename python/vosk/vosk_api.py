import wave
import json
import logging

pyaudio_available = False
try:
    import pyaudio
    pyaudio_available = True
except:
    logging.warn('pyaudio not available. recognition with microphone will not work')

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

def get_recognizer(model, sample_rate, spk_model=None, grammar=None):
    recognizer = None
    try:
        if spk_model is None:
            if grammar:
                recognizer = KaldiRecognizer(model, sample_rate, grammar)
            else:
                recognizer = KaldiRecognizer(model, sample_rate)
        else:
            if grammar:
                recognizer = KaldiRecognizer(model, spk_model, sample_rate, grammar)
            else:
                recognizer = KaldiRecognizer(model, spk_model, sample_rate)
    except Exception as ex:
        logging.exception(ex, exc_info=True)
    
    return recognizer
  
class Recognizer:
    model = None
    sample_rate = None
    spk_model = None
    grammar = None
    def __init__(self, model, sample_rate, spk_model=None, grammar=None):
        # For wav pcm files, sample_rate and frame_rate mean the samething.
        self.model = model
        self.sample_rate = sample_rate
        self.spk_model = spk_model
        self.grammar = grammar
    
    def recognize(self, path_to_wav, recognise_from_microphone=False, return_audio=False, include_final_result=True, n_frames=1000):
        recognizer = get_recognizer(self.model, self.sample_rate, self.spk_model, self.grammar)

        if recognizer is None:
            return [False]

        if not pyaudio_available and recognise_from_microphone:
            logging.error('pyaudio is not available. recognition from microphone is not possible.')
            return [False]

        if recognise_from_microphone:
            p = pyaudio.PyAudio()
            wav_f = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        
        else:
            wav_f = wave.open(path_to_wav, 'rb')
        
        if wav_f.getnchannels() != 1 or wav_f.getsampwidth() != 2 or wav_f.getcomptype() != "NONE":
            logging.error("Only PCM format wav files with single channel are supported.")
            return [False]
        
        while True:
            current_data = wav_f.readframes(n_frames)
            
            if len(current_data) == 0:
                #processing done
                break
            
            current_res = None
            if recognizer.AcceptWaveform(current_data):
                current_res = recognizer.Result()
            else:
                current_res = recognizer.PartialResult()
            
            current_res = json.loads(current_res)

            yield current_res

        if include_final_result:
            yield json.loads(recognizer.FinalResult())
        