import datetime
import shutil
from os import popen

from fpdf import FPDF
from json_dumper import JsonDumper


json_out = JsonDumper()

class sample:
    name = "Sample Name"
    width = 10
    height = 20
    age = 0


class fpdf_handler(FPDF):
    date = "0"
    time = "0"
    date_today = "0"
    date_and_time = "0"

    def set_time(self):
        self.date_today = datetime.datetime.today()
        self.date = self.date_today.strftime("%d:%m:%Y")
        self.time = self.date_today.strftime("%H:%M:%S")
        self.date_and_time = self.date_today.strftime("%Y_%m_%d__%H_%M_%S")

    def header(self):
        # Set up a logo
        self.image('mini_logo.png', 10, 8, 33)

        self.set_font('Arial', 'I', 15)

        # Add test time
        self.cell(150)
        self.cell(0, 0, 'Date: ' + self.date, ln=1, align="L")
        self.cell(150)
        self.cell(0, 10, 'Time: ' + self.time, ln=1, align="L")
        self.cell(0, 10, "COF Test Results", ln=1, align="C")
        # Line break
        self.ln(5)

        self.set_line_width(1)
        self.line(x1=10, y1=30, x2=200, y2=30)
        # self.ln(10)

    def footer(self):
        self.set_y(-10)

        self.set_font('Arial', 'I', 12)

        self.set_line_width(1)
        self.line(x1=10, y1=285, x2=200, y2=285)

        self.cell(0, 10,
                  "Alarge Laboratory and Plastic Welding Teknologies - https://www.alarge.com.tr/en/ - info@alarge.com.tr")

    def graph_to_pdf(self, choise):
        if choise == 1:
            self.image('graph.png', x=30, y=140, w=150)
        else:
            self.image('graph.png', x=30, y=170, w=150)

    def print_obj(self, obj):
        print(obj.name)

    def create_pdf(self, static, dynamic, sample1, sample2, test_mode, forces):

        self.set_time()
        self.add_page()
        self.set_font('Times', '', 12)
        if sample2.name == "":
            self.single_table(sample1, static, dynamic, test_mode)
            self.graph_to_pdf(1)
        else:
            self.diff_table(sample1, sample2, static, dynamic, test_mode)
            self.graph_to_pdf(2)

        filename = "COF Test " + self.date_and_time + ".pdf"
        mount_dir = "/media/pi/*"
        self.output(filename)
        self.close()
        json_out.dump_time(static, dynamic, sample1, sample2, test_mode, forces, self.date_and_time)

        source = "./" + filename
        usb_dir = popen("ls " + mount_dir).read()
        usb_dir = usb_dir.split()
        if usb_dir.count("media/pi/ALI") > 0:
            usb_dir = usb_dir.remove("/media/pi/ALI")
            print("ALI'yi buldum ve silmeye calistim")
        try:
            usb_dir = usb_dir[0]
            destination = usb_dir + filename

            popen("cp " + source + " " + str(destination) +"/")
            try:
                shutil.copy2(source, str(destination))
            except shutil.Error as e:
                print("Error: %s" % e)
            except IOError as e:
                print("Error: %s" % e.strerror)
        except:
            pass
    def single_table(self, sample, staticCof, dynamicCof, test_mode):
        if test_mode == 1:
            test_mode = "Angle Test"
        elif test_mode == 0:
            test_mode = "Motorized Test"
        data = [['Standard: ', "ISO 8295"],
                ['Company Name: ', sample.company_name],
                ['Operator Name: ', sample.operator_name],
                ['Testing Weight(gr): ', str(sample.testing_weight)],
                ['Test Mode: ', test_mode],
                ['Sample Name: ', sample.name],
                ['Sample Width(mm): ', str(sample.width)],
                ['Sample Height(mm): ', str(sample.height)],
                ['Sample Age(months): ', str(sample.age)],
                ['Testing Against: ', 'The same sample'],
                ['Static Coefficient of Friction: ', str(staticCof)],
                ['Dynamic Coefficient of Friction: ', str(dynamicCof)]
                ]
        spacing = 2
        self.set_font("Arial", size=12)
        col_width = self.w / 2.2
        row_height = self.font_size
        for row in data:
            for item in row:
                self.cell(col_width, row_height * spacing,
                          txt=item, border=0)
            self.ln(row_height * spacing)

    def diff_table(self, sample1, sample2, staticCof, dynamicCof, test_mode):
        if test_mode == 1:
            test_mode = "Angle Test"
        elif test_mode == 0:
            test_mode = "Motorized Test"
        data = [['Standard: ', "ISO 8295"],
                ['Company Name: ', sample1.company_name],
                ['Operator Name: ', sample1.operator_name],
                ['Testing Weight(gr): ', str(sample1.testing_weight)],
                ['Test Mode: ', test_mode],
                ['Sample Name: ', sample1.name],
                ['Sample Width(mm): ', str(sample1.width)],
                ['Sample Height(mm): ', str(sample1.height)],
                ['Sample Age: ', str(sample1.age)],
                ['Testing Against: ', 'Different Sample'],
                ['Second Sample Name: ', sample2.name],
                ['Second Sample Width(mm): ', str(sample2.width)],
                ['Second Sample Height(mm): ', str(sample2.height)],
                ['Second Sample Age(months): ', str(sample2.age)],
                ['Static Coefficient of Friction: ', str(staticCof)],
                ['Dynamic Coefficient of Friction: ', str(dynamicCof)]
                ]
        spacing = 2
        self.set_font("Arial", size=12)
        col_width = self.w / 2.2
        row_height = self.font_size
        for row in data:
            for item in row:
                self.cell(col_width, row_height * spacing,
                          txt=item, border=0)
            self.ln(row_height * spacing)
