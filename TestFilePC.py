# To start mosquitto now and restart at login:
#   brew services start mosquitto
# Or, if you don't want/need a background service you can just run:
#   /opt/homebrew/opt/mosquitto/sbin/mosquitto -c /opt/homebrew/etc/mosquitto/mosquitto.conf
# Test file - pc file

import sounddevice as sd #para gravar som

# ----- gravação de som ---------------
sd.default.samplerate = 100
sd.default.channels = 0
fs = 20 #i guess the ideia is for the mqtt broker to send the fs
#perhaps we can use a default one in case none is provided
duration = 10.5  #s 
record = sd.rec(int(duration * fs), dtype='float64')