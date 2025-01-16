import streamlit as st
import paho.mqtt.client as mqtt
import time
import threading as th
from streamlit_autorefresh import st_autorefresh
from streamlit.runtime.scriptrunner import add_script_run_ctx
import os
import numpy as np
import io
import sounddevice as sd
import soundfile as sf

# MQTT Configurations
COMMAND_TOPIC = "BMM/audio/conf"
DATA_TOPIC = "BMM/audio/files"
BROKER = "broker.hivemq.com"
PORT = 1883
CLIENT_ID = "StreamlitClient"




st_autorefresh(interval=3000, key="fizzbuzzcounter")

if 'MyData' not in st.session_state:
    st.session_state['MyData'] = {
        'Run': False,
        'Broker' : BROKER,
        'TopicSub': DATA_TOPIC,
        'TopicPub': COMMAND_TOPIC,
        'audio_chunk': io.BytesIO(),
        'audio_filename':''
    }

if "ConnectionWidget" not in st.session_state:
        st.session_state["ConnectionWidget"]={
            'label': 'Disconnected',
            'status': 'info'
    }
def update_conection(label, status_type):
        st.session_state["ConnectionWidget"]['label'] = label
        st.session_state["ConnectionWidget"]['status'] = status_type
connection_label = st.session_state["ConnectionWidget"]['label']
connection_type = st.session_state["ConnectionWidget"]['status']     




## DATA RECEIVED WIDGET
if "ReceivedWidget" not in st.session_state:
            st.session_state["ReceivedWidget"]={
                'label': 'Waiting',
                'status': 'info'
        }
def received_status(label, status_type):
        st.session_state["ReceivedWidget"]['label'] = label
        st.session_state["ReceivedWidget"]['status'] = status_type
received_label = st.session_state["ReceivedWidget"]['label']
received_type = st.session_state["ReceivedWidget"]['status']



# MQTT Callbacks
def MQTT_TH(client): 
    def on_connect(client, userdata, flags, rc):
        if rc == 0:  
            print("connected")
            update_conection("Successfully connected", 'connected')
            
        else:
            print(f"Failed to connect, return code {rc}")
            update_conection("Disconnected Broker", 'failed')

        client.subscribe(DATA_TOPIC)  # Subscribe to the data topic
        st.session_state['MyData']['TopicSub'] = DATA_TOPIC
       

    def on_message(client, userdata, msg):
        AUDIO_SAVE_DIR = "/workspace/Project-AAI-microphone/received_audios"
        os.makedirs(AUDIO_SAVE_DIR, exist_ok=True)
        audio_filename = os.path.join(AUDIO_SAVE_DIR, f"audio_{int(time.time())}.wav")
        print("Message Received")
        received_status("DATA RECEIVED!", 'success')
        print(received_status("DATA RECEIVED!", 'success'))
        st.session_state['MyData']['audio_filename'] = audio_filename
        print(st.session_state['MyData']['audio_filename'])
        data = np.frombuffer(msg.payload, dtype=np.float32)
        st.session_state['MyData']['audio_chunk'] = data
        
        print(f"Received audio chunk with size {len(data)} bytes.")
        sample_rate = 44100  # Sample rate in Hz
        sf.write(audio_filename, data, sample_rate)
        print(f"Audio saved successfully as {audio_filename}")

    # MQTT setup
    client.on_connect = on_connect
    client.on_message = on_message
    print("MQTT INITIALIZATION")
    st.session_state['MyData']['Run'] = True
    client.connect(st.session_state['MyData']['Broker'], 1883, 60)
    client.loop_forever()
    print('MQTT link ended')
    st.session_state['MyData']['Run'] = False

if 'mqttThread' not in st.session_state or not st.session_state.mqttThread.is_alive():
    print('Initializing MQTT Client and Thread')
    st.session_state.mqttClient = mqtt.Client()
    st.session_state.mqttThread = th.Thread(target=MQTT_TH, args=[st.session_state.mqttClient])
    add_script_run_ctx(st.session_state.mqttThread) 

custom_theme = """
    <style>
        .title { 
            text-align:center;
            font-size: 50px;  
            color: #001A6E;  
            line-height: 1; 
            margin-top: 0px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        
        .stButton > button {
            width: 250px; 
            height: 50px; 
            background-color: #009990; 
            color:  #E1FFBB; 
            font-size: 20px; 
            font-weight: bold
            border: none; 
            padding: 10px 20px;
            border-radius:30px; 
            cursor: pointer;
        }
        .stButton > button:active {
            background-color: #074799; 
            color: #E1FFBB;
            font-weight: bold; 
        }
        .stButton > button:hover {
            font-weight: bold;
            background-color: #074799; 
            color:  #E1FFBB;
            border = #001A6E
        }
        
        .fullScreenFrame > div {
            display: flex;
            justify-content: center;
        }
    </style>
"""

st.markdown(custom_theme, unsafe_allow_html=True)


st.markdown( """
                    <div class='title'>AUDIO RECORDER CONTROLER</div>
                    """,
                    unsafe_allow_html= True)
       
col = st.columns((3, 3), gap='large')
with col[0]:
  
    if st.session_state['MyData']['Run']:
        if st.button('MQTT disconnect'):
            st.session_state['MyData']['mqttClient'].disconnect()
    else:
        if st.button('MQTT connect', key='start'):
            if not st.session_state.mqttThread.is_alive():
                st.session_state.mqttThread.start()
            else:
                st.warning("Thread is running")
                update_conection("Thread running", "failed")
    connection_placeholder = st.empty() 

        
    connection_label = st.session_state["ConnectionWidget"]['label']
    connection_type = st.session_state["ConnectionWidget"]['status']

       
    if connection_type == 'Disconnected':
        connection_placeholder.info(connection_label)
    elif connection_type == 'connected':
        connection_placeholder.success(connection_label)
    elif connection_type == 'failed':
        connection_placeholder.warning(connection_label)
    elif connection_type == 'waiting':
        connection_placeholder.error(connection_label) 

with col[1]: 
    
    if st.button('Start Recording', key='start_button'):
        st.session_state.mqttClient.publish(st.session_state['MyData']['TopicPub'], 'start')
        print('CHECKPOINT: Acquisition strat')
    received_placeholder = st.empty()

      
    received_label = st.session_state["ReceivedWidget"]['label']
    received_type = st.session_state["ReceivedWidget"]['status']

    if received_type == 'no_data':
        received_placeholder.info(received_label)
    elif received_type == 'success':
        received_placeholder.success(received_label)
    elif received_type == 'failed':
        received_placeholder.warning(received_label)
    elif received_type == 'waiting':
        received_placeholder.error(received_label)

file = st.session_state['MyData']['audio_filename']
st.markdown(
    f"""
    <p>File saved as: <strong>{file}</strong></p>
    """,
    unsafe_allow_html=True
)
AUDIO_SAVE_DIR = '/workspace/Project-AAI-microphone/received_audios'
audio_files = [f for f in os.listdir(AUDIO_SAVE_DIR) if f.endswith(('.wav', '.mp3', '.ogg'))]

if not audio_files:
    st.error("No audio files found in the directory.")
else:
    # Select an audio file
    selected_file = st.selectbox("Choose an audio file to play:", audio_files)

    # Path to the selected file
    audio_path = os.path.join(AUDIO_SAVE_DIR, selected_file)

    # Display audio player
    st.audio(audio_path)
