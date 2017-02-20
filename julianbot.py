import cv2
import numpy as np

image = cv2.imread('julian2.jpg', flags=cv2.IMREAD_UNCHANGED)
julianface = cv2.imread('julianface.png', flags=cv2.IMREAD_UNCHANGED)

classifier = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

faces = classifier.detectMultiScale(
    grayscale,
    scaleFactor=1.1,
    minNeighbors=10,
    minSize=(30, 30),
    flags=cv2.CASCADE_SCALE_IMAGE
)

factor = 2.0

for (x, y, w, h) in faces:
    x -= (factor - 1.0) / 2 * w
    y -= (factor - 1.0) / 2 * h
    w *= factor
    h *= factor
    x, y, w, h = int(x), int(y), int(w), int(h)
    try:
        insert = cv2.resize(julianface, (w, h))
        for i in range(w):
            for j in range(h):
                image[y + i, x + j] = \
                    image[y + i, x + j] * ((255 - insert[i, j, 3]) / 255) + \
                    insert[i, j][:3] * (insert[i, j, 3] / 255)

                # image[x + i, y + j] * \
                #   (255 - insert[i, j, 3]) / 255 + \
                #   insert[i, j][:3] * insert[i, j, 3] / 255
    except Exception as e:
        print(e)

#cv2.imshow("Faces found", image)
# cv2.waitKey(0)
cv2.imwrite('out.jpg', image)
