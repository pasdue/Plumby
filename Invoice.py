import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

def get_jobs(date_from=None, date_to=None, search_term=None):
   conn = sqlite3.connect('job_data.db')
   query = """
       SELECT j.*, 
              GROUP_CONCAT(i.description || ' - ' || i.quantity || ' x CHF' || i.price) as items
       FROM jobs j
       LEFT JOIN job_items i ON j.job_id = i.job_id
       WHERE 1=1
   """
   params = []
   if date_from:
       query += " AND j.job_date >= ?"
       params.append(date_from)
   if date_to:
       query += " AND j.job_date <= ?"
       params.append(date_to)
   if search_term:
       query += " AND (j.client_name LIKE ? OR j.job_id LIKE ?)"
       params.extend([f"%{search_term}%", f"%{search_term}%"])
   query += " GROUP BY j.job_id ORDER BY j.job_date DESC"
   return pd.read_sql_query(query, conn, params=params)

def delete_job(job_id):
   conn = sqlite3.connect('job_data.db')
   c = conn.cursor()
   try:
       c.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
       c.execute("DELETE FROM job_items WHERE job_id = ?", (job_id,))
       conn.commit()
       return True
   except Exception as e:
       st.error(f"Error deleting job: {str(e)}")
       return False
   finally:
       conn.close()

def get_job_details(job_id):
   conn = sqlite3.connect('job_data.db')
   c = conn.cursor()
   c.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
   job = c.fetchone()
   c.execute("SELECT * FROM job_items WHERE job_id = ?", (job_id,))
   items = c.fetchall()
   conn.close()
   return job, items

def create_pdf_invoice(selected_jobs):
   buffer = io.BytesIO()
   doc = SimpleDocTemplate(buffer, pagesize=A4)
   elements = []
   styles = getSampleStyleSheet()

   for _, job in selected_jobs.iterrows():
       # Header
       elements.append(Paragraph("DÜBENDORFER SANITÄR-SERVICE GmbH", styles['Heading1']))
       elements.append(Paragraph("Glattwiesenstrasse 20, 8152 Glattbrugg", styles['Normal']))
       elements.append(Paragraph("Tel: 076 388 95 60", styles['Normal']))
       elements.append(Spacer(1, 20))
       
       # Client Info
       elements.append(Paragraph(f"Bill To:", styles['Normal']))
       elements.append(Paragraph(job['client_name'], styles['Normal']))
       elements.append(Paragraph(job['client_address'], styles['Normal']))
       elements.append(Spacer(1, 20))
       
       # Invoice Details
       elements.append(Paragraph(f"Invoice #: {job['job_id']}", styles['Normal']))
       elements.append(Paragraph(f"Date: {job['job_date']}", styles['Normal']))
       elements.append(Spacer(1, 20))

       # Get items
       conn = sqlite3.connect('job_data.db')
       c = conn.cursor()
       c.execute("SELECT * FROM job_items WHERE job_id = ?", (job['job_id'],))
       items = c.fetchall()

       # Items Table
       data = [['Description', 'Quantity', 'Price', 'Total']]
       for item in items:
           total = float(item[4]) * float(item[5])
           data.append([
               item[3],
               f"{float(item[5]):.2f}",
               f"CHF {float(item[4]):.2f}",
               f"CHF {total:.2f}"
           ])
       data.append(['', '', 'Total:', f"CHF {float(job['total_amount']):.2f}"])

       table = Table(data, colWidths=[250, 75, 100, 100])
       table.setStyle([
           ('FONT', (0,0), (-1,-1), 'Helvetica'),
           ('FONTSIZE', (0,0), (-1,-1), 10),
           ('GRID', (0,0), (-1,-2), 1, colors.black),
           ('BACKGROUND', (0,0), (-1,0), colors.grey),
           ('TEXTCOLOR', (0,0), (-1,0), colors.white),
       ])
       
       elements.append(table)
       elements.append(Spacer(1, 20))
       
       # Bank Details
       elements.append(Paragraph("Bank Details:", styles['Normal']))
       elements.append(Paragraph("Bank: UBS Switzerland AG", styles['Normal']))
       elements.append(Paragraph("IBAN: CH85 0028 3283 1127 5501 Y", styles['Normal']))
       elements.append(Paragraph("BIC: UBSWCHZH80A", styles['Normal']))
       elements.append(Paragraph("MWST-Nr.: CHE-257.523.928", styles['Normal']))
       
       elements.append(Spacer(1, 30))

   doc.build(elements)
   return buffer.getvalue()

st.title("Invoice Creator")

# Filters
col1, col2, col3 = st.columns(3)
with col1:
   date_from = st.date_input("From Date", key="date_from")
with col2:
   date_to = st.date_input("To Date", key="date_to")
with col3:
   search = st.text_input("Search (Client or Job ID)", key="search")

# Get filtered jobs
jobs = get_jobs(
   date_from.strftime('%Y-%m-%d'),
   date_to.strftime('%Y-%m-%d'),
   search
)

# Multi-select jobs
selected_job_indices = []
for index, job in jobs.iterrows():
   with st.container(border=True):
       col1, col2, col3 = st.columns([2,2,1])
       
       with col1:
           selected = st.checkbox(f"Select", key=f"select_{job['job_id']}")
           if selected:
               selected_job_indices.append(index)
           st.markdown(f"**Job ID:** {job['job_id']}")
           st.markdown(f"**Client:** {job['client_name']}")
       
       with col2:
           st.markdown(f"**Date:** {job['job_date']}")
           st.markdown(f"**Total:** CHF {job['total_amount']:.2f}")
       
       with col3:
           if st.button("Delete", key=job['job_id']):
               if delete_job(job['job_id']):
                   st.success("Job deleted!")
                   st.rerun()
       
       with st.expander("Details"):
           st.write("**Address:**", job['client_address'])
           st.write("**Notes:**", job['job_notes'])
           if job['items']:
               st.write("**Items:**")
               items_list = job['items'].split(',')
               for item in items_list:
                   st.write(f"- {item}")

# Generate PDF button
if selected_job_indices and st.button("Generate Selected Invoices"):
   selected_jobs = jobs.iloc[selected_job_indices]
   pdf = create_pdf_invoice(selected_jobs)
   st.download_button(
       label="Download Invoices",
       data=pdf,
       file_name="invoices.pdf",
       mime="application/pdf"
   )