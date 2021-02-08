import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore
from PyQt5 import QtGui
import pyqtgraph as pg
from PyQt5.uic import loadUi

import RPi.GPIO as gpio

import datetime
from fpdf_handler import fpdf_handler

class sample:
    name = ""
    width = 0
    height = 0
    age = 0

import angle_read

gpio.setmode(gpio.BCM)
from hx711 import HX711
from motor_driver import motor_driver

# set up the load cell
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.reset()
hx.tare()

class App(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        loadUi("cof.ui", self)
        self.setWindowTitle("Alarge Coefficient of Friction Tester")

        self.test_time = [0]
        self.test_data = [0]
        self.filter_counter = 0
        self.filter_storage = 0
        self.filtered_value = 0
        self.tick = 0

        self.sample1 = sample()
        self.sample2 = sample()

        self.Alarge_logo() # Show Alarge logo

        self.tabs.tabBar().hide() # hide tab bar

        self.button_events()

        self.set_plotter()

        self.md = motor_driver()

    def Alarge_logo(self):
        # Show Alarge logo
        pixmap = QtGui.QPixmap('mini_logo.png')
        self.logo.setPixmap(pixmap)
        self.logo.resize(pixmap.width(), pixmap.height())
        self.logo.move(180, 0)

    def button_events(self):
        self.pushButtonTestScreen.clicked.connect(self.test_screen)  # go to test screen
        self.pushButtonStart.clicked.connect(self.start_test)  # plot when clicked
        self.pushButtonStop.clicked.connect(self.stop_test)  # tare when clicked
        self.pushButtonWeight.clicked.connect(self.btn_weight)  # weight when clicked
        self.pushButtonAngle_30.clicked.connect(self.set_angle_30)  # set angle to 30 when clicked
        self.pushButtonResults.clicked.connect(lambda: self.tabs.setCurrentIndex(2))  # go to results tab and calculate results
        self.pushButtonTests.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.pushButtonAngle_0.clicked.connect(self.set_angle_0)  # set angle to 0 when clicked
        self.pushButtonCreatePDF.clicked.connect(self.createPDF)
        self.pushButtonMain.clicked.connect(lambda: self.tabs.setCurrentIndex(0))

    def set_plotter(self):

        # Set Plotter
        self.graphWidget.setBackground('w')
        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphWidget.plot(self.test_time, self.test_data, pen=pen)

    def test_screen(self):
        # set the sample name
        self.sample1.name = self.sampleName1.text()
        self.sample1.width = self.sampleWidth1.text()
        self.sample1.height = self.sampleHeight1.text()
        self.sample1.age = self.sampleAge1.text()
        # if second sample checkbox is checked and properties are filled
        if not self.is_second_sample_properties_empty() and self.checkBoxDiff.isChecked():
            self.sample2.name = self.sampleName2.text()
            self.sample2.width = self.sampleWidth2.text()
            self.sample2.height = self.sampleHeigth2.text()
            self.sample2.age = self.sampleAge2.text()
            self.tabs.setCurrentIndex(1)  # go to test screen
        elif  self.is_second_sample_properties_empty() and self.checkBoxDiff.isChecked():
            self.labelSecondSampleError.setText("You need to enter Second sample properties!")
            pass
        elif  not self.is_second_sample_properties_empty() and not self.checkBoxDiff.isChecked():
            self.labelSecondSampleError.setText("You need check the checkbox to test against different sample!")
            pass
        elif self.is_second_sample_properties_empty() and not self.checkBoxDiff.isChecked():
            self.tabs.setCurrentIndex(1)  # go to test screen

    def is_second_sample_properties_empty(self):
        if self.sampleName2.text() == "" or self.sampleWidth2.text() == 0 or self.sampleHeigth2.text() == 0 or self.sampleAge2.text() == 0:
            return True
        else:
            return False

    def update_angle_labels(self):
        val = round(angle_read.get_rotation(1), 2)
        self.AngleValue.setText(str(val))

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
        self.md.motor_run(drive_time, frequency, direction)
        print("motor driver kodundan cikildi")
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def stop_test(self):
        self.timer.stop()
        self.md.stop_motor()
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

    def set_angle_30(self):

        while self.check_angle_30:
            self.update_angle_labels()
            val = round(angle_read.get_rotation(1), 2)
            self.AngleValue.setText(str(val))
            if val <= 28:
                freq = (30 - val)*20
                self.md.start_angle_motor_rise(freq)
            else:
                self.md.stop_angle_motor()
        print("Angle is set!")

    def set_angle_0(self):

        while self.check_angle_0:
            self.update_angle_labels()
            val = round(angle_read.get_rotation(1), 2)
            self.AngleValue.setText(str(val))
            if val >= 2:
                freq = val*20
                self.md.start_angle_motor_fall(freq)
            else:
                self.md.stop_angle_motor()
        print("Angle is set!")
    def check_angle_30(self):
        val = angle_read.get_rotation(1)
        self.AngleValue.setText(val)
        if val >= 28 and val <= 32:
            return False
        else:
            return True

    def check_angle_0(self):
        val = angle_read.get_rotation(1)
        self.AngleValue.setText(val)
        if val <= 2:
            return False
        else:
            return True

    def results_tab(self):
        self.tabs.setCurrentIndex(2)
        self.create_results()

    def create_results(self):
        date_today = datetime.date.today()
        self.label_date.setText(str(date_today))

        dynamic_cof = self.find_dynamic_cof()
        static_cof = self.find_static_cof()

        self.label_static_cof_result.setText(str(static_cof))
        self.label_dynamic_cof_result.setText(str(dynamic_cof))

    def find_dynamic_cof(self):
        dynamic_cof = 1
        return dynamic_cof

    def find_static_cof(self):
        static_cof = 2
        return static_cof

    def createPDF(self):
        self.pdf = fpdf_handler()
        self.pdf.create_pdf(1, 2, self.sample1, self.sample2)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())



app = QApplication([])
window = App()
window.show()
app.exec_()