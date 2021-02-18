from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy_garden.graph import MeshLinePlot
from kivy.clock import Clock

import datetime
from fpdf_handler import fpdf_handler

import RPi.GPIO as gpio
import angle_read
from math import cos

gpio.setmode(gpio.BCM)
from hx711 import HX711
from motor_driver import motor_driver

# set up the load cell

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.reset()
hx.tare()

Builder.load_file('cof.kv')

md = motor_driver()


class sample:
    name = ""
    width = 0
    height = 0
    age = 0


sample1 = sample()
sample2 = sample()

global normal_force # üstte kayan metal malzemenin kütlesi (kg)
normal_force = 0.2
global test_angle
test_angle = 0

global forces
forces = [[0,0]]

sample_time = 0.1


def get_force():
    val = hx.get_weight(5)
    calib = 1  # kalibrasyon sayısı
    val /= calib
    if val < 0:
        val = 1
    forces.append([round((forces[-1][0] + sample_time),4), val])


def find_biggest(array):
    biggest = 0
    for i in array:
        if i > biggest:
            biggest = i
        else:
            pass
    return biggest

def find_dynamic_force(array):
    static = 0
    count = 0
    if len(array) > 10:
        for i in array:
            if static == i:
                count += 1
                if count == 5:
                    return static
            else:
                static = i
    else:
        return 1


class ScreenOne(Screen):

    def btn_text(self):
        sample1.name = self.ids.first_name.text
        sample1.width = self.ids.first_width.text
        sample1.height = self.ids.first_height.text
        sample1.age = self.ids.first_age.text
        if self.ids.switch.active:
            sample2.name = self.ids.second_name.text
            sample2.width = self.ids.second_width.text
            sample2.height = self.ids.second_height.text
            sample2.age = self.ids.second_age.text


class ScreenTwo(Screen):
    plot = MeshLinePlot(color=[1, 0, 0, 1])

    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.force_current_label = Label(text="Current Force: ", markup=True)
        self.force_current_label.pos = (-340, 170)
        self.force_current_label.color = (0,0,0,1)
        self.add_widget(self.force_current_label)

        self.force_text = "0"
        self.force_current = Label(text=self.force_text, markup=True)
        self.force_current.pos = (-240, 170)
        self.force_current.color = (0,0,0,1)
        self.add_widget(self.force_current)

        self.angle_current_label = Label(text="Current Angle: ", markup=True)
        self.angle_current_label.pos = (200, 170)
        self.angle_current_label.color = (0,0,0,1)
        self.add_widget(self.angle_current_label)

        self.angle_text = str(round(angle_read.get_rotation(1), 2))
        self.angle_current = Label(text=self.angle_text, markup=True)
        self.angle_current.pos = (300, 170)
        self.angle_current.color = (0,0,0,1)
        self.add_widget(self.angle_current)

    def start(self):
        forces.clear()
        self.ids.graph.remove_plot(self.plot)
        self.ids.graph.add_plot(self.plot)
        Clock.schedule_interval(self.get_value, sample_time)

        drive_time, frequency, direction = md.calculate_ticks()
        md.motor_run(drive_time, frequency, direction)

    def stop(self):
        Clock.unschedule(self.get_value)
        md.stop_motor()

    def save_graph(self):
        self.ids.graph.export_to_png("graph.png")

    def get_value(self, dt):
        get_force()

        if forces[-1][0] == 0:
            self.ids.graph.xmax = 1
        else:
            self.ids.graph.xmax = forces[-1][0]

        if forces[-1][1] == 0:
            self.ids.graph.ymax = 1
        else:
            self.ids.graph.ymax = find_biggest(forces) * 1.1

        self.ids.graph.y_ticks_major = round(self.ids.graph.ymax)

        self.plot.points = forces
        self.force_current.text = str(round(forces[-1][1],2))

    def show_angle(self, angle):

        angle = "[color=454545]" + str(angle) + "[/color]"
        self.angle_current.text = angle

    def set_angle(self):
        angle = self.ids.angle_text.text
        if angle != "":
            try:
                angle = int(angle)
                while self.check_angle(angle):
                    val = round(angle_read.get_rotation(1), 2)
                    freq = (angle - val) * 20
                    self.show_angle(val)
                    if freq > 0:
                        md.start_angle_motor_rise(freq)
                    else:
                        freq *= -1
                        md.start_angle_motor_fall(freq)
                md.stop_angle_motor()
            except:
                pass
        else:
            pass

    def check_angle(self, angle):
        val = round(angle_read.get_rotation(1), 2)
        self.show_angle(val)
        if val <= angle + 1 and val >= angle - 1:
            return False
        else:
            return True


class ScreenThree(Screen):
    date_today = datetime.date.today()
    date_text = str(date_today)
    date_text = "[color=454545]" + date_text + "[/color]"

    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.static_cof_text = "0"
        self.l_static = Label(text=self.static_cof_text, markup=True)
        self.l_static.pos = (-90, 95)
        self.l_static.pos_hint_x = 0.5
        self.dynamic_cof_text = "0"
        self.l_dynamic = Label(text=self.dynamic_cof_text, markup=True)
        self.l_dynamic.pos = -90, 0

        self.add_widget(self.l_static)
        self.add_widget(self.l_dynamic)


    def create_results(self):
        dynamic_cof = self.find_dynamic_cof()
        static_cof = self.find_static_cof()
        return dynamic_cof, static_cof

    def find_dynamic_cof(self):
        dynamic_force = find_dynamic_force(forces)
        dynamic_cof = dynamic_force / (normal_force * 9.81 * cos(test_angle))
        dynamic_cof = round(dynamic_cof, 3)
        return dynamic_cof

    def find_static_cof(self):
        static_force = find_biggest(forces)
        static_cof = float(static_force) / (normal_force * 9.81 * cos(test_angle))
        static_cof = round(static_cof, 3)
        return static_cof

    def update_results(self):
        self.dynamic, self.static = self.create_results()
        self.static_cof_text = "[color=454545]"+ str(self.static) +"[/color]"
        self.dynamic_cof_text = "[color=454545]"+ str(self.dynamic) +"[/color]"

        self.l_dynamic.text = self.dynamic_cof_text
        self.l_static.text = self.static_cof_text

    def createPDF(self):
        self.pdf = fpdf_handler()
        self.pdf.create_pdf( self.static, self.dynamic, sample1, sample2)


screen_manager = ScreenManager()

screen_manager.add_widget(ScreenOne(name="screen_one"))
screen_manager.add_widget(ScreenTwo(name="screen_two"))
screen_manager.add_widget(ScreenThree(name="screen_three"))


class AwesomeApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        Window.size = (800, 480)  # pencere boyutu
        return screen_manager


if __name__ == "__main__":
    AwesomeApp().run()

