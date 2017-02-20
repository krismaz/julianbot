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


sc = SlackClient(token)
if sc.rtm_connect():
    while True:
        messages = sc.rtm_read()
        for message in messages:
            try:
                if message['type'] == 'file_comment_added' and message['comment']['comment'] == '<@U47T0LMB7>' :
                    info = sc.api_call('files.info', file = message['file_id'])['file']
                    url = info['url_private']
                    get = requests.get(url, headers={'Authorization': 'Bearer {}'.format(token)})
                    file = url.split('/')[-1]
                    with open(file, 'wb') as f:
                        f.write(get.content)
                    image = cv2.imread(file, flags=cv2.IMREAD_UNCHANGED)
                    julianize(image)
                    cv2.imwrite(file+'.out.jpg', image)
                    sc.api_call('files.upload', channels=info['channels'][0], filename='julian' + file, file=open('out.jpg', 'rb'))
            except Exception as e:
                print(e)
        time.sleep(1)
else:
    print("Connection Failed, invalid token?")

