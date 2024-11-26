import pyaudio
import wave
import paho.mqtt.client as mqtt
import json


# -------- MQTT Settings
BROKER = "test.mosquitto.org"  
COMMAND_TOPIC = "BMM/audio/conf"
DATA_TOPIC = "BMM/audio/files"
CLIENT_ID = "BMM"

## ------- Default configurations

DEFAULT_NUMBER_FILES =1
DEFAULT_SAMPLES = 1024  # Record in chunks of 1024 samples
#DEFAULT_FORMAT = pyaudio.paInt16  # 16 bits per sample
DEFAULT_CHANNEL = 1 # corresponds to the macOS microphone
DEFAULT_fs = 44100  # Recorded samples / second
DEFAULT_DURATION = 5
recording = False





# ----- MQTT RECEIVING CONDITIONS FROM THE CLOUD ------

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code", rc)
    client.subscribe(COMMAND_TOPIC)


def on_message(client, userdata, msg):
    global number_files, samples, channel, fs, duration, recording
    payload = json.loads(msg.payload.decode())

    if 'number_files' in payload:
        number_files = int(payload['number_files'])
        print(f"Updating number of files to be recorded to {number_files}")
    else:
        number_files= DEFAULT_NUMBER_FILES


    if 'samples' in payload:
        samples = int(payload['samples'])
        print(f"Number of samples per file: {samples}")
    else:
        samples= DEFAULT_SAMPLES

    if 'channel' in payload:
        channel = int(payload['channel'])
        print(f"Channel: {channel}") #on MacOS, it's 0 for the normal microphone. In others, idk. This gives the option to set it for different systems or microphones
    else:
        samples= DEFAULT_CHANNEL
     
    if 'fs' in payload:
        fs = int(payload['fs'])
        print(f"Updated sampling rate to {fs} Hz")
    else:
        fs = DEFAULT_fs  # Reset to default if no sampling rate is provided
        print(f"No sampling rate received, using default: {fs} Hz")

    if 'duration' in payload:
        samples = int(payload['duration'])
        print(f"Duration of audio file: {duration}s")
    else:
        samples= DEFAULT_DURATION
        
    if 'command' in payload:
        if payload['command'] == "start":
            print("Starting recording")
            recording = True
            record(fs=fs)
        elif payload['command'] == "stop":
            print("Stopping recording")
            recording = False




## -------- Creating a function to record
def record(number_files, samples, channel, fs, duration): # the idea is i set the number of files, samples, channels... that i want through streamlit
    # ------ Recording segment -------
    global recording
    p = pyaudio.PyAudio()  # Create an interface to PortAudio
    for i in range(number_files):
       filename = f"recording_{i + 1}.wav"
       print(f'Recording audio file number{i+1}')
       stream = p.open(channel,
                        rate=fs,
                        frames_per_buffer=samples,
                        input=True)
       
       #storing the audio
       frames = []
       for k in range(0, int(fs / samples * duration)):
            data = stream.read(samples)
            frames.append(data)
            client.publish(DATA_TOPIC, data) --> para enviar ao broker
       wf = wave.open(filename, 'wb')  
       wf.setnchannels(channel)
       wf.setsampwidth(pyaudio.paInt16)
       wf.setframerate(fs)
       wf.writeframes(b''.join(frames))
       wf.close()
   
    print(f"Finished recording file {filename}")
    stream.stop_stream()
    stream.close()
    p.terminate()

    print('All desired files recorded')

# ------ MQTT Client Setup
client = mqtt.Client(CLIENT_ID)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883, 60)

# Start MQTT loop
client.loop_start()


        