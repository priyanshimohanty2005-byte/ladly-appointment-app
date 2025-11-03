import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
import base64
from io import BytesIO

# ---------------------------------------------
# DATABASE SETUP
# ---------------------------------------------
conn = sqlite3.connect('ladly.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS appointments
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              customer_name TEXT,
              contact TEXT,
              service TEXT,
              staff TEXT,
              date TEXT,
              time TEXT,
              price REAL)''')
conn.commit()

# ---------------------------------------------
# PAGE CONFIG & STYLE
# ---------------------------------------------
st.set_page_config(page_title="Ladly Appointment App", layout="wide")

st.markdown("""
    <style>
        body {
            background-color: #fff3f3;
            color: #2e2e2e;
            font-family: 'Poppins', sans-serif;
        }
        .block-container {
            padding-top: 1rem;
        }
        .sidebar .sidebar-content {
            background-color: #b76e79;
        }
        h1, h2, h3 {
            color: #b76e79;
            font-weight: 600;
        }
        .metric-card {
            background-color: #ffe4ec;
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0px 2px 8px rgba(183, 110, 121, 0.2);
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------
# HEADER
# ---------------------------------------------
st.markdown("<h1 style='text-align:center;'>💅 Ladly Appointment App</h1>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------
menu = ["Dashboard", "Book Appointment", "View Appointments", "Generate Invoice"]
choice = st.sidebar.selectbox("Select Page", menu)

# ---------------------------------------------
# BOOK APPOINTMENT
# ---------------------------------------------
if choice == "Book Appointment":
    st.subheader("📅 Book a New Appointment")

    with st.form(key="booking_form"):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name")
            contact = st.text_input("Contact Number")
            service = st.selectbox("Select Service", ["Haircut", "Facial", "Manicure", "Pedicure", "Makeup", "Hair Spa"])
        with col2:
            staff = st.selectbox("Assign Staff", ["Bharti", "Rupa", "Gudi"])
            date = st.date_input("Select Date")
            time = st.time_input("Select Time")
            price = st.number_input("Service Price (₹)", min_value=0)

        submitted = st.form_submit_button("Confirm Appointment")

        if submitted:
            c.execute('INSERT INTO appointments (customer_name, contact, service, staff, date, time, price) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (customer_name, contact, service, staff, str(date), str(time), price))
            conn.commit()
            st.success(f"Appointment booked for {customer_name} with {staff} on {date} at {time}")

# ---------------------------------------------
# VIEW APPOINTMENTS
# ---------------------------------------------
elif choice == "View Appointments":
    st.subheader("📋 All Appointments")

    df = pd.read_sql("SELECT * FROM appointments", conn)
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No appointments found.")

# ---------------------------------------------
# DASHBOARD
# ---------------------------------------------
elif choice == "Dashboard":
    st.subheader("📊 Salon Dashboard & Staff Performance")

    df = pd.read_sql("SELECT * FROM appointments", conn)
    if df.empty:
        st.info("No data available yet.")
    else:
        total_appointments = len(df)
        total_revenue = df["price"].sum()
        top_staff = df["staff"].value_counts().idxmax()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='metric-card'><h3>Total Appointments</h3><h2>{total_appointments}</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-card'><h3>Total Revenue</h3><h2>₹{total_revenue}</h2></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-card'><h3>Top Performer</h3><h2>{top_staff}</h2></div>", unsafe_allow_html=True)

        st.markdown("### 📈 Revenue by Staff")
        revenue_by_staff = df.groupby("staff")["price"].sum()
        fig, ax = plt.subplots()
        ax.bar(revenue_by_staff.index, revenue_by_staff.values, color="#b76e79")
        plt.xlabel("Staff")
        plt.ylabel("Revenue (₹)")
        st.pyplot(fig)

        st.markdown("### 💇‍♀️ Appointments by Service Type")
        service_counts = df["service"].value_counts()
        fig2, ax2 = plt.subplots()
        ax2.pie(service_counts.values, labels=service_counts.index, autopct="%1.1f%%", startangle=90,
                colors=["#f4b6c2", "#b76e79", "#ffc4d6", "#ffb3c6", "#e7a0b6", "#c25b73"])
        st.pyplot(fig2)

# ---------------------------------------------
# INVOICE GENERATOR
# ---------------------------------------------
elif choice == "Generate Invoice":
    st.subheader("🧾 Generate Customer Invoice")

    df = pd.read_sql("SELECT * FROM appointments", conn)
    if df.empty:
        st.info("No appointments to generate invoices.")
    else:
        selected_name = st.selectbox("Select Customer", df["customer_name"].unique())
        record = df[df["customer_name"] == selected_name].iloc[-1]

        st.write(f"**Customer Name:** {record['customer_name']}")
        st.write(f"**Service:** {record['service']}")
        st.write(f"**Staff:** {record['staff']}")
        st.write(f"**Date:** {record['date']}")
        st.write(f"**Time:** {record['time']}")
        st.write(f"**Amount:** ₹{record['price']}")

        # PDF GENERATION FIXED
        def generate_pdf(data):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 18)
            pdf.set_text_color(183, 110, 121)
            pdf.cell(200, 10, txt="Ladly Appointment Invoice", ln=True, align="C")
            pdf.set_font("Arial", "", 12)
            pdf.set_text_color(50, 50, 50)
            pdf.ln(10)
            for key, value in data.items():
                pdf.cell(0, 10, f"{key}: {value}", ln=True)
            pdf.ln(10)
            pdf.cell(0, 10, "Thank you for visiting Ladly!", ln=True, align="C")

            # Write PDF to memory buffer
            pdf_output = BytesIO()
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            pdf_output.write(pdf_bytes)
            pdf_output.seek(0)
            return pdf_output

        if st.button("Generate PDF Invoice"):
            data = {
                "Customer": record['customer_name'],
                "Service": record['service'],
                "Staff": record['staff'],
                "Date": record['date'],
                "Time": record['time'],
                "Total Amount": f"₹{record['price']}"
            }
            pdf_data = generate_pdf(data)
            b64 = base64.b64encode(pdf_data.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="invoice_{record["customer_name"]}.pdf">📥 Download Invoice PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
