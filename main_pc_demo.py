
# import os
from PyQt5.QtWidgets import *
# from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore
from PyQt5 import QtGui
import pyqtgraph as pg
from PyQt5.uic import loadUi
import datetime
from motor_driver_pc import motor_driver_pc

#from fpdf import FPDF
from fpdf_handler import fpdf_handler
from random import random

class sample:
    name = ""
    width = 0
    height = 0
    age = 0

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

        self.sample1 = sample()
        self.sample2 = sample()

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
        self.pushButtonTestScreen.clicked.connect(self.test_screen) # go to test screen
        self.pushButtonStart.clicked.connect(self.start_test)  # plot when clicked
        self.pushButtonStop.clicked.connect(self.stop_test)  # tare when clicked
        self.pushButtonWeight.clicked.connect(self.btn_weight)  # weight when clicked
        self.pushButtonAngle_30.clicked.connect(self.set_angle)  # set angle when clicked
        self.pushButtonResults.clicked.connect(self.results_tab)  # go to results tab and calculate results
        self.pushButtonTests.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
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

    def show_imu(self):
        print("imu shown!")
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

"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        date_today = datetime.datetime.today()
        date = date_today.strftime("%Y:%m:%d")
        time = date_today.strftime("%H:%M:%S")
        date_and_time = date_today.strftime("%Y:%m:%d--%H:%M:%S")

        pdf.cell(200, 10, txt="Deneme!", ln=1, align="C")
        pdf.cell(10, 10, txt=date_and_time, ln=1, align="L")
        pdf.cell(200, 50, txt=time, ln=1, align="L")
        pdf.output("COF Test " + date_and_time +".pdf")
"""