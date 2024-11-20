import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd


st.title("Job List")

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

# Display jobs
for _, job in jobs.iterrows():
    with st.container(border=True):
        col1, col2, col3 = st.columns([2,2,1])
        
        with col1:
            st.markdown(f"**Job ID:** {job['job_id']}")
            st.markdown(f"**Client:** {job['client_name']}")
        
        with col2:
            st.markdown(f"**Date:** {job['job_date']}")
            st.markdown(f"**Total:** CHF {job['total_amount']:.2f}")

# Deletes the Job (couldnt do it with confirmation button)   
     
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