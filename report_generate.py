from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class PDFReport:
    def __init__(self, filename, title, content):
        self.filename = filename
        self.title = title
        self.content = content

    def generate_report(self):
        c = canvas.Canvas(self.filename, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, self.title)
        c.setFont("Helvetica", 12)
        y_position = 730
        for line in self.content.split('\n'):
            c.drawString(100, y_position, line)
            y_position -= 20
        c.save()

# Usage
title = "Patient Report"
content = """
Cytochrome P450 2C19 Genotype

This is a sample content for the PDF report.

More details can be added here.

Conclusion:
"""

import os

directory = r"C:\users\karla\OneDrive\Documents\NE 4B\NE 409"
if not os.path.exists(directory):
    os.makedirs(directory)

report = PDFReport(r"C:\users\karla\OneDrive\Documents\NE 4B\NE 409\sample_report.pdf", title, content)
report.generate_report()
