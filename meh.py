import sounddevice as sd
import numpy as np
import wave


# Get detailed information about the selected device

device_index = 0
duration = 5
device_info = sd.query_devices(device_index, 'input')
samplerate = int(device_info['default_samplerate'])
channels = device_info['max_input_channels']  # Auto-detect channels


sd.default.samplerate = 44100
sd.default.channels = 1
devices = sd.query_devices()
print(devices)

def callback(indata, frames, time, status):
    if status:
        print(status)

print(f"Recording for {duration} seconds...")
audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='float32', device=device_index)
sd.wait()  # Wait until recording is finished
print("Recording completed.")

filename = "teste.wav"
with wave.open(filename, 'w') as wf:
    wf.setnchannels(channels)  # Stereo
    wf.setsampwidth(2)  # 16-bit audio
    wf.setframerate(samplerate)
    wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

print(f"Audio saved to {filename}")