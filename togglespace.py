#!/usr/bin/python3
import requests
import RPi.GPIO as GPIO
import time
import socket
import threading
import os
import sys

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(7, GPIO.OUT)

data = ""
listen_IP = ""
listen_port = ""

showState = ''
openSpace = ''
closeSpace = ''
with open("/home/pi/spaceOpenCloseButton/token.conf", "r") as token_raw:
    space, token, url_tmp = "", "", ""
    for line in token_raw.readlines():
        # Ist kein Kommentar
        if not line.startswith('#'):
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

    showState = url_tmp + 'space=' + space + '&state=show'
    openSpace = url_tmp + 'space=' + space + '&token=' + token + '&state=open'
    closeSpace = url_tmp + 'space=' + space + '&token=' + token + '&state=closed'

def rec_UDP():
    global data, listen_IP, listen_port
    while True:
        # UDP commands for listening
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((listen_IP, listen_port))
        data, addr = sock.recvfrom(1024)
        print("received message:", data)

def do_server_query(action):
    jsoncontent = requests.get(action).json()
    return jsoncontent["status"]

def update_led_status_open():
    print("led status is open")
    GPIO.output(11, 0)
    GPIO.output(7, 1)

def update_led_status_close():
    print("led status is closed")
    GPIO.output(7, 0)
    GPIO.output(11, 1)

def update_space_status(server_status):
    if server_status == "open":
        update_led_status_open()
    elif server_status == "closed":
        update_led_status_close()
    os.system("{}/on_update_space_status.sh {}".format(os.path.dirname(sys.argv[0]), server_status))

def togglespace():
    server_status = do_server_query(showState)
    if server_status == "open":
        print("space is now:", do_server_query(closeSpace))
    elif server_status == "closed":
        print("space is now:", do_server_query(openSpace))
    # get the new status
    server_status = do_server_query(showState)
    update_space_status(server_status)

try:
    # get current state as initial state from server
    update_space_status(do_server_query(showState))

    listen_UDP = threading.Thread(target=rec_UDP)
    listen_UDP.start()
    print("Schleife start")
    loop_counter = 0
    while True:
        time.sleep(0.1)
        loop_counter += 1
        if loop_counter >= 50:
            # pull state every 5sec
            loop_counter = 0
            update_space_status(do_server_query(showState))
        if GPIO.input(15) == GPIO.LOW:
            togglespace()
            time.sleep(0.5)
        if "change" in str(data):
            update_space_status(do_server_query(showState))
        data = ""
except KeyboardInterrupt:
    print("\nExiting ...\n")
    GPIO.output(11,0)
    GPIO.output(7,0)
    os._exit(0)
