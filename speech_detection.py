import pyaudio
from array import array
from collections import deque
from queue import Queue, Full
from threading import Thread
import numpy as np
import wave

import time

# const values for mic streaming
CHUNK = 1024 # 음성데이터를 불러올 때 한번에 몇개의 정수를 불러올지
BUFF = CHUNK * 10
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
WAVE_OUTPUT_FILENAME = 'output.wav'


# const valaues for silence detection
SILENCE_THREASHOLD = 32767
SILENCE_END_THREASHOLD = 1000
SILENCE_SECONDS = 3
RECORD_SECONDS = 15

def main():
    q = Queue()
    t = Thread(target=listen, args=(q,))
    t.start()
# define listen function for threading
def listen(q):
    # open stream
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    # FIXME: release initial noisy data (1sec)
    #for _ in range(0, int(RATE / CHUNK)):
    #    data = stream.read(CHUNK, exception_on_overflow=False)

    is_started = False
    #vol_que = deque(maxlen=SILENCE_SECONDS)
    vol_end_que = deque(maxlen = SILENCE_SECONDS)

    print('start listening')
    frames = []
    while True:
        try:
            # define temporary variable to store sum of volume for 1 second 
            vol_sum = 0

            # read data for 1 second in chunk
            for _ in range(0, int(RATE / CHUNK)):
                data = stream.read(CHUNK, exception_on_overflow=False)

                # get max volume of chunked data and update sum of volume
                vol = max(array('h', data))
                vol_sum += vol

                # if status is listening, check the volume value
                if not is_started:
                    print(vol)
                
                    if vol >= SILENCE_THREASHOLD:
                        print('start of speech detected')
                        is_started = True

                # if status is speech started, write data
                if is_started:
                    #q.put(data)
                    frames.append(data)

            # if status is speech started, update volume queue and check silence
            if is_started:
                #vol_que.append(vol_sum / (RATE / CHUNK) < SILENCE_THREASHOLD)
                if vol < SILENCE_END_THREASHOLD and ((vol_sum / (RATE / CHUNK)) < SILENCE_END_THREASHOLD):
                    vol_end_que.append(vol_sum / (RATE / CHUNK) < SILENCE_END_THREASHOLD)
                    if len(vol_end_que) == SILENCE_SECONDS and all(vol_end_que):
                        print('end of speech detected')
                        break
        except Full:
            print('except')
            pass

    # close stream
    stream.stop_stream()
    stream.close()
    audio.terminate()
    print('audio terminate')
    
    # save audio file
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

if __name__ == '__main__':
    main()
    time.sleep(5)

