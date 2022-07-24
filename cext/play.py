import simpleaudio as sa
import cv2
import modems

# from https://realpython.com/playing-and-recording-sound-python/#:~:text=python%2Dsounddevice,-As%20stated%20in&text=In%20order%20to%20play%20WAV,WAV%20files%20as%20NumPy%20arrays.&text=The%20line%20containing%20sf.,its%20RIFF%20header%2C%20and%20sounddevice.

def play_file():
    filename = 'test_aprs.wav'
    wave_obj = sa.WaveObject.from_wave_file(filename)
    play_obj = wave_obj.play()
    play_obj.wait_done()  # Wait until sound has finished playing


def play_buffer():
    audio_data = modems.encode_afsk(['hello','world'], 11025)
    play_obj = sa.play_buffer(audio_data, 1, 2, 11025)
    play_obj.wait_done()

def play_sstv():
    img = cv2.imread('testcard.jpg')
    audio_data = modems.encode_sstv(img, 16000)
    play_obj = sa.play_buffer(audio_data, 1, 2, 16000)
    play_obj.wait_done()

play_sstv()