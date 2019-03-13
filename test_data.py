import time
import socket
import json
import random


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
                'alpha': random.random(),
                'bravo': random.random(),
                'charlie': random.random() < 0.001,
                'delta': random.random(),
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
