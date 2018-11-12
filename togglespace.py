#!/usr/bin/python3
import json
from urllib.request import urlopen
import RPi.GPIO as GPIO
import time
import socket
import threading
import os

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(7, GPIO.OUT)

data = ""
listen_IP = ""
listen_port = ""

url = ["Status Anzeigen", "Space oeffnen", "Space schliessen"]
with open("/home/pi/spaceOpenCloseButton/token.conf", "r") as token_raw:
    space, token, url_tmp = "","",""
    for line in token_raw.readlines():
        if line[0] == '#':
            pass # Ist ein Kommentar
        else:
            line = line.replace('\n', '')
            key, value = line.split('=')
            if key == 'space':
                space = value
            elif key == 'token':
                token = value
            elif key == 'url':
                url_tmp = value
            elif key == 'listen_IP':
                listen_IP = value
            elif key == 'listen_port':
                listen_port = int(value)
            else:
                pass
    url = [url_tmp + 'space=' + space + '&state=show', url_tmp + 'space=' + space + '&token=' + token + '&state=open', url_tmp + 'space=' + space + '&token=' + token + '&state=closed']

def rec_UDP():
    global data, listen_IP, listen_port
    while True:
        # UDP commands for listening
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((listen_IP, listen_port))
        data, addr = sock.recvfrom(1024)
        print("received message:", data)

def do_server_query(action):
    jsonurl = urlopen(url[action])
    jsoncontent = json.loads(bytes.decode(jsonurl.read()))
    return jsoncontent["status"]

def update_led_status_open():
    print("led status is open")
    GPIO.output(11, 0)
    GPIO.output(7, 1)

def update_led_status_close():
    print("led status is closed")
    GPIO.output(7, 0)
    GPIO.output(11, 1)

def update_led_status(server_status):
    if server_status == "open":
        update_led_status_open()
    elif server_status == "closed":
        update_led_status_close()

def togglespace():
    server_status = do_server_query(0)
    if server_status == "open":
        print("space is now:", do_server_query(2))
    elif server_status == "closed":
        print("space is now:", do_server_query(1))
    # get the new status
    server_status = do_server_query(0)
    update_led_status(server_status)

try:
    # get current state as initial state from server
    update_led_status(do_server_query(0))

    listen_UDP = threading.Thread(target=rec_UDP)
    listen_UDP.start()
    print("Schleife start")
    while True:
        time.sleep(0.1)
        if GPIO.input(15) == GPIO.LOW:
            togglespace()
            time.sleep(0.5)
        if "change" in str(data):
            update_led_status(do_server_query(0))
        data=""
except KeyboardInterrupt:
    print("\nExiting ...\n")
    GPIO.output(11,0)
    GPIO.output(7,0)
    os._exit(0)
