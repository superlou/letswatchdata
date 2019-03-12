import numpy as np
import socket
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
from pyqtgraph.dockarea import *
import json
from queue import Queue
import threading
import time
from annotator import Annotator


def socket_listener(host, port, rx_queue):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, port))
        sock.listen()
        print('Waiting for connection on {}:{}...'.format(host, port))
        conn, addr = sock.accept()

        with conn:
            print('Connected to {}'.format(addr))

            while True:
                data = conn.recv(1024).strip()
                tokens = data.split(b'\n')

                for token in tokens:
                    try:
                        str = token.decode('utf-8')
                        msg = json.loads(str)
                        rx_queue.put(msg)
                    except json.decoder.JSONDecodeError:
                        print('Error decoding json: {}'.format(str))

                time.sleep(0.01)


class ParamManager:
    def __init__(self, dock_area, params_tree, config):
        self.dock_area = dock_area
        self.params = {}    # [Param, Plot, Curve, QTreeWidgetItem]
        self.params_tree = params_tree
        self.last_dock_added = None
        self.xlink = None
        self.annotators = {a['param']: Annotator(a['param'], a)
                            for a in config.get('annotators', [])}

    def update(self, param_name, time, value):
        try:
            param = self.params[param_name]
        except KeyError:
            param = self.create_param(param_name, value)

        # Update parameter history
        param[0].update(time, value)

        # Update parameter curve
        if param[2]:
            param[2].setData(param[0].t_series, param[0].v_series)

        # Update value in parameter tree
        param[3].setData(1, QtCore.Qt.DisplayRole, value)

        # Add arrows if annotation event occurs
        if param_name in self.annotators:
            annotator = self.annotators[param_name]
            if annotator.matches(param[0]):
                for p in [p for n, p in self.params.items() if p[1]]:
                    param, plot, curve, item = p
                    arrow = pg.ArrowItem()
                    arrow.setPos(time, param.v_series[-1])
                    plot.addItem(arrow)

    def create_param(self, param_name, value):
        if isinstance(value, (int, float)):
            dock = Dock(param_name, closable=True)

            if self.last_dock_added:
                self.dock_area.addDock(dock, 'bottom', self.last_dock_added)
            else:
                self.dock_area.addDock(dock, 'right')

            self.last_dock_added = dock

            plot = pg.PlotWidget(title=param_name)
            plot.setXLink(self.xlink)

            if self.xlink is None:
                self.xlink = plot.getPlotItem()

            dock.addWidget(plot)
            plot.showGrid(True, True, 0.4)

            curve = plot.plot('r', x=[], y=[])
        else:
            plot = None
            curve = None

        param = Param(param_name)
        tree_widget_item = QtGui.QTreeWidgetItem([param_name])
        self.params_tree.addTopLevelItem(tree_widget_item)

        self.params[param_name] = [param, plot, curve, tree_widget_item]
        return self.params[param_name]


class Param:
    def __init__(self, name):
        self.name = name
        self.t_series = []
        self.v_series = []

    def update(self, time, value):
        if isinstance(value, bool):
            value = int(value)

        self.t_series.append(time)
        self.v_series.append(value)


def update_gui(rx_queue, pm):
    while not rx_queue.empty():
        msg = rx_queue.get()

        params = [(msg['t'], k) for k, v in msg.items() if k != 't']

        for param in params:
            pm.update(param[1], param[0], msg[param[1]])


if __name__ == '__main__':
    config = json.load(open('config.json'))
    rx_queue = Queue()

    args = ('127.0.0.1', 65432, rx_queue)
    socket_thread = threading.Thread(target=socket_listener, args=args)
    socket_thread.daemon = True
    socket_thread.start()

    app = QtGui.QApplication([])
    pg.setConfigOptions(antialias=True)

    win = QtGui.QMainWindow()
    win.setWindowTitle('SocketPlot')

    area = DockArea()
    win.setCentralWidget(area)

    params_tree_dock = Dock("Parameters", size=(1,1))
    area.addDock(params_tree_dock)
    params_tree = pg.TreeWidget()
    params_tree.setColumnCount(2)
    params_tree_dock.addWidget(params_tree)

    pm = ParamManager(area, params_tree, config)

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: update_gui(rx_queue, pm))
    timer.start(30)

    win.show()
    app.exec_()
