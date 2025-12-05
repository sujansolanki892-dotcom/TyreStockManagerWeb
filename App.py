import streamlit as st
import pandas as pd
from collections import Counter
from datetime import datetime

# --- Load CSV files ---
@st.cache_data
def load_stock():
    return pd.read_csv("stock.csv")

@st.cache_data
def load_billing():
    return pd.read_csv("billing.csv")

@st.cache_data
def load_complaints():
    return pd.read_csv("complaint.csv")

# --- Save CSV files ---
def save_stock(df):
    df.to_csv("stock.csv", index=False)

def save_billing(df):
    df.to_csv("billing.csv", index=False)

def save_complaints(df):
    df.to_csv("complaint.csv", index=False)

# --- Helper for price suggestion ---
def suggest_price(tyre_name, stock_df, billing_df):
    min_price = stock_df.loc[stock_df['TyreName']==tyre_name, 'PurchasePrice'].values[0]
    prices = billing_df.loc[billing_df['TyreName']==tyre_name, 'SellPrice'].tolist()
    most_freq_price = Counter(prices).most_common(1)[0][0] if prices else min_price
    return min_price, most_freq_price

# --- Streamlit UI ---
st.title("Tyre Stock Manager (Web Version)")

menu = ["Stock", "Billing", "Customer Demand", "Complaints"]
choice = st.sidebar.selectbox("Menu", menu)

# --- STOCK ---
if choice == "Stock":
    st.header("Stock List")
    stock_df = load_stock()
    st.dataframe(stock_df)

    st.subheader("Add / Update Stock")
    tyre_name = st.text_input("Tyre Name")
    size = st.text_input("Size")
    brand = st.text_input("Brand")
    purchase_price = st.number_input("Purchase Price", min_value=0)
    quantity = st.number_input("Quantity", min_value=0, step=1)
    
    if st.button("Add / Update Stock"):
        if tyre_name in stock_df['TyreName'].values:
            stock_df.loc[stock_df['TyreName']==tyre_name, ['Size','Brand','PurchasePrice','Quantity']] = [size, brand, purchase_price, quantity]
        else:
            stock_df = pd.concat([stock_df, pd.DataFrame([[tyre_name,size,brand,purchase_price,quantity]], columns=stock_df.columns)], ignore_index=True)
        save_stock(stock_df)
        st.success("Stock updated successfully!")
        st.dataframe(stock_df)

# --- BILLING ---
elif choice == "Billing":
    st.header("Create Bill")
    stock_df = load_stock()
    billing_df = load_billing()

    tyre_name = st.selectbox("Select Tyre", stock_df['TyreName'].tolist())
    qty = st.number_input("Quantity", min_value=1, step=1)
    sell_price = st.number_input("Sell Price", min_value=0)
    
    if st.button("Create Bill"):
        available_qty = stock_df.loc[stock_df['TyreName']==tyre_name, 'Quantity'].values[0]
        if qty > available_qty:
            st.warning("Not enough stock!")
        else:
            # Update stock
            stock_df.loc[stock_df['TyreName']==tyre_name, 'Quantity'] -= qty
            save_stock(stock_df)
            
            # Save billing
            bill_number = len(billing_df)+1
            date = datetime.now().strftime("%d-%m-%Y %H:%M")
            total_price = qty * sell_price
            billing_df = pd.concat([billing_df, pd.DataFrame([[bill_number,date,tyre_name,
                                                              stock_df.loc[stock_df['TyreName']==tyre_name,'Size'].values[0],
                                                              stock_df.loc[stock_df['TyreName']==tyre_name,'Brand'].values[0],
                                                              qty,sell_price,total_price]],
                                                            columns=billing_df.columns)], ignore_index=True)
            save_billing(billing_df)
            st.success(f"Bill #{bill_number} created!")
            st.dataframe(billing_df)

# --- CUSTOMER DEMAND ---
elif choice == "Customer Demand":
    st.header("Customer Demand / Price Suggestion")
    stock_df = load_stock()
    billing_df = load_billing()
    tyre_search = st.text_input("Enter Tyre Name or Size")
    
    if st.button("Search"):
        results = []
        for idx,row in stock_df.iterrows():
            if tyre_search.lower() in row['TyreName'].lower() or tyre_search.lower() in row['Size'].lower():
                min_price, freq_price = suggest_price(row['TyreName'], stock_df, billing_df)
                results.append({
                    "TyreName": row['TyreName'],
                    "Size": row['Size'],
                    "Brand": row['Brand'],
                    "Stock": row['Quantity'],
                    "Buy Price": row['PurchasePrice'],
                    "Lowest Sell Price": min_price,
                    "Most Frequent Price": freq_price
                })
        if results:
            st.dataframe(pd.DataFrame(results))
        else:
            st.warning("No tyres found!")

# --- COMPLAINTS ---
elif choice == "Complaints":
    st.header("Add Complaint")
    stock_df = load_stock()
    complaints_df = load_complaints()

    tyre_name = st.selectbox("Select Tyre", stock_df['TyreName'].tolist())
    issue = st.text_input("Issue Description")
    qty_affected = st.number_input("Quantity Affected", min_value=1, step=1)

    if st.button("Add Complaint"):
        date = datetime.now().strftime("%d-%m-%Y")
        complaints_df = pd.concat([complaints_df, pd.DataFrame([[tyre_name,
                                                                 stock_df.loc[stock_df['TyreName']==tyre_name,'Size'].values[0],
                                                                 stock_df.loc[stock_df['TyreName']==tyre_name,'Brand'].values[0],
                                                                 date,issue,qty_affected,'Pending']],
                                                               columns=complaints_df.columns)], ignore_index=True)
        save_complaints(complaints_df)
        st.success("Complaint added!")
        st.dataframe(complaints_df)
