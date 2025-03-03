#!/bin/bash


sudo apt update && sudo apt upgrade -y


sudo apt install -y python3 python3-pip python3-venv build-essential libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools


python3 -m venv venv
source venv/bin/activate


pip install --upgrade pip
pip install streamlit paho-mqtt numpy streamlit-autorefresh sounddevice


if [ $? -eq 0 ]; then
    echo "Instalação concluída com sucesso!"
else
    echo "Ocorreu um erro durante a instalação. Verifique os logs acima."
    exit 1
fi


echo "Ambiente configurado. Para ativar o ambiente virtual novamente no futuro, execute:"
echo "source venv/bin/activate"
