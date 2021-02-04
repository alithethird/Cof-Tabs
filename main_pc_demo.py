
# import os
from PyQt5.QtWidgets import *
# from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore
from PyQt5 import QtGui
import pyqtgraph as pg
from PyQt5.uic import loadUi

from motor_driver_pc import motor_driver_pc

from random import random

class App(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        loadUi("cof.ui", self)
        self.setWindowTitle("PyQt5 & Matplotlib Example GUI")

        self.test_time = [0]
        self.test_data = [0]
        self.filter_counter = 0
        self.filter_storage = 0
        self.filtered_value = 0
        self.tick = 0

        # go to test screen
        self.pushButton1.clicked.connect(lambda: self.tabs.setCurrentIndex(1))

        self.Alarge_logo() # Show Alarge logo

        self.tabs.tabBar().hide() # hide tab bar

        self.button_events()

        self.set_plotter()

        self.md = motor_driver_pc()


    def Alarge_logo(self):
        # Show Alarge logo
        pixmap = QtGui.QPixmap('mini_logo.png')
        self.logo.setPixmap(pixmap)
        self.logo.resize(pixmap.width(), pixmap.height())
        self.logo.move(180, 0)

    def button_events(self):
        self.pushButton1.clicked.connect(lambda: self.tabs.setCurrentIndex(1))  # go to test screen when clicked
        self.pushButtonStart.clicked.connect(self.start_test)  # plot when clicked
        self.pushButtonStop.clicked.connect(self.stop_test)  # tare when clicked
        self.pushButtonWeight.clicked.connect(self.btn_weight)  # weight when clicked
        self.pushButtonAngle.clicked.connect(self.set_angle)  # set angle when clicked
        self.pushButtonResults.clicked.connect(lambda: self.tabs.setCurrentIndex(2))  # go to results tab and calculate results
        self.pushButtonTests.clicked.connect(lambda: self.tabs.setCurrentIndex(1))

    def set_plotter(self):

        # Set Plotter
        self.graphWidget.setBackground('w')
        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphWidget.plot(self.test_time, self.test_data, pen=pen)


    def start_test(self):
        print("test basladi")


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




    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


app = QApplication([])
window = App()
window.show()
app.exec_()