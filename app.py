# coding:utf-8

import sys
import io
import os

sys.dont_write_bytecode = True
from route import app, socketio


from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

from gevent import monkey
monkey.patch_all()

try:
    if __name__ == "__main__":

        PORT = 7200
        if os.path.exists('data/port.pl'):
            f = open('data/port.pl')
            PORT = int(f.read())
            f.close()

        # HOST = '0.0.0.0'
        # app.run(host=HOST, port=PORT)

        http_server = WSGIServer(
            (HOST, PORT), app, handler_class=WebSocketHandler)
        http_server.serve_forever()
        socketio.run(app, host=HOST, port=PORT)
except Exception as ex:
    print(ex)
