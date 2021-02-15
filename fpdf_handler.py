from fpdf import FPDF
import datetime
import shutil

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
        self.date_and_time = self.date_today.strftime("%Y:%m:%d--%H:%M:%S")

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
        #self.ln(10)

    def footer(self):
        self.set_y(-10)

        self.set_font('Arial', 'I', 12)

        self.set_line_width(1)
        self.line(x1=10, y1=285, x2=200, y2=285)

        self.cell(0,10,"Alarge Laboratuvar ve Plastik Kaynak Teknolojileri - https://www.alarge.com.tr - info@alarge.com.tr")



    def print_obj(self, obj):
        print(obj.name)

    def create_pdf(self, static, dynamic, sample1, sample2):

        self.set_time()
        self.add_page()
        self.set_font('Times', '', 12)
        if sample2.name == "":
            self.single_table(sample1, static, dynamic)
        else:
            self.diff_table(sample1, sample2, static, dynamic)

        filename = "COF Test " + self.date_and_time + ".pdf"

        self.output(filename)
        source = "./" + filename
        destination = "/media/pi/USB1/" + filename

        try:
            shutil.copy2(source, destination)
        except shutil.Error as e:
            print("Error: %s" % e)
        except IOError as e:
            print("Error: %s" % e.strerror)
        self.close()


    def single_table(self, sample, staticCof, dynamicCof):
        data = [['Standard: ', "ISO 8295"],
                ['Sample Name: ', sample.name],
                ['Sample Width: ', str(sample.width)],
                ['Sample Heigth: ', str(sample.height)],
                ['Sample Age: ', str(sample.age)],
                ['Testing Against: ', 'The same sample'],
                ['Static Coefficient of Fricion: ', str(staticCof)],
                ['Dynamic Coefficient of Fricion: ', str(dynamicCof)]
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


    def diff_table(self, sample1, sample2, staticCof, dynamicCof):
        data = [['Standard: ', "ISO 8295"],
                ['Sample Name: ', sample1.name],
                ['Sample Width: ', str(sample1.width)],
                ['Sample Heigth: ', str(sample1.height)],
                ['Sample Age: ', str(sample1.age)],
                ['Testing Against: ', 'Different Sample'],
                ['Second Sample Name: ', sample2.name],
                ['Second Sample Width: ', str(sample2.width)],
                ['Second Sample Heigth: ', str(sample2.height)],
                ['Second Sample Age: ', str(sample2.age)],
                ['Static Coefficient of Fricion: ', str(staticCof)],
                ['Dynamic Coefficient of Fricion: ', str(dynamicCof)]
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
