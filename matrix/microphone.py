"""Push-to-talk microphone capture followed by local Whisper transcription."""

import plistlib
import sys
import wave
from array import array
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from PyQt6.QtCore import QBuffer, QCoreApplication, QIODevice, QMicrophonePermission, QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices

from matrix.speech import transcribe


def pcm16(data, rate, channels, sample_type):
    typecode, scale, offset = {
        "UInt8": ("B", 256, 128), "Int16": ("h", 1, 0),
        "Int32": ("i", 1 / 65536, 0), "Float": ("f", 32768, 0),
    }[sample_type]
    samples = array(typecode)
    samples.frombytes(data[:len(data) - len(data) % samples.itemsize])
    frames = len(samples) // channels
    if frames < rate // 10:
        raise ValueError("The microphone did not deliver enough audio.")
    mono = [
        sum(samples[index:index + channels]) / channels
        for index in range(0, frames * channels, channels)
    ]
    result = array("h")
    for index in range(frames * 16_000 // rate):
        position = index * rate / 16_000
        left = int(position)
        right = min(left + 1, frames - 1)
        sample = mono[left] + (mono[right] - mono[left]) * (position - left)
        result.append(max(-32768, min(32767, int((sample - offset) * scale))))
    if sys.byteorder != "little":
        result.byteswap()
    return result.tobytes()


def has_macos_usage_description():
    path = Path(QCoreApplication.applicationFilePath()).parent.parent / "Info.plist"
    try:
        with path.open("rb") as stream:
            return bool(plistlib.load(stream).get("NSMicrophoneUsageDescription"))
    except (OSError, ValueError, plistlib.InvalidFileException):
        return False


class Microphone(QObject):
    state = pyqtSignal(str)
    message = pyqtSignal(str)
    transcript = pyqtSignal(str)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.source = None
        self.buffer = None
        self.format = None
        self.device_id = ""
        self.port_stream = None
        self.port_data = bytearray()
        self.port_rate = None
        self.pending = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.stop)

    def toggle(self):
        if self.active:
            self.stop()
            return
        if self.pending:
            return
        if sys.platform == "darwin" and not has_macos_usage_description():
            self.message.emit("Open the Jacked Jarvis app bundle to grant microphone access on macOS.")
            return
        permission = QMicrophonePermission()
        status = self.app.checkPermission(permission)
        if status == Qt.PermissionStatus.Granted:
            self.start()
        elif status == Qt.PermissionStatus.Undetermined:
            self.pending = True
            self.state.emit("requesting")
            self.app.requestPermission(permission, self.permission_result)
        else:
            guidance = {
                "darwin": "Enable Jacked Jarvis under Privacy & Security → Microphone.",
                "win32": "Enable microphone access for desktop apps under Privacy & security → Microphone.",
            }.get(sys.platform, "Check the desktop or sandbox audio-input permission.")
            self.message.emit("Microphone access is off. " + guidance)

    def permission_result(self, _result):
        self.pending = False
        if self.app.checkPermission(QMicrophonePermission()) == Qt.PermissionStatus.Granted:
            self.start()
        else:
            self.message.emit("Microphone permission was declined.")
            self.state.emit("idle")

    def start(self):
        devices = QMediaDevices.audioInputs()
        device = QMediaDevices.defaultAudioInput()
        if self.device_id:
            device = next((item for item in devices if bytes(item.id()).hex() == self.device_id), None)
        if device is None or device.isNull():
            self.message.emit("No microphone is available.")
            self.state.emit("idle")
            return
        audio_format = device.preferredFormat()
        if not audio_format.isValid() or audio_format.sampleFormat() == QAudioFormat.SampleFormat.Unknown:
            self.start_portaudio(device.description())
            return
        self.format = audio_format
        self.source = QAudioSource(device, audio_format, self)
        self.buffer = QBuffer(self)
        self.buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        self.source.start(self.buffer)
        if self.source.error().name != "NoError":
            error = self.source.error().name
            self.reset()
            self.message.emit(f"Could not start microphone capture ({error}).")
            self.state.emit("idle")
            return
        self.message.emit(f"Recording from {device.description()}.")
        self.timer.start(30_000)
        self.state.emit("recording")

    @property
    def active(self):
        return self.source is not None or self.port_stream is not None

    def start_portaudio(self, name):
        try:
            import sounddevice
        except ImportError:
            self.message.emit("This input needs the local sounddevice package. Install it in the desktop Python environment.")
            self.state.emit("idle")
            return
        try:
            devices = sounddevice.query_devices()
            index = next((i for i, item in enumerate(devices)
                          if item["name"] == name and item["max_input_channels"] > 0), None)
            if index is None:
                raise ValueError(f"PortAudio could not locate the selected input {name}.")
            self.port_rate = int(devices[index]["default_samplerate"])
            self.port_data.clear()
            self.port_stream = sounddevice.RawInputStream(
                device=index, samplerate=self.port_rate, channels=1, dtype="int16",
                callback=self.capture_portaudio,
            )
            self.port_stream.start()
        except (OSError, RuntimeError, ValueError, sounddevice.PortAudioError) as error:
            self.reset()
            self.message.emit(f"Could not capture {name}: {error}")
            self.state.emit("idle")
            return
        self.message.emit(f"Recording from {name} through PortAudio.")
        self.timer.start(30_000)
        self.state.emit("recording")

    def capture_portaudio(self, data, _frames, _timing, _status):
        remaining = max(0, self.port_rate * 2 * 30 - len(self.port_data))
        self.port_data.extend(bytes(data)[:remaining])

    def reset(self):
        self.timer.stop()
        if self.port_stream is not None:
            self.port_stream.close()
        self.port_stream = None
        self.port_data.clear()
        if self.source is not None:
            self.source.stop()
            self.source.deleteLater()
        if self.buffer is not None:
            self.buffer.close()
            self.buffer.deleteLater()
        self.source = self.buffer = None

    def stop(self):
        if not self.active:
            return
        if self.port_stream is not None:
            self.port_stream.stop()
            data = bytes(self.port_data)
            rate, channels, sample_type = self.port_rate, 1, "Int16"
        else:
            self.source.stop()
            data = bytes(self.buffer.data())
            rate, channels, sample_type = self.format.sampleRate(), self.format.channelCount(), self.format.sampleFormat().name
        self.reset()
        self.message.emit(f"Captured {len(data):,} audio bytes for local transcription.")
        self.state.emit("transcribing")
        Thread(
            target=self.recognize,
            args=(data, rate, channels, sample_type),
            daemon=True,
        ).start()

    def recognize(self, data, rate, channels, sample_type):
        try:
            samples = pcm16(data, rate, channels, sample_type)
            with TemporaryDirectory(prefix="jacked-mic-") as directory:
                clip = Path(directory) / "prompt.wav"
                with wave.open(str(clip), "wb") as output:
                    output.setparams((1, 2, 16_000, 0, "NONE", "not compressed"))
                    output.writeframes(samples)
                text = transcribe(clip)
            self.transcript.emit(text)
        except (OSError, RuntimeError, ValueError) as error:
            self.message.emit(str(error))
        finally:
            self.state.emit("idle")
