from datetime import datetime
from fpdf import FPDF

class TenantReportPrinter:
    def __init__(self):
        self.pdf = FPDF()
        
    def generate_report(self, tenants_data):
        """
        Generate a PDF report with tenant consumption and payment information
        :param tenants_data: List of dictionaries containing tenant information
        """
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        
        # Header
        self.pdf.cell(0, 10, "Lista Locatarilor si Consumul", ln=True, align='C')
        self.pdf.ln(10)
        
        # Column headers
        self.pdf.set_font("Arial", "B", 12)
        self.pdf.cell(50, 10, "Nume Locatar", border=1)
        self.pdf.cell(40, 10, "Apartament", border=1)
        self.pdf.cell(50, 10, "Consum (RON)", border=1)
        self.pdf.cell(50, 10, "De Plata", border=1)
        self.pdf.ln()
        
        # Data rows
        self.pdf.set_font("Arial", "", 12)
        for tenant in tenants_data:
            self.pdf.cell(50, 10, str(tenant.get('nume', '')), border=1)
            self.pdf.cell(40, 10, str(tenant.get('apartament', '')), border=1)
            self.pdf.cell(50, 10, f"{tenant.get('consum', 0):.2f}", border=1)
            self.pdf.cell(50, 10, f"{tenant.get('de_plata', 0):.2f}", border=1)
            self.pdf.ln()
            
    def save(self, filename="raport_locatari.pdf"):
        """Save the generated PDF report"""
        self.pdf.output(filename)
