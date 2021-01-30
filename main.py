import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, \
    QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore
from PyQt5 import QtWidgets
import pyqtgraph as pg
# import numpy as np
# pyqt 5.11.3

import RPi.GPIO as gpio

gpio.setmode(gpio.BCM)
from hx711 import HX711
from motor_driver import motor_driver

# set up the load cell
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.reset()
hx.tare()


# L = np.zeros(1)
# import force_read as f_r

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Alarge Coefficient of Friction Tester'
        self.left = 0
        self.top = 0
        self.width = 800
        self.height = 480
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()


class MyTableWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        self.test_time = [0]
        self.test_data = [0]
        self.filter_counter = 0
        self.filter_storage = 0
        self.filtered_value = 0
        self.tick = 0

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab1, "Main Menu")
        self.tabs.addTab(self.tab2, "Test")
        self.tabs.addTab(self.tab3, "Results")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self)
        self.pushButton1 = QPushButton("PyQt5 button")
        self.tab1.layout.addWidget(self.pushButton1)
        self.tab1.setLayout(self.tab1.layout)

        # Create second tab
        self.tab2.layout = QVBoxLayout(self)
        self.pushButtonStart = QPushButton("Start the test")
        self.pushButtonStop = QPushButton("Stop the test")
        self.pushButtonWeight = QPushButton("Weight")



        # Set Plotter
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.graphicsView = pg.PlotWidget(title="Coefficient of Friction Test")
        self.tab2.layout.addWidget(self.pushButtonStart)
        self.tab2.layout.addWidget(self.pushButtonStop)
        self.tab2.layout.addWidget(self.pushButtonWeight)

        self.tab2.setLayout(self.tab2.layout)
        self.tab2.layout.addWidget(self.graphicsView)
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphicsView.plot(self.test_time, self.test_data, pen=pen)
        # button events
        self.pushButtonStart.clicked.connect(self.start_test)  # plot when clicked
        self.pushButtonStop.clicked.connect(self.stop_test)  # tare when clicked
        self.pushButtonWeight.clicked.connect(self.btn_weight)  # weight when clicked

        self.md = motor_driver()
        # timer set and update plot
        # integrate motor driving with QTtimer
        # motor driver can already calculate wait time and tick count

    def start_test(self):
        print("test basladi")
        hx.tare()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        # md = motor_driver.motor_driver()
        # md.enable_motor()
        # md.run_standard_test()

        # md.motor_run(0.01, 400, 1)
        drive_time, frequency, direction = self.md.calculate_ticks()
        self.md.motor_run(3, 100, direction)
        print("motor driver kodundan cikildi")
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def cof_test(self, ttime=0.01, ticks=400, direction=1):
        # counts down ticks
        if self.tick == 0:
            self.tick = ticks

        self.md.send_tick(ttime, direction)

        self.tick = self.tick - 1

        print(self.tick)

        if self.tick < 1:
            self.tick = 0

        self.update_plot()

        if self.tick == 0:
            self.stop_test()

    def filter_force(self):
        # hx711 library already does that :(
        # we need a better method for it and that will happen after an inspection of hx711 library
        # take every 5 calculation and calculate mean then print to plot
        val = hx.get_weight(1)
        self.filter_storage = self.filter_storage + val
        if (self.filter_counter % 5) == 0:
            self.filtered_value = self.filter_storage / 5
            self.filter_storage = 0
            self.update_plot(self.filtered_value)
            self.filter_counter = 0

    def stop_test(self):
        self.timer.stop()
        # motor_driver.motor_driver.disable_motor()

    def btn_tare(self):
        hx.tare()

    def btn_weight(self):
        val = hx.get_weight(5)

        print(val)

    def update_plot(self):
        val = hx.get_weight(5)
        # print(val)
        self.test_data.append(val)
        self.test_time.append(self.test_time[-1] + 0.05)
        self.data_line.setData(self.test_time, self.test_data)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

    """
            # Add plot to second tab
            self.graphicsView = pg.PlotWidget()
            self.tab2.layout = QVBoxLayout(self)
            self.graphicsView.setObjectName("graphicsView")
            self.tab2.layout.addWidget(self.graphicsView)
            self.pushButtonStart = QPushButton("Plot that shit")

            self.pushButtonStart.clicked.connect(self.btn_clk)
    """

    """
        def btn_clk(self):
            val = hx.get_weight(5)
            np.append(L, val)

            self.graphicsView.plot(L, pen=pg.mkPen('r', width=3))  # this line plots red
    """
