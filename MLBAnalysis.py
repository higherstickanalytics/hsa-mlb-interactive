import streamlit as st
import pandas as pd

# Paths to the files
hitters_path = 'data/baseball_data/combined_hitters_data.csv'
pitchers_path = 'data/baseball_data/combined_pitchers_data.csv'
schedule_path = 'data/MLB_Schedule.csv'

# Load the data
hitters_df = pd.read_csv(hitters_path)
pitchers_df = pd.read_csv(pitchers_path)
schedule_df = pd.read_csv(schedule_path, parse_dates=['Date'], dayfirst=False)

# Title of the app
st.title("MLB Data Viewer")

# Display the first 5 rows of each dataset
st.subheader("First 5 Rows of Hitters Data")
st.dataframe(hitters_df.head())

st.subheader("First 5 Rows of Pitchers Data")
st.dataframe(pitchers_df.head())

st.subheader("First 5 Rows of MLB Schedule Data")
st.dataframe(schedule_df.head())
