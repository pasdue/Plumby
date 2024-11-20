import streamlit as st
from datetime import datetime, timedelta
import sqlite3

st.set_page_config(page_title="Job Entry", page_icon="🔧", layout="wide")

#Initialize session state variables
if 'api_items' not in st.session_state:
    st.session_state.api_items = []
if 'manual_items' not in st.session_state:
    st.session_state.manual_items = []
if 'work_hours' not in st.session_state:
    st.session_state.work_hours = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'show_selection' not in st.session_state:
    st.session_state.show_selection = False

# Initialize job database
conn = sqlite3.connect('job_data.db')
c = conn.cursor()

# the ''' are used to write on multiple lines in SQL (only for readability)

c.execute('''CREATE TABLE IF NOT EXISTS jobs               
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             job_id TEXT,
             client_name TEXT,
             client_address TEXT,
             job_date TEXT,
             job_notes TEXT,
             total_amount REAL,
             timestamp TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS job_items
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             job_id TEXT,
             type TEXT,
             description TEXT,
             price REAL,
             quantity REAL)''')

conn.commit()
conn.close()

def save_job_to_db(job_data, items_data):
    try:
        conn = sqlite3.connect('job_data.db')
        c = conn.cursor()

        c.execute("INSERT INTO jobs (job_id, client_name, client_address, job_date, job_notes, total_amount, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (job_data['job_id'], job_data['client_name'], job_data['client_address'], job_data['job_date'], job_data['job_notes'], job_data['total_amount'], job_data['timestamp']))

        for item in items_data:
            c.execute("INSERT INTO job_items (job_id, type, description, price, quantity) VALUES (?, ?, ?, ?, ?)",
                      (job_data['job_id'], item['type'], item['description'], item['price'], item['quantity']))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving job data: {str(e)}")
        return False

def save_job_data(client_name, client_address, job_date, job_notes, total):

#creating a unique job id with curent date and time (Year, Months; days, hours, minutes, seconds)
    job_id = datetime.now().strftime('%Y%m%d_%H%M%S')         
    job_data = {
        'job_id': job_id,
        'client_name': client_name,
        'client_address': client_address,
        'job_date': job_date.strftime('%Y-%m-%d'),
        'job_notes': job_notes,
        'total_amount': total,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    items_data = []
    for item in st.session_state.api_items:
        items_data.append({
            'type': 'catalog',
            'description': f"{item[2]} (AFNr: {item[3]} - {item[4]})",
            'price': float(item[1]) if item[1] else 0,
            'quantity': float(item[-1]) if item[-1] else 0
        })
    for item in st.session_state.manual_items:
        items_data.append({
            'type': 'manual',
            'description': item['description'],
            'price': item['price'],
            'quantity': item['quantity']
        })
    for item in st.session_state.work_hours:
        items_data.append({
            'type': 'work',
            'description': item['description'],
            'price': item['rate'],
            'quantity': item['hours']
        })
    
    if save_job_to_db(job_data, items_data):
        st.success("Job saved!")
        st.session_state.api_items = []
        st.session_state.manual_items = []
        st.session_state.work_hours = []

def show_job_entry():
    st.title("Enter Client Information")
    with st.expander("Client Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input("Client Name")
            client_address = st.text_area("Client Address")
        with col2:
            job_date = st.date_input("Job Date", datetime.today())
            job_notes = st.text_area("Job Notes")

    conn = sqlite3.connect('BR_Bauhandel_Database.db')
    c = conn.cursor()

    st.title("Select your Items")
    with st.expander("Add Items", expanded=True):
        tab1, tab2, tab3 = st.tabs(["Catalog Search", "Manual Entry", "Work Hours"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                search_value = st.text_input("Article Number")
            with col2:
                catalog_quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            
            if st.button("Search"):
                if search_value:
                    c.execute('SELECT DISTINCT "ArtikelNr", "AFNr", "AF Bezeichnung" FROM BR_Bauhandel WHERE "ArtikelNr" = ?', (search_value,))
                    results = c.fetchall()
                    
                    if results:
                        st.session_state.search_results = results
                        st.session_state.show_selection = True
                    else:
                        st.error("No items found with this Article Number")
            
            if 'show_selection' in st.session_state and st.session_state.show_selection:
                if 'search_results' in st.session_state and st.session_state.search_results:
                    st.write("Please select the specific item:")
                    
                    options = [f"AFNr: {row[1]} - {row[2]}" for row in st.session_state.search_results]
                    selected_option = st.selectbox("Available Items", options)
                    
                    if st.button("Add Selected Item"):
                        selected_index = options.index(selected_option)
                        selected_afnr = st.session_state.search_results[selected_index][1]
                        
                        c.execute('SELECT "ArtikelNr", "Preis", "Beschreibung", "AFNr", "AF Bezeichnung" FROM BR_Bauhandel WHERE "ArtikelNr" = ? AND "AFNr" = ?', 
                                (search_value, selected_afnr))
                        item = c.fetchone()
                        
                        if item:
                            item_with_quantity = list(item)
                            item_with_quantity.append(catalog_quantity)
                            st.session_state.api_items.append(item_with_quantity)
                            st.success("Item added")
                            
                            st.session_state.show_selection = False
                            st.session_state.search_results = None
                            st.rerun()

        with tab2:
            cols = st.columns(3)
            with cols[0]:
                desc = st.text_input("Description")
            with cols[1]:
                price = st.number_input("Price (CHF)", min_value=0.0, step=0.01)
            with cols[2]:
                qty = st.number_input("Quantity", min_value=1, step=1)
            
            if st.button("Add Item"):
                if desc and price:
                    st.session_state.manual_items.append({
                        'description': desc,
                        'price': price,
                        'quantity': qty,
                        'total': price * qty
                    })
                    st.success("Item added")

        with tab3:
            cols = st.columns(3)
            with cols[0]:
                work_desc = st.text_input("Work Description")
            with cols[1]:
                rate = st.number_input("Hourly Rate (CHF)", min_value=0.0, step=0.5)
            with cols[2]:
                hours = st.number_input("Hours", min_value=0.0, step=0.5)
            
            if st.button("Add Hours"):
                if work_desc and rate and hours:
                    st.session_state.work_hours.append({
                        'description': work_desc,
                        'rate': rate,
                        'hours': hours,
                        'total': rate * hours
                    })
                    st.success("Hours added")

    conn.close()

    st.title("Job Overview")

    with st.expander("### Current Items", expanded=True):              ## **MAKES IT BOLD / ## MAKES IT BIGGER
        st.write("Catalog Items:")
        if st.session_state.api_items:
            total_api = 0
            for item in st.session_state.api_items:
                try:
                    price = float(item[1]) if item[1] else 0
                    quantity = float(item[-1])
                    item_total = price * quantity
                    total_api += item_total
                    st.write(f"{item[2]} (AFNr: {item[3]} - {item[4]}) - CHF{price:.2f} x {quantity} = CHF{item_total:.2f}")
                except (ValueError, TypeError, IndexError) as e:
                    st.error(f"Error processing catalog item: {str(e)}")
        else:
            total_api = 0
        
        st.write("Manual Items:")
        if st.session_state.manual_items:            
            total_manual = 0
            for item in st.session_state.manual_items:
                try:
                    item_total = item['price'] * item['quantity']
                    total_manual += item_total
                    st.write(f"{item['description']} - CHF{item['price']:.2f} x {item['quantity']} = CHF{item_total:.2f}")
                except KeyError as e:
                    st.error(f"Error processing manual item: {str(e)}")
        else:
            total_manual = 0

        st.write("Work Hours:")
        if st.session_state.work_hours:
            total_work = 0
            for item in st.session_state.work_hours:
                try:
                    item_total = item['rate'] * item['hours']
                    total_work += item_total
                    st.write(f"{item['description']} - CHF{item['rate']:.2f}/hr x {item['hours']}hrs = CHF{item_total:.2f}")
                except KeyError as e:
                    st.error(f"Error processing work hours: {str(e)}")
        else:
            total_work = 0
        
        total = total_api + total_manual + total_work

        #-------- replaced in the colum below
        ####  st.subheader(f"Total: CHF{total:.2f}")  

    # Box using st.container

    container = st.container(border=True)

    col1, col2 = st.columns(2)
    with col1:
          container.markdown("## Total Value:")
    with col2:
          container.markdown(f"### CHF {total:.2f}")

# Buttons to Save everything (saves to job data) or cleare everythin in Sessions State (empty the cache)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Job"):
            if not client_name:
                st.error("Enter client name")
            else:
                save_job_data(client_name, client_address, job_date, job_notes, total)

    with col2:
        if st.button("Clear All"):
            st.session_state.api_items = []
            st.session_state.manual_items = []
            st.session_state.work_hours = []
            st.success("Cleared")

show_job_entry()