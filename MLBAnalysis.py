import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# File paths
hitters_path = 'data/baseball_data/combined_hitters_data.csv'
pitchers_path = 'data/baseball_data/combined_pitchers_data.csv'
schedule_path = 'data/MLB_Schedule.csv'

# Load data
hitters_df = pd.read_csv(hitters_path)
pitchers_df = pd.read_csv(pitchers_path)
schedule_df = pd.read_csv(schedule_path, parse_dates=['Date'], dayfirst=False)

# Strip any extra spaces from column names
hitters_df.columns = [col.strip() for col in hitters_df.columns]
pitchers_df.columns = [col.strip() for col in pitchers_df.columns]

# Check the first few rows and column names of the Hitters data
st.write("Hitters Data Columns:")
st.write(hitters_df.columns)

st.write("First few rows of Hitters data:")
st.write(hitters_df.head())

# Check the 'Players' column specifically
st.write("First few players from the Hitters data:")
st.write(hitters_df['Players'].head())

# App title
st.title("MLB Data Viewer with Pie and Time-Series Charts")
st.write("Data from [MLB Stats](https://www.mlb.com/)")

# Sidebar: select player type
player_type = st.sidebar.radio("Select Player Type", ['Hitters', 'Pitchers'])

# Define dataframes and mappings
df = hitters_df if player_type == 'Hitters' else pitchers_df
player_list = df['Players'].dropna().unique().tolist()

# Check if player_list is empty
if len(player_list) == 0:
    st.write("No players found in the selected dataset.")
else:
    # Sidebar: player selection
    selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))

    # Sidebar: date filter
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min_date, value=min_date))
    end_date = pd.to_datetime(st.sidebar.date_input("End Date", max_value=max_date, value=max_date))

    # Filter data based on selected player and date range
    df_filtered = df[(df['Players'] == selected_player) & (df['Date'] >= start_date) & (df['Date'] <= end_date)]

    if df_filtered.empty:
        st.write("No data available for this player in the selected date range.")
    else:
        # Sidebar: stat selection (e.g., Batting Average, ERA)
        stat_options = ['BA', 'OBP', 'SLG', 'OPS', 'RBI', 'HR', 'SB', 'SO']  # Example for hitters
        if player_type == 'Pitchers':
            stat_options += ['ERA', 'SO9', 'WHIP']  # Additional options for pitchers
        selected_stat = st.sidebar.selectbox("Select a stat to analyze", stat_options)

        # Display the filtered data
        st.subheader(f"Data for {selected_player} ({player_type})")
        st.write(df_filtered[['Date', 'Players', selected_stat]])

        # Pie chart for selected stat
        stat_counts = df_filtered[selected_stat].value_counts().sort_index()
        fig, ax = plt.subplots()
        ax.pie(stat_counts, labels=stat_counts.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)

        # Time-series plot
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        ax2.plot(df_filtered['Date'], df_filtered[selected_stat], marker='o', linestyle='-', color='b')
        ax2.set_xlabel("Date")
        ax2.set_ylabel(selected_stat)
        ax2.set_title(f"{selected_stat} Over Time for {selected_player}")
        st.pyplot(fig2)
