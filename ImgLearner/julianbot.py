import cv2
import numpy as np
from os import listdir
from os.path import join
import random
from slackclient import SlackClient
from config import token
import json
import requests
import time
import learner


def julianize(image):
    julianfaces = [cv2.imread(join('julians', julian), flags=cv2.IMREAD_UNCHANGED)
                   for julian in listdir('julians')]

    classifier = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = classifier.detectMultiScale(
        grayscale,
        scaleFactor=1.1,
        minNeighbors=10,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    factor = 1.8

    for (x, y, w, h) in sorted(faces, key=lambda x: x[2] * x[3]):
        julianface = random.choice(julianfaces)
        if random.choice([True, False]):
            julianface = cv2.flip(julianface, 1)
        x -= (factor - 1.0) / 2 * w
        y -= (factor - 1.0) / 2 * h
        w *= factor
        h *= factor
        x, y, w, h = int(x), int(y), int(w), int(h)
        try:
            insert = cv2.resize(julianface, (w, h))
            for i in range(w):
                for j in range(h):
                    if(image.shape[2]) == 3:
                        image[y + i, x + j] = \
                            image[y + i, x + j] * ((255 - insert[i, j, 3]) / 255) + \
                            insert[i, j][:3] * (insert[i, j, 3] / 255)
                    else:
                        image[y + i, x + j] = \
                            image[y + i, x + j] * ((255 - insert[i, j, 3]) / 255) + \
                            insert[i, j] * (insert[i, j, 3] / 255)
        except Exception as e:
            print(e)

files = dict()

def getFile(message):
    url = files[message['thread_ts']]
    get = requests.get(
        url, headers={'Authorization': 'Bearer {}'.format(token)})
    file = url.split('/')[-1]
    with open(file, 'wb') as f:
        f.write(get.content)
    return file

sc = SlackClient(token)
if sc.rtm_connect():
    seen = set()
    while True:
        messages = sc.rtm_read()
        for message in messages:
            print("\n================================================")
            print(message)
            print(files)
            try:
                if message['type'] == 'message':
                    if message['ts'] in seen or 'text' not in message:
                        print("SSSSSEEEEEEEEEEEEEEEEENNNN")
                        continue
                    seen.add(message['ts'])
                    if 'files' in message:
                        files[message['ts']] = message['files'][0]['url_private_download']

                    text = message['text']
                    if not text.startswith('<@U47T0LMB7>'):
                        print("NOT FOR ME")
                        continue
                    command = text.lower().split()[1:]
                    if 'thread_ts' not in message:
                        message['thread_ts'] = message['ts']

                    if command[0] == 'learn':
                        learner.handle(' '.join(('register' , command[1], message['ts'], getFile(message))))
                        print("!!GOOOD!!!")
                        sc.api_call('chat.postMessage', channel=message['channel'], text="TARGET " +  command[1] + " AQUIRED" )
                    elif command[0] == 'guess':
                        file = getFile(message)
                        learner.handle(' '.join(('annotate', file, file + ".out.jpg")))
                        sc.api_call('files.upload', channels=message['channel'], filename='julian' + file, file=open(file + '.out.jpg', 'rb'))
                    elif command[0].startswith('assemble'):
                        print("AAAAAAASEEEEEEMMBLE!")
                        sc.api_call('chat.postMessage', channel=message['channel'], text="JULIANBOT ONLINE!")


            except Exception as e:
                print(e)
        time.sleep(1)
else:
    print("Connection Failed, invalid token?")
