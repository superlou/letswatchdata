import time
import socket
import json
import random
import numpy as np


def send_data(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        print('Connected')

        t = 0
        dt = 0.01

        while 1:
            t += dt
            data = {
                't': t,
                'alpha': np.sin(2 * np.pi * 0.14 * t),
                'bravo': np.sin(2 * np.pi * 0.14 * t) + random.random() / 10.0,
                'charlie': random.random() < 0.0002,
                'delta': random.random(),
                'echo': np.sin(2 * np.pi * 0.2 * t),
                'noise1': random.random(),
                'noise2': random.random(),
                'noise3': random.random(),
                'noise4': random.random(),
                'noise5': random.random(),
                'noise6': random.random(),
                'noise7': random.random(),
                'noise8': random.random(),
                'noise9': random.random(),
                'noise10': random.random(),
                'noise11': random.random(),
                'noise12': random.random(),
            }

            b = json.dumps(data) + '\n'
            sock.sendall(b.encode('utf-8'))

            time.sleep(dt)


if __name__ == '__main__':
    host, port = '127.0.0.1', 65432

    while True:
        try:
            send_data(host, port)
        except:
            print('Unable to connect')
            time.sleep(1)
            pass
