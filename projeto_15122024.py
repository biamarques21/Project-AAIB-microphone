import pyaudio
import wave
import paho.mqtt.client as mqtt
import json
import base64
import os
import requests

# -------- MQTT Settings
BROKER = "127.0.0.1"  
COMMAND_TOPIC = "BMM/audio/conf"
CLIENT_ID = "BMM"

# GitHub settings
GITHUB_TOKEN = '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'  # Replace with your GitHub token
REPO_NAME = 'martabaptista05/Projeto'  # Replace with your GitHub repo name
GITHUB_API_URL = f'https://api.github.com/repos/{REPO_NAME}/contents/'
COMMIT_MESSAGE = "Upload de áudio via MQTT"

# ------- Default configurations
DEFAULT_NUMBER_FILES = 1
DEFAULT_SAMPLES = 1024  # Record in chunks of 1024 samples
DEFAULT_CHANNEL = 1  # corresponds to the macOS microphone
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
        number_files = DEFAULT_NUMBER_FILES

    if 'samples' in payload:
        samples = int(payload['samples'])
        print(f"Number of samples per file: {samples}")
    else:
        samples = DEFAULT_SAMPLES

    if 'channel' in payload:
        channel = int(payload['channel'])
        print(f"Channel: {channel}")
    else:
        channel = DEFAULT_CHANNEL

    if 'fs' in payload:
        fs = int(payload['fs'])
        print(f"Updated sampling rate to {fs} Hz")
    else:
        fs = DEFAULT_fs  # Reset to default if no sampling rate is provided
        print(f"No sampling rate received, using default: {fs} Hz")

    if 'duration' in payload:
        duration = int(payload['duration'])
        print(f"Duration of audio file: {duration}s")
    else:
        duration = DEFAULT_DURATION
        
    if 'command' in payload:
        if payload['command'] == "start":
            print("Starting recording")
            recording = True
            record(samples, channel, fs, duration)
        elif payload['command'] == "stop":
            print("Stopping recording")
            recording = False


## -------- Creating a function to record
def record(samples, channel, fs, duration):
    global recording
    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    # Gerar o nome do arquivo com base no número de arquivos existentes
    filename = generate_unique_filename()

    print(f'Recording audio file: {filename}')
    stream = p.open(format=pyaudio.paInt16,
                    channels=channel,
                    rate=fs,
                    frames_per_buffer=samples,
                    input=True)

    # storing the audio
    frames = []
    for k in range(0, int(fs / samples * duration)):
        data = stream.read(samples)
        frames.append(data)
    
    # Save the recording locally
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channel)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(b''.join(frames))
        
    if os.path.exists(filename):
        print(f"Arquivo {filename} salvo com sucesso.")
    else:
        print(f"Falha ao salvar o arquivo {filename}.")
    print(f"Finished recording file {filename}")

    # Enviar o arquivo para o GitHub
    upload_to_github(filename, REPO_NAME, GITHUB_TOKEN, COMMIT_MESSAGE)

    stream.stop_stream()
    stream.close()
    p.terminate()

    print('Recording finished and file uploaded to GitHub')


## -------- Function to upload the file to GitHub
def upload_to_github(file_path, repo_name, github_token, commit_message):
    # Extrair o nome do arquivo do caminho
    file_name = file_path.split('/')[-1]
    
    # URL para criar ou atualizar o arquivo no repositório
    url = f"https://api.github.com/repos/{repo_name}/contents/{file_name}"

    # Verificar se o arquivo já existe no repositório
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    
    # Caso o arquivo não exista, a resposta será um erro 404
    if response.status_code == 404:
        sha = None
    elif response.status_code == 200:
        # O arquivo existe, então precisamos do sha para atualizar
        sha = response.json()['sha']
    else:
        print(f"Erro ao verificar arquivo: {response.status_code} - {response.text}")
        return

    # Ler o conteúdo do arquivo a ser enviado
    with open(file_path, "rb") as f:
        content = f.read()
    
    # Codificar o conteúdo em base64
    encoded_content = base64.b64encode(content).decode()

    # Dados para enviar
    data = {
        "message": commit_message,
        "content": encoded_content,
    }

    if sha:
        data["sha"] = sha  # Incluir o sha para atualizar o arquivo existente

    # Enviar a solicitação PUT para criar ou atualizar o arquivo
    response = requests.put(url, json=data, headers=headers)

    # Verificar a resposta
    if response.status_code == 201:
        print(f"Arquivo {file_path} enviado com sucesso para o GitHub!")
    elif response.status_code == 200:
        print(f"Arquivo {file_path} atualizado com sucesso no GitHub!")
    else:
        print(f"Falha ao enviar arquivo: {response.status_code} - {response.text}")


# ------ Função para gerar nome único de arquivo
def generate_unique_filename():
    # Buscar arquivos no repositório para determinar o número de arquivos existentes
    url = f'https://api.github.com/repos/{REPO_NAME}/contents/'
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        files = response.json()
        # Filtrar arquivos que começam com 'recording_' e terminar com '.wav'
        recordings = [file for file in files if file['name'].startswith('recording_') and file['name'].endswith('.wav')]
        # Encontrar o número máximo de gravações e gerar o próximo número
        if recordings:
            existing_numbers = [int(file['name'].split('_')[1].split('.')[0]) for file in recordings]
            next_number = max(existing_numbers) + 1
        else:
            next_number = 1  # Caso não haja arquivos gravados ainda
    else:
        print(f"Erro ao acessar o repositório: {response.status_code} - {response.text}")
        next_number = 1  # Caso ocorra erro, começamos com 1

    # Gerar o nome do arquivo com base no número incremental
    return f"recording_{next_number}.wav"


# ------ MQTT Client Setup
client = mqtt.Client(CLIENT_ID)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883, 60)

# Start MQTT loop
client.loop_start()
