import paho.mqtt.client as mqtt
import json
import base64
import sounddevice as sd
import io 
import wave
## isto é o gravador ------------
# -------- MQTT Settings
BROKER = "broker.hivemq.com"  
COMMAND_TOPIC = "BMM/audio/conf"
DATA_TOPIC = "BMM/audio/files"
CLIENT_ID = "BMMend"

## ------- Default configurations

DEFAULT_NUMBER_FILES =1
DEFAULT_SAMPLES = 1024  # Record in chunks of 1024 samples
#DEFAULT_FORMAT = pyaudio.paInt16  # 16 bits per sample
DEFAULT_CHANNEL = 1 # corresponds to the macOS microphone
DEFAULT_fs = 44100  # Recorded samples / second
DEFAULT_DURATION = 5



def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code", rc)
    client.subscribe(COMMAND_TOPIC)

global recording 
recording = False
global encoded_data
def on_message(client, userdata, msg):
    print('message')
    global  recording
    global encoded_data
    payload = msg.payload.decode()
    if payload == "start":
        print("Starting recording")
        print("Recording for 5  seconds...")
        audio_data = sd.rec(int(5 * 44100), samplerate=44100, channels= 1, dtype='float32', device = 0)
        sd.wait()  # Wait until recording is finished
        print("Recording completed.")
        data = audio_data.tobytes()
        client.publish(DATA_TOPIC, data)
    else:
        print("Not recording")
# ------ MQTT Client Setup
client = mqtt.Client(client_id=CLIENT_ID)
print('conected')
client.on_connect = on_connect
print('2')
client.on_message = on_message
print('3')
client.connect(BROKER, 1883, 60)
print('connected')


# Start MQTT loop
client.loop_forever()
print('loop')

