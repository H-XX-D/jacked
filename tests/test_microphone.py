from array import array
from types import SimpleNamespace
import unittest
from unittest.mock import patch

try:
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtMultimedia import QAudioFormat
    from matrix.microphone import Microphone, pcm16
except ImportError:
    Microphone = None


@unittest.skipIf(Microphone is None, "Optional Qt Multimedia desktop dependencies are absent")
class MicrophoneTests(unittest.TestCase):
    def test_stereo_conversion_resamples_and_averages_channels(self):
        raw = array("h", [1200, -1200] * 4800).tobytes()
        result = pcm16(raw, 48000, 2, "Int16")
        self.assertEqual(len(result), 3200)
        self.assertTrue(all(value == 0 for value in array("h", result)))
        with self.assertRaises(ValueError):
            pcm16(b"", 48000, 2, "Int16")

    def test_native_input_captures_and_cancels(self):
        app = QCoreApplication.instance() or QCoreApplication([])
        microphone = Microphone(app)
        native = QAudioFormat()
        native.setSampleRate(48000)
        native.setChannelCount(2)
        native.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        usable = SimpleNamespace(preferredFormat=lambda: native, isNull=lambda: False,
                                 description=lambda: "Usable test input")
        stopped = []

        class Source:
            def __init__(self, device, audio_format, parent):
                self.device = device

            def start(self, destination):
                destination.write(b"\0" * 3200)

            def error(self):
                return SimpleNamespace(name="NoError")

            def stop(self):
                stopped.append(True)

            def deleteLater(self):
                pass

        with patch("matrix.microphone.QMediaDevices.defaultAudioInput", return_value=usable), \
                patch("matrix.microphone.QMediaDevices.audioInputs", return_value=[usable]), \
                patch("matrix.microphone.QAudioSource", Source):
            microphone.start()
        self.assertIs(microphone.source.device, usable)
        self.assertEqual(len(microphone.buffer.data()), 3200)
        microphone.reset()
        self.assertTrue(stopped)
        self.assertIsNone(microphone.buffer)

    def test_invalid_qt_format_uses_the_same_input_with_portaudio(self):
        app = QCoreApplication.instance() or QCoreApplication([])
        microphone = Microphone(app)
        device = SimpleNamespace(preferredFormat=QAudioFormat, isNull=lambda: False,
                                 description=lambda: "Volt 1")

        class Stream:
            def __init__(self, **kwargs):
                self.settings = kwargs

            def start(self):
                self.settings["callback"](b"\0" * 3200, 1600, None, None)

            def stop(self):
                pass

            def close(self):
                pass

        sdk = SimpleNamespace(
            query_devices=lambda: [{"name": "Volt 1", "max_input_channels": 2, "default_samplerate": 44100}],
            RawInputStream=Stream, PortAudioError=RuntimeError,
        )
        import sys
        with patch("matrix.microphone.QMediaDevices.defaultAudioInput", return_value=device), \
                patch("matrix.microphone.QMediaDevices.audioInputs", return_value=[device]), \
                patch.dict(sys.modules, {"sounddevice": sdk}):
            microphone.start()
        self.assertTrue(microphone.active)
        self.assertEqual(microphone.port_stream.settings["device"], 0)
        self.assertEqual(len(microphone.port_data), 3200)
        microphone.reset()
        self.assertFalse(microphone.active)
