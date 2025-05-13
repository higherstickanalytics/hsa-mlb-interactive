import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# File paths
hitters_path = 'data/baseball_data/combined_hitters_data.csv'
pitchers_path = 'data/baseball_data/combined_pitchers_data.csv'
schedule_path = 'data/MLB_Schedule.csv'

# Load data
hitters_df = pd.read_csv(hitters_path)
pitchers_df = pd.read_csv(pitchers_path)
schedule_df = pd.read_csv(schedule_path, parse_dates=['Date'], dayfirst=False)

# App title
st.title("MLB Data Viewer")

# Sidebar: select position
position = st.sidebar.radio("Select Player Position", ['Hitters', 'Pitchers'])

# Clean column names
hitters_df.columns = [col.strip() for col in hitters_df.columns]
pitchers_df.columns = [col.strip() for col in pitchers_df.columns]

# Ensure 'Players' column exists in both datasets
if 'Players' not in hitters_df.columns or 'Players' not in pitchers_df.columns:
    st.error(f"'Players' column not found in the selected position data.")
    st.stop()

# Ensure 'Date' column is datetime in both datasets
if 'Date' in hitters_df.columns:
    hitters_df['Date'] = pd.to_datetime(hitters_df['Date'], errors='coerce')
    hitters_df = hitters_df.dropna(subset=['Date'])
else:
    st.error("Missing 'Date' column in hitters data.")
    st.stop()

if 'Date' in pitchers_df.columns:
    pitchers_df['Date'] = pd.to_datetime(pitchers_df['Date'], errors='coerce')
    pitchers_df = pitchers_df.dropna(subset=['Date'])
else:
    st.error("Missing 'Date' column in pitchers data.")
    st.stop()

# Filter valid players
if position == 'Hitters':
    df = hitters_df
else:
    df = pitchers_df

player_list = df['Players'].dropna().unique().tolist()
if not player_list:
    st.warning(f"No players found in the {position} data.")
    st.stop()

# Sidebar: player selection
selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))

# Sidebar: date filter
min_date = df['Date'].min()
max_date = df['Date'].max()
start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min_date, value=min_date))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", max_value=max_date, value=max_date))

# Filter data based on selected date range and player
df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
player_df = df_filtered[df_filtered['Players'] == selected_player]

# Display the filtered player's data
st.subheader(f"Data for {selected_player} ({position})")
st.dataframe(player_df)

# Stat selection (this can be customized based on your needs)
if position == 'Hitters':
    stat_options = ['BA', 'OBP', 'SLG', 'HR', 'RBI', 'SB', 'OPS']
else:
    stat_options = ['ERA', 'SO', 'SV', 'W', 'IP', 'WHIP', 'BB']

selected_stat = st.sidebar.selectbox("Select a statistic:", stat_options)

# Pie chart (distribution of selected stat)
st.subheader(f"{selected_stat} Distribution for {selected_player}")
stat_counts = player_df[selected_stat].value_counts().sort_index()
labels = [f"{int(val)}" if val == int(val) else f"{val:.1f}" for val in stat_counts.index]
sizes = stat_counts.values

# Color logic for pie chart
colors = []
for val, count in zip(stat_counts.index, stat_counts.values):
    if val > player_df[selected_stat].median():
        colors.append('green')
    elif val < player_df[selected_stat].median():
        colors.append('red')
    else:
        colors.append('gray')

fig1, ax1 = plt.subplots()
wedges, texts, autotexts = ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
                                   startangle=140, colors=colors, textprops={'fontsize': 10})
ax1.axis('equal')
ax1.set_title(f"{selected_stat} Distribution")
st.pyplot(fig1)

# Time-series plot for the selected stat over time
st.subheader(f"{selected_stat} Over Time for {selected_player}")
fig2, ax2 = plt.subplots(figsize=(12, 6))
data = player_df[['Date', selected_stat]].dropna()
ax2.plot(data['Date'], data[selected_stat], color='gray', marker='o')

ax2.set_xlabel("Date")
ax2.set_ylabel(selected_stat)
ax2.set_title(f"{selected_stat} Over Time")
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
st.pyplot(fig2)

# Summary: games at or above median value
total_games = len(data)
count_above_median = sum(data[selected_stat] > player_df[selected_stat].median())
if total_games > 0:
    st.write(f"Games at or above median {selected_stat}: {count_above_median}/{total_games} ({count_above_median / total_games:.2%})")
else:
    st.write("No data available in selected date range.")
