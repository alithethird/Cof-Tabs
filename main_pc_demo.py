from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy_garden.graph import MeshLinePlot
from kivy.clock import Clock

import datetime
from random import random

from fpdf_handler import fpdf_handler
from motor_driver_pc import motor_driver_pc

from math import cos
Builder.load_file('cof.kv')

md = motor_driver_pc()
class sample:
    name = ""
    width = 0
    height = 0
    age = 0

global forces
forces = [[0,0]]

sample_time = 0.1

sample1 = sample()
sample2 = sample()

global normal_force # üstte kayan metal malzemenin kütlesi (kg)
normal_force = 0.2
global test_angle
test_angle = 0
def get_force(forces):

    if len(forces) > 1:
        if len(forces) < 100:
            forces.append([round((forces[-1][0] + sample_time),4), (forces[-1][1] + 100)])
        else:
            forces.append([round((forces[-1][0] + sample_time),4), (forces[-1][1] - 100)])
    else:
        forces.append([0,random()])

def find_biggest(array):
    biggest = 1
    for i in array[:][:]:
        if i[1] > biggest:
            biggest = i[1]
        else:
            pass
    return biggest

def find_static_force(array):
    static = 0
    count = 0
    for i in array[:][:]:
        if static == i[1]:
            count += 1
            if count == 5:
                return static
        else:
            static = i[1]

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

    plot = MeshLinePlot(color=[1,0,0,1])
    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.force_current_label = Label(text="Current Force: ")
        self.force_current_label.pos = (-335, 170)
        self.force_current_label.color = (0,0,0,1)
        self.add_widget(self.force_current_label)

        self.force_text = "0"
        self.force_current = Label(text=self.force_text)
        self.force_current.pos = (-225, 170)
        self.force_current.color = (0,0,0,1)
        self.add_widget(self.force_current)

        self.angle_current_label = Label(text="Current Angle: ")
        self.angle_current_label.pos = (200, 170)
        self.angle_current_label.color = (0,0,0,1)
        self.add_widget(self.angle_current_label)

        self.angle_text = str(10)
        self.angle_current = Label(text=self.angle_text)
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
        print("motor driver kodundan cikildi")

    def stop(self):
        Clock.unschedule(self.get_value)
        md.stop_motor()

    def save_graph(self):
        self.ids.graph.export_to_png("graph.png")

    def get_value(self, dt):
        print("gettin value")

        get_force(forces)

        if forces[-1][0] == 0:
            self.ids.graph.xmax = 1
        else:
            self.ids.graph.xmax = forces[-1][0]

        if forces[-1][1] == 0:
            self.ids.graph.ymax = 1
        else:
            self.ids.graph.ymax = find_biggest(forces) * 1.1

        self.ids.graph.y_ticks_major = round(self.ids.graph.ymax)
        """
        if forces[-1]*2 > self.ids.graph.ymax:
            self.ids.graph.ymax = forces[-1] * 2
"""
        self.plot.points = forces
        print( "y: "+ str(forces[-1][1]))
        print( "x: " + str(forces[-1][0]))
        self.force_current.text = str(round(forces[-1][1],2))

    def btn_angle_text(self):
        text = self.ids.angle_text.text
        print(text)

    def show_angle(self, dt):
        angle = 10
        self.angle_current.text = str(angle)
    def set_angle(self):
        Clock.schedule_interval(self.show_angle, sample_time)
        angle = self.ids.angle_text.text
        if angle != "":
            print("angle is set to: " + angle)
            md.set_angle_x(float(angle)) # bu fonksiyonu text açısına ulaşacak şekilde düzenle
            test_angle = angle
        else:
            print("no angle given")
            test_angle = 0

class ScreenThree(Screen):
    date_today = datetime.date.today()
    date_text = str(date_today)
    date_text = date_text
    def __init__(self, **args):
        Screen.__init__(self, **args)
        self.static_cof_text = "0"
        self.l_static = Label(text=self.static_cof_text)
        self.l_static.pos = (-90, 95)
        self.l_static.pos_hint_x = 0.5
        self.l_static.color = (0,0,0,1)
        self.add_widget(self.l_static)

        self.dynamic_cof_text = "0"
        self.l_dynamic = Label(text=self.dynamic_cof_text)
        self.l_dynamic.pos = -90, 0
        self.l_dynamic.color = (0,0,0,1)
        self.add_widget(self.l_dynamic)


    def create_results(self):
        dynamic_cof = str(self.find_dynamic_cof())
        static_cof = str(self.find_static_cof())
        return dynamic_cof, static_cof

    def find_dynamic_cof(self):
        dynamic_force = find_biggest(forces)
        dynamic_cof = dynamic_force / (normal_force * 9.81 * cos(test_angle))
        dynamic_cof = round(dynamic_cof, 3)
        return dynamic_cof

    def find_static_cof(self):
#        static_force = round(find_static_force(forces), 3)
        static_force = 10
        static_cof = static_force / (normal_force * 9.81 * cos(test_angle))
        static_cof = round(static_cof)
        return static_cof

    def update_results(self):
        self.dynamic, self.static =  self.create_results()
        self.static_cof_text = str(self.static)
        self.dynamic_cof_text = str(self.dynamic)
        print(self.dynamic_cof_text)
        self.l_dynamic.text = self.dynamic_cof_text
        self.l_static.text = self.static_cof_text
    def createPDF(self):
        self.pdf = fpdf_handler()
        self.pdf.create_pdf( self.static, self.dynamic, sample1, sample2)
        print("PDF created!")




screen_manager = ScreenManager()
"""
ScreenThree.add_widget(ScreenThree.l_static)
ScreenThree.add_widget(ScreenThree.l_dynamic)
"""
screen_manager.add_widget(ScreenOne(name="screen_one"))
screen_manager.add_widget(ScreenTwo(name="screen_two"))
screen_manager.add_widget(ScreenThree(name="screen_three"))



class AwesomeApp(App):
    def build(self):
        Window.clearcolor = (1,1,1,1)
        Window.size = (800, 480) # pencere boyutu
        return screen_manager



if __name__ == "__main__":
    AwesomeApp().run()

