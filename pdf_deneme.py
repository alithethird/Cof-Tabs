from fpdf_handler import fpdf_handler


class sample:
    name = "Sample Name"
    width = 10
    height = 20
    age = 0

    def get_size(self):
        size = str(self.width) + ' x ' + str(self.height)
        return size

    def get_age(self):
        return self.age

obj = sample()
sample2 = sample()
sample2.name = "-1"
md = fpdf_handler()
#md.print_obj(obj)
md.create_pdf(1, 2, obj, sample2)
