"""
    Implements a naoqi ALModule for live streaming of Pepper's microphone to default host default audio output device.
    Based on: https://github.com/JBramauer/pepperspeechrecognition/blob/master/module_speechrecognition.py

    Author: Finn Rietz
"""

import sounddevice as sd
from sounddevice import PortAudioError
import time
import numpy as np

from utils import rawToWav

import naoqi
from naoqi import ALProxy

CHANNELS = 1
SAMPLE_RATE = 48000
IP = "192.168.100.166"
PORT = 9559
MOD_NAME = "SpeechRecognition"


#  we need to inherit from ALModule so that we can subscribe to the audio device...
class SpeechRecognitionModule(naoqi.ALModule):

    def __init__(self, strModuleName, strNaoIp, noaPort):

        # kill previous instance, useful for developing ;)
        try:
            p = ALProxy(MOD_NAME)
            p.exit()
        except RuntimeError:  # when there is no instance in the broke...
            pass

        self.strNaoIp = strNaoIp
        self.naoPort = noaPort
        self.broker = self.setup_broker()  # setup naoqi broker for module communication

        try:
            naoqi.ALModule.__init__(self, strModuleName)  # init module
        except RuntimeError:
            # When module is already registered (eg camera tab has been closed and is now reopened)
            pass

        self.BIND_PYTHON(self.getName(), "callback")  # not sure what this does?

        self.memory = naoqi.ALProxy("ALMemory")
        self.memory.declareEvent(self.getName())  # needed for callback

        self.audio = naoqi.ALProxy("ALAudioDevice")

        # audio buffer
        self.buffer = []

        self.stream_latency = 0.5

        # sounddevice stream for audio playback in realtime
        # dtype=np.int16 is very important! This fixes the insane static noises
        self.stream = sd.OutputStream(channels=CHANNELS, samplerate=SAMPLE_RATE, dtype=np.int16, latency=self.stream_latency)

        self.livestream = True

        self.isStarted = False

    def setup_broker(self):
        return naoqi.ALBroker(
            "myBroker",     # we need to use the broker when when we implement own module...
            "0.0.0.0",      # listen to anyone
            0,              # find a free port and use it
            self.strNaoIp,  # parent broker IP
            self.naoPort)   # parent broker port

    def start(self):
        # audio = naoqi.ALProxy("ALAudioDevice")
        nNbrChannelFlag = 3  # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2 AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        nDeinterleave = 0
        self.audio.setClientPreferences(self.getName(), SAMPLE_RATE, nNbrChannelFlag,
                                        nDeinterleave)  # setting same as default generate a bug !?!

        # we can only subscribe to the ALAudiodevice with an implementation of ALModule...
        # needs to have a "process" method that will be used as callback...
        self.audio.subscribe(self.getName())

        # also start the sounddevice stream so that we can write data on it
        try:
            self.stream.start()
            self.isStarted = True
            # print "SD STREAM ACTIVE: ", self.stream.active
        except PortAudioError:
            # when stream has been closed, pointer become invalid, so we have to make a new stream
            self.stream = sd.OutputStream(channels=CHANNELS, samplerate=SAMPLE_RATE, dtype=np.int16, latency=self.stream_latency)
            self.stream.start()
            self.isStarted = True

    def stop(self):
        if not self.isStarted:
            return
        else:
            self.isStarted = False
            self.stream.close()
            self.audio.unsubscribe(self.getName())

    def processRemote(self, nbOfChannels, nbrOfSamplesByChannel, aTimeStamp, buffer):
        """
        This is our callback method!
        Due to inheritance, this will be called once our module subscribes to the audio device in start()
        Name of method may not be changed!
        :param nbOfChannels: param required for signature to work
        :param nbrOfSamplesByChannel: param required for signature to work
        :param aTimeStamp: param required for signature to work
        :param buffer: the actual, buffer audio data from Pepper's mic
        :return: None
        """
        if self.isStarted:
            # calculate a decimal seconds timestamp
            # timestamp = float(str(aTimeStamp[0]) + "." + str(aTimeStamp[1]))
            # print str(timestamp), "processRemote!!!!"

            aSoundDataInterlaced = np.fromstring(str(buffer), dtype=np.int16)
            aSoundData = np.reshape(aSoundDataInterlaced, (nbOfChannels, nbrOfSamplesByChannel), 'F')

            self.buffer.append(aSoundData)

            # write the callback data from ALAudiodevice to sounddevice stream, causing it to be played
            # we need to transpose, because sounddevice expects columns to be channels, and we get rows as channels
            if self.livestream:
                print np.shape(aSoundData)
                self.stream.write(aSoundData.T)

    def save_buffer(self):
        """
        Saves buffered audio data to physical .wav file.
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
        """
        Reshapes buffer matrix to 1d array of microphone energy values, so that it can be treated as audio data
        :return:
        """
        return np.concatenate(self.buffer, axis=1)[0]


def main():
    # Warning: SpeechRecognition must be a global variable
    # The name given to the constructor must be the name of the
    # variable
    global SpeechRecognition
    SpeechRecognition = SpeechRecognitionModule("SpeechRecognition", IP, PORT)
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
