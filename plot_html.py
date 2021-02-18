
import plotly.plotly as py
import base64

from fpdf import FPDF, HTMLMixin

class PDF(FPDF, HTMLMixin):
    pass

pdf = PDF()
pdf.add_page()

width = 600
height = 600

template = (''
    '<img style="width: {width}; height: {height}" src="data:image/png;base64,{image}">'
    '{caption}'                              # Optional caption to include below the graph
    '<br>'
    '<hr>'
'')

# A collection of Plotly graphs
figures = [
    {'data': [{'x': [1,2,3], 'y': [3,1,6]}], 'layout': {'title': 'the first graph'}},
    {'data': [{'x': [1,2,3], 'y': [3,7,6], 'type': 'bar'}], 'layout': {'title': 'the second graph'}}
]

# Generate their images using `py.image.get`
images = [base64.b64encode(py.image.get(figure, width=width, height=height)).decode('utf-8') for figure in figures]

report_html = ''
for image in images:
    _ = template
    _ = _.format(image=image, caption='', width=width, height=height)
    report_html += _

pdf.write_html(report_html)

pdf.output("html.pdf")