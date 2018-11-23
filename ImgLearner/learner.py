import sqlite3
import face_recognition
import cv2
import base64
import numpy as np
import json
import traceback

conn = sqlite3.connect('example.db')

c = conn.cursor()

c.execute('''
        CREATE TABLE IF NOT EXISTS signatures
             (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             person_id TEXT NOT NULL,
             image_id TEXT NOT NULL,
             signature TEXT NOT NULL,
             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
             modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);''')
conn.commit()


c.execute('''SELECT signature, person_id, image_id FROM signatures;''')


sigs = [(np.frombuffer(base64.decodestring(sig.encode('ascii')),dtype=np.float64), person, image) for sig, person, image in c.fetchall()];

print('Fetched', len(sigs), 'signatures')

def shrink(image):
    h, w = image.shape[:2]
    f = min(1000/h, 1000/w, 1.0)
    return cv2.resize(image, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)

def register(person, image, path):
    image_loaded = shrink(face_recognition.load_image_file(path))
    face_locations = face_recognition.face_locations(image_loaded, 0, model='cnn')
    encoding = face_recognition.face_encodings(image_loaded, face_locations)[0]
    b64 = base64.b64encode(encoding).decode('ascii')
    c.execute('''
                UPDATE signatures SET signature = "{0}", modified_at = CURRENT_TIMESTAMP WHERE person_id = "{1}" AND image_id = "{2}";'''
                    .format(b64, person, image))
    c.execute('''
                INSERT INTO signatures (signature, person_id, image_id) SELECT "{0}", "{1}", "{2}" WHERE changes() = 0;'''
                    .format(b64, person, image))
    sigs.append((encoding, person, image))
    conn.commit()
    return (person, image, b64)


def remove(person, image):
    c.execute('''DELETE FROM signatures WHERE person_id LIKE "{0}" AND image_id LIKE "{1}";'''.format(person, image))
    conn.commit()
    return c.execute('''SELECT changes();''').fetchall()[0][0]


def analyse(path):
    results = []
    image = shrink(cv2.imread(path))
    face_locations = face_recognition.face_locations(image, 0, model='cnn')
    face_encodings = face_recognition.face_encodings(image, face_locations)
    for location, face_encoding in zip(face_locations, face_encodings):
        # See if the face is a match for the known face(s)
        matches = list(
                    zip(
                        (np.linalg.norm([e for e, _, __ in sigs] - face_encoding, axis=1) ),
                        ((n, p) for _, n, p in sigs)))
        results.append({
                "position": location,
                "matches": list(sorted(matches))[:3]
            })
    return results



def annotate(path, out):
    analysis = analyse(path)
    image = shrink(cv2.imread(path))
    for match in analysis:
        top, right, bottom, left = match['position']
        best = match["matches"][0]
        cv2.putText(image, str((1.0 - best[0])*100)[:4] + '% - ' + str(best[1][0]), (left - 40, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 1)
    cv2.imwrite(out, image)
    return analysis

def handle(line):
    command = line.split()
    if command[0] == 'register':
        return ''.join(register(*command[1:]))
    elif command[0] == 'remove':
        print(remove(*command[1:]))
    elif command[0] == 'analyse':
        print(json.dumps(analyse(*command[1:])))
    elif command[0] == 'annotate':
        print(json.dumps(annotate(*command[1:])))
    else:
        raise Exception('Unknown command ' + command[0])

def close():
    conn.close()

def main():
    while True:
        try:
           handle(input())
        except EOFError:
            break
        except Exception:
            traceback.print_exc()
    close()

if __name__ == '__main__':
    main()

