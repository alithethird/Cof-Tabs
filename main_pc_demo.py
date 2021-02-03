import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, \
    QGridLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import pyqtgraph as pg
# import numpy as np
# pyqt 5.11.3
from motor_driver_pc import motor_driver_pc

from random import random
import time

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
        self.tabs.setMovable(True)
        self.tabs.tabBar().hide() # hide tab bar

        # Add tabs
        self.tabs.addTab(self.tab1, "Main Menu")
        self.tabs.addTab(self.tab2, "Test")
        self.tabs.addTab(self.tab3, "Results")

        # Create first tab
        self.tab1.layout = QVBoxLayout(self)
        self.pushButton1 = QPushButton("Test Screen")
        self.tab1.layout.addWidget(self.pushButton1)
#        self.tab1.layout.addStretch(self.logo)
        self.tab1.setLayout(self.tab1.layout)

        # Create second tab
        self.tab2.layout = QVBoxLayout(self)
        self.pushButtonStart = QPushButton("Start the test")
        self.pushButtonStop = QPushButton("Stop the test")
        self.pushButtonWeight = QPushButton("Weight")
        # açı butonu
        self.pushButtonAngle = QPushButton("Set Angle")
        # results butonu
        self.pushButtonResults = QPushButton("Results")
        # Set Plotter
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.graphicsView = pg.PlotWidget(title="Coefficient of Friction Test")
        self.tab2.layout.addWidget(self.pushButtonStart)
        self.tab2.layout.addWidget(self.pushButtonStop)
        self.tab2.layout.addWidget(self.pushButtonWeight)
        self.tab2.layout.addWidget(self.pushButtonAngle)
        self.tab2.layout.addWidget(self.pushButtonResults)

        # Create Third Tab
        self.tab3.layout = QVBoxLayout(self)
        self.tab3.setLayout(self.tab3.layout)
        # go back to test
        self.pushButtonTests = QPushButton("Go back")

        self.tab3.layout.addWidget(self.pushButtonTests)
        self.tab3.setLayout(self.tab3.layout)
        self.tab3.setGeometry(100, 100, 200, 100)
        # Add Label for static cof
        label_name_static_cof = QtWidgets.QLabel(self.tab3)
        # Show name
        label_name_static_cof.setText('Static Coefficient of Friction: ')
        label_name_static_cof.move(0,0)
        label_name_static_cof.resize(400, 100)
        # Show result
        label_static_cof_result = QtWidgets.QLabel(self.tab3)
        label_static_cof_result.setText('0.00')
        label_static_cof_result.move(200, 35)

        # Add Label for dynamic cof
        label_name_dynamic_cof = QtWidgets.QLabel(self.tab3)
        # Show name
        label_name_dynamic_cof.setText('Dynamic Coefficient of Friction: ')
        label_name_dynamic_cof.move(0,30)
        label_name_dynamic_cof.resize(400, 100)
        # Show result
        label_dynamic_cof_result = QtWidgets.QLabel(self.tab3)
        label_dynamic_cof_result.setText('0.00')
        label_dynamic_cof_result.move(220, 65)

        # add logo
        logo = QtWidgets.QLabel(self.tab1)
        pixmap = QtGui.QPixmap('mini_logo.png')
        logo.setPixmap(pixmap)
        logo.resize(pixmap.width(), pixmap.height())
        logo.move(180, 0)

        #logo.move(120,120)
        self.tab2.setLayout(self.tab2.layout)
        self.tab2.layout.addWidget(self.graphicsView)
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphicsView.plot(self.test_time, self.test_data, pen=pen)
        # button events
        self.pushButton1.clicked.connect(lambda : self.tabs.setCurrentIndex(1))  # go to test screen when clicked
        self.pushButtonStart.clicked.connect(self.start_test)  # plot when clicked
        self.pushButtonStop.clicked.connect(self.stop_test)  # tare when clicked
        self.pushButtonWeight.clicked.connect(self.btn_weight)  # weight when clicked
        self.pushButtonAngle.clicked.connect(self.set_angle) # set angle when clicked
        self.pushButtonResults.clicked.connect(self.goto_results_tab) # go to results tab and calculate results
        self.pushButtonTests.clicked.connect(lambda : self.tabs.setCurrentIndex(1))

        self.md = motor_driver_pc()
        # timer set and update plot

    def start_test(self):
        print("test basladi")

        self.labelA.setText('hübele')
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        # md = motor_driver.motor_driver()
        # md.enable_motor()
        # md.run_standard_test()

        # md.motor_run(0.01, 400, 1)
        drive_time, frequency, direction = self.md.calculate_ticks()
        self.md.motor_run(drive_time, frequency, direction)
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
        val = random()
        self.filter_storage = self.filter_storage + val
        if (self.filter_counter % 5) == 0:
            self.filtered_value = self.filter_storage / 5
            self.filter_storage = 0
            self.update_plot(self.filtered_value)
            self.filter_counter = 0

    def stop_test(self):
        self.timer.stop()
        self.md.stop_motor()
        # motor_driver.motor_driver.disable_motor()

    def btn_tare(self):
        print("Tare completed")

    def btn_weight(self):
        val = random()

        print(val)

    def update_plot(self):
        val = random()
        # print(val)
        self.test_data.append(val)
        self.test_time.append(self.test_time[-1] + 0.05)
        self.data_line.setData(self.test_time, self.test_data)

    def set_angle(self):
        x = 2 # x süresi 2 saniye olsun mesela
        self.md.set_angle_x(x)
        # en azından x sn boyunca 30 dereceye ulaşmayacağını biliyoruz
        # bu x saniye boyunca sistem kasmaması için pwm ile sürüyoruz
        # signal timer ile x saniyeye ulaştığımızda interrupt giriyoruz
        # x saniye sonunda açıya bakıp ona göre sürmeye başlıyoruz

    def goto_results_tab(self):
        self.tabs.setCurrentIndex(2)


    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
