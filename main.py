import numpy as np
import socket
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
from pyqtgraph.dockarea import *
import json
from queue import Queue
import threading
import time
import argparse
from annotator import Annotator
from parameter import Parameter, ParameterDB


def socket_listener(host, port, rx_queue):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, port))
        sock.listen()
        print('Waiting for connection on {}:{}...'.format(host, port))
        conn, addr = sock.accept()

        with conn:
            print('Connected to {}'.format(addr))

            while True:
                data = conn.recv(100000).strip()
                tokens = data.split(b'\n')

                for token in tokens:
                    try:
                        str = token.decode('utf-8')
                        msg = json.loads(str)
                        rx_queue.put(msg)
                    except json.decoder.JSONDecodeError:
                        print('Error decoding json: {}'.format(str))

                time.sleep(0.05)


class ParamManager:
    def __init__(self, dock_area, params_tree, config):
        self.dock_area = dock_area
        self.db = ParameterDB()
        self.curves = {}
        self.qtree_widget_items = {}
        self.plot_widget_items = []
        # self.params = {}    # [Parameter, Plot, Curve, QTreeWidgetItem]
        self.params_tree = params_tree
        self.last_dock_added = None
        self.xlink = None
        self.annotators = {a['param']: Annotator(a['param'], a)
                            for a in config.get('annotators', [])}

        self.auto_pens = [
            pg.mkPen('#f00'),
            pg.mkPen('#0f0'),
            pg.mkPen('#00f'),
            pg.mkPen('#AA0'),
            pg.mkPen('#0AA'),
            pg.mkPen('#A0A'),
        ]

        self.initialize_plots(config)

    def initialize_plots(self, config):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # Create 1 dock for each plot
        for plot in config.get('plots', []):
            dock_name = ', '.join(plot.get('parameters', []))
            dock = Dock(dock_name, closable=False)

            if self.last_dock_added:
                # Position under the previous dock
                self.dock_area.addDock(dock, 'bottom', self.last_dock_added)
            else:
                # Position to the right of the tree
                self.dock_area.addDock(dock, 'right')

            self.last_dock_added = dock

            plot_widget = pg.PlotWidget(title=dock_name)
            plot_widget.showGrid(True, True, 0.4)
            dock.addWidget(plot_widget)
            self.plot_widget_items.append(plot_widget)
            plot_widget.addLegend()

            # Link all plot x-axes to the first plot
            plot_widget.setXLink(self.xlink)
            if self.xlink is None:
                self.xlink = plot_widget.getPlotItem()

            # Create curve for each parameter in a plot
            for i, parameter_name in enumerate(plot.get('parameters', [])):
                curve = plot_widget.plot('r', x=[], y=[], name=parameter_name)
                curve.parent = plot_widget  # todo Hacky
                self.curves[parameter_name] = curve
                curve.setPen(self.auto_pens[i % len(self.auto_pens)])


    def update(self, parameter_name, time, value):
        try:
            parameter = self.db.get(parameter_name)
        except KeyError:
            parameter = self.db.create(parameter_name)

        # Update parameter history
        parameter.update(time, value)

        # Update parameter curve
        if parameter_name in self.curves:
            curve = self.curves[parameter_name]
            curve.setData(parameter.t_series, parameter.v_series)
            curve.parameter = parameter     # todo This is hacky

        # Update value in parameter tree
        if not parameter_name in self.qtree_widget_items:
            item = QtGui.QTreeWidgetItem([parameter_name])
            self.params_tree.addTopLevelItem(item)
            self.qtree_widget_items[parameter_name] = item

        item = self.qtree_widget_items[parameter_name]
        item.setData(1, QtCore.Qt.DisplayRole, value)

        # Add arrows if annotation event occurs
        # todo This is slow and hacky
        if parameter_name in self.annotators:
            annotator = self.annotators[parameter_name]
            if annotator.matches(parameter):
                for parameter_name, curve in self.curves.items():
                    parameter = self.db.get(parameter_name)
                    arrow = pg.ArrowItem()
                    arrow.setPos(time, parameter.v_series[-1])
                    curve.parent.addItem(arrow)


def update_gui(rx_queue, pm):
    while not rx_queue.empty():
        msg = rx_queue.get()

        params = [(msg['t'], k) for k, v in msg.items() if k != 't']

        for param in params:
            pm.update(param[1], param[0], msg[param[1]])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help="Configuration JSON file")
    args = parser.parse_args()

    try:
        config = json.load(open(args.config))
    except FileNotFoundError:
        print('Unable to open "{}"'.format(args.config))
        return

    rx_queue = Queue()

    args = ('127.0.0.1', 65432, rx_queue)
    socket_thread = threading.Thread(target=socket_listener, args=args)
    socket_thread.daemon = True
    socket_thread.start()

    app = QtGui.QApplication([])
    pg.setConfigOptions(antialias=True)

    win = QtGui.QMainWindow()
    win.setWindowTitle("Let's Watch Data")

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


if __name__ == '__main__':
    main()
