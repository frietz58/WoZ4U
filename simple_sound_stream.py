import sounddevice as sd
import time
import numpy as np

from utils import rawToWav

import naoqi
from naoqi import ALProxy

CHANNELS = 1
SAMPLE_RATE = 48000
IP = "130.239.182.11"
PORT = 9559
MOD_NAME = "SpeechRecognition"


#  we need to inherit from ALModule so that we can subscribe to the audio device...
class SpeechRecognitionModule(naoqi.ALModule):

    def __init__(self, strModuleName, strNaoIp):
        naoqi.ALModule.__init__(self, strModuleName)

        self.BIND_PYTHON(self.getName(), "callback")  # not sure what this does?
        self.strNaoIp = strNaoIp

        self.memory = naoqi.ALProxy("ALMemory")
        self.memory.declareEvent(self.getName())  # needed for callback

        # audio buffer
        self.buffer = []

        # sounddevice stream for audio playback in realtime
        self.stream = sd.OutputStream(channels=CHANNELS, samplerate=SAMPLE_RATE, dtype=np.int16)

        self.livestream = True

    def start(self):
        audio = naoqi.ALProxy("ALAudioDevice")
        nNbrChannelFlag = 3  # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2 AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        nDeinterleave = 0
        audio.setClientPreferences(self.getName(), SAMPLE_RATE, nNbrChannelFlag, nDeinterleave)  # setting same as default generate a bug !?!

        # we can only subscribe to the ALAudiodevice with an implementation of ALModule...
        # needs to have a "process" method that will be used as callback...
        audio.subscribe(self.getName())

        # also start the sounddevice stream so that we can write data on it
        self.stream.start()

    def processRemote(self, nbOfChannels, nbrOfSamplesByChannel, aTimeStamp, buffer):
        # this is our callback method!
        # Due to inheritance, this will be called once our module subscribes to the audio device in start()
        # Name may not be changed!

        # calculate a decimal seconds timestamp
        timestamp = float(str(aTimeStamp[0]) + "." + str(aTimeStamp[1]))
        print str(timestamp), "processRemote!!!!"

        aSoundDataInterlaced = np.fromstring(str(buffer), dtype=np.int16)
        aSoundData = np.reshape(aSoundDataInterlaced, (nbOfChannels, nbrOfSamplesByChannel), 'F')

        self.buffer.append(aSoundData)

        # write the callback data from ALAudiodevice to sounddevice stream, causing it to be played
        # we need to transpose, because sounddevice expects columns to be channels, and we get rows as channels
        if self.livestream:
            self.stream.write(aSoundData.T)

    def save_buffer(self):
        """
        Saves buffered audio data to physical .wav file.
        :param data:
        :return:
        """
        filename = "simple_out"
        outfile = open(filename + ".raw", "wb")
        data = self.transform_buffer()
        data.tofile(outfile)
        outfile.close()
        rawToWav(filename)
        print filename

    def transform_buffer(self):
        return np.concatenate(self.buffer, axis=1)[0]


def main():
    # kill previous instance, useful for developing ;)
    try:
        p = ALProxy(MOD_NAME)
        p.exit()
    except RuntimeError:  # when there is no instance in the broke...
        pass

    myBroker = naoqi.ALBroker(
        "myBroker",  # we need to use the broker when when we implement own module...
        "0.0.0.0",  # listen to anyone
        0,  # find a free port and use it
        str(IP),  # parent broker IP
        PORT)  # parent broker port

    # Warning: SpeechRecognition must be a global variable
    # The name given to the constructor must be the name of the
    # variable
    global SpeechRecognition
    SpeechRecognition = SpeechRecognitionModule("SpeechRecognition", IP)
    SpeechRecognition.start()

    # # sound quality testing
    # time.sleep(10)
    # SpeechRecognition.save_buffer()
    # sd.play(SpeechRecognition.transform_buffer(), 48000)
    # time.sleep(10)
    # exit(0)

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print('interrupted!')


if __name__ == "__main__":
    main()
