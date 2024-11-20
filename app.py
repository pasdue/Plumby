import streamlit as st

#----- PAGE SETUP ---------

# Dashboard Page
main_page = st.Page(
    page="views/Dashboard.py",
    title="Dashboard",
    icon="",
    default=True,
)

# Job Entry Page

JobEntry_page = st.Page(
    page="views\JobEntry.py",
    title="Job Entry",
    icon="",
)  

# Job List Page

JobList_page = st.Page(
    page="views\JobList.py",
    title="Job List",
    icon="",
)

# Invoice Creater Page

Invoice_page = st.Page(
    page="views\Invoice.py",
    title="Invoice Creater",
    icon="",
)

#------Naviagtion Setup -------------

pg = st.navigation(pages=[main_page, JobEntry_page, JobList_page, Invoice_page])

#------RUN NAVIAGTION --------------

pg.run()