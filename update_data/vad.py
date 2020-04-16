#!/home/wly/Miniconda3/bin/python
# -*- coding: utf-8 -*-
import collections
import contextlib
import sys
import wave
import os
import webrtcvad
import librosa
from pydub import AudioSegment

mode = 3


def read_wave(path):
    try:
        with contextlib.closing(wave.open(path, 'rb')) as wf:
            num_channels = wf.getnchannels()
            assert num_channels == 1
            sample_width = wf.getsampwidth()
            assert sample_width == 2
            sample_rate = wf.getframerate()
            assert sample_rate in (8000, 16000, 32000, 48000)
            pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate
    except:
        print('error', path)
        wavname = os.path.splitext(os.path.basename(path))[0]
        wavdir = os.path.dirname(path)
        newpath = os.path.join(wavdir, wavname + "2.wav")
        os.system("sox {} -c 1 -e signed -b 16 -r 16000 -t wav {}".format(path, newpath))
        # y, sr = librosa.load(path, sr=None)
        # y_16k = librosa.resample(y, sr, 16000)
        # y_16k_mono = librosa.to_mono(y_16k)
        # librosa.output.write_wav(newpath,y_16k_mono,16000)
        with wave.open(newpath, 'rb') as wf:
            sample_rate = wf.getframerate()
            pcm_data = wf.readframes(wf.getnframes())
        os.remove(newpath)
        return pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    """Writes a .wav file.
    Takes path, PCM audio data, and sample rate.
    """
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


class Frame(object):
    """Represents a "frame" of audio data."""

    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


## qie fen bu yu liu shi jian
def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames):
    """Filters out non-voiced audio frames.
    Given a webrtcvad.Vad and a source of audio frames, yields only
    the voiced audio.
    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to detrigger.
    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.
    Arguments:
    sample_rate - The audio sample rate, in Hz.
    frame_duration_ms - The frame duration in milliseconds.
    padding_duration_ms - The amount to pad the window, in milliseconds.
    vad - An instance of webrtcvad.Vad.
    frames - a source of audio frames (sequence or generator).
    Returns: A generator that yields PCM audio data.
    """
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    ##pre_buffer = collections.deque(maxlen=4) ## 14 frames == 14 * 30ms = 0.42s
    # # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    # points = []
    count = 0
    i = 0
    while i < len(frames):
        is_speech = vad.is_speech(frames[i].bytes, sample_rate)

        # sys.stdout.write('1' if is_speech else '0')
        ##if i > 3:
        ##   pre_buffer.append((frames[i-4], is_speech))
        if not triggered:
            ring_buffer.append((frames[i], is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])
            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                startpoint = ring_buffer[0][0].timestamp
                # sys.stdout.write('+(%s)' % (ring_buffer[0][0].timestamp,))
                # # We want to yield all the audio we see from now until
                # # we are NOTTRIGGERED, but we have to start with the
                # # audio that's already in the ring buffer.
                ##for f, s in pre_buffer: ## add pre 14 frames
                ##    voiced_frames.append(f)

                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frames[i])
            ring_buffer.append((frames[i], is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                endpoint = frames[i].timestamp - (padding_duration_ms / 1000)
                # points.append((startpoint, endpoint))
                count = count + 1
                # sys.stdout.write('-(%s)' % (frames[i].timestamp + frames[i].duration))
                triggered = False
                j = 0
                content = []
                while j < len(voiced_frames) - 10:
                    content.append(voiced_frames[j].bytes)
                    j = j + 1
                yield count, b''.join(content), (startpoint, endpoint)
                ring_buffer.clear()
                voiced_frames = []
        i = i + 1
    if triggered:
        endpoint = frames[i - 1].timestamp - (padding_duration_ms / 1000)
        # points.append((startpoint, endpoint))
        count = count + 1
        # sys.stdout.write('-(%s)' % (frames[i-1].timestamp + frames[i-1].duration))
    # sys.stdout.write('\n')
    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield count, b''.join([f.bytes for f in voiced_frames]), (startpoint, endpoint)


def get_wav_time(wav_path):
    try:
        file = wave.open(wav_path)
        # print('---------声音信息------------')

        a = file.getparams().nframes  # 帧总数
        f = file.getparams().framerate  # 采样频率
        # sample_time = 1 / f  # 采样点的时间间隔
        time = a / f  # 声音信号的长度
    except Exception:
        print(wav_path+" open error")
        return 0

    return time


def get_all_file(rawdir):
    allfile = []
    for root, dirs, files in os.walk(rawdir):
        for f in files:
            if ".wav" in f:
                allfile.append(os.path.join(root, f))

    return allfile


# 传入一个wav路径，返回静音段的开始结束时间点，以及语音总时长
def get_wav_start_end(f):
    global mode
    try:
        audio, sample_rate = read_wave(f)
    except Exception as e:
        print(e)
    t_all = get_wav_time(f)
    vad = webrtcvad.Vad(mode)
    frames = frame_generator(30, audio, sample_rate)
    frames = list(frames)
    segments = vad_collector(sample_rate, 30, 300, vad, frames)
    # sound = AudioSegment.from_wav(f)
    start = 0.0
    end = 0.0
    for i, segment in enumerate(segments):
        if i == 0:
            start = segment[2][0]
        end = segment[2][1]
    return start, end, t_all



