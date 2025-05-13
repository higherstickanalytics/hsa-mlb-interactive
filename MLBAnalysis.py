import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# File paths
hitters_path = 'data/baseball_data/combined_hitters_data.csv'
pitchers_path = 'data/baseball_data/combined_pitchers_data.csv'
schedule_path = 'data/MLB_Schedule.csv'

# Load data
hitters_df = pd.read_csv(hitters_path)
pitchers_df = pd.read_csv(pitchers_path)
schedule_df = pd.read_csv(schedule_path, parse_dates=['Date'], dayfirst=False)

# Convert Date from strings like "Mar 28" to full dates
def convert_to_full_date(date_str):
    try:
        return pd.to_datetime(f"{datetime.now().year} {date_str}", format='%Y %b %d')
    except:
        return pd.NaT

# Apply to datasets
hitters_df['Date'] = hitters_df['Date'].apply(convert_to_full_date)
pitchers_df['Date'] = pitchers_df['Date'].apply(convert_to_full_date)
schedule_df['Date'] = schedule_df['Date'].apply(convert_to_full_date)

# Add Total Bases to hitters
for col in ['2B', '3B', 'HR', 'H']:
    if col not in hitters_df.columns:
        hitters_df[col] = 0
hitters_df['1B'] = hitters_df['H'] - hitters_df['2B'] - hitters_df['3B'] - hitters_df['HR']
hitters_df['TB'] = hitters_df['1B'] + 2*hitters_df['2B'] + 3*hitters_df['3B'] + 4*hitters_df['HR']

# App title
st.title("MLB Data Viewer (Counts Only)")

# Ensure valid date ranges
min_date = pd.to_datetime(hitters_df['Date'].min(), errors='coerce')
max_date = pd.to_datetime(hitters_df['Date'].max(), errors='coerce')

if pd.isna(min_date) or pd.isna(max_date):
    st.error("Invalid dates found in dataset.")
    min_date = pd.to_datetime('2020-01-01')
    max_date = pd.to_datetime('2025-12-31')

# Sidebar: date filter
start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min_date, value=min_date))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", max_value=max_date, value=max_date))

# Sidebar: player type
player_type = st.sidebar.radio("Select Player Type", ["Hitters", "Pitchers"])

# Stat options
if player_type == "Hitters":
    df = hitters_df
    stats = ['TB', 'HR', 'RBI', 'SB', 'SO']
    stat_names = ['Total Bases', 'Home Runs', 'Runs Batted In', 'Stolen Bases', 'Strikeouts']
else:
    df = pitchers_df
    stats = ['SO', 'BB', 'HBP', 'IP', 'H', 'BF', 'Pit']
    stat_names = ['Strikeouts', 'Walks', 'Hit By Pitch', 'Innings Pitched', 'Hits', 'Batters Faced', 'Pitches Thrown']

# Sidebar: player and stat
player_list = df['Players'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))
selected_stat_display = st.sidebar.selectbox("Select a statistic:", stat_names)
selected_stat = stats[stat_names.index(selected_stat_display)]

# Filter player data
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
player_df = df[df['Players'] == selected_player].copy()
player_df[selected_stat] = pd.to_numeric(player_df[selected_stat], errors='coerce').dropna()

# Threshold
max_val = player_df[selected_stat].max()
default_thresh = player_df[selected_stat].median()
threshold = st.sidebar.number_input("Set Threshold", min_value=0.0, max_value=float(max_val), value=float(default_thresh), step=0.5)

# --- PIE CHART ---
st.subheader(f"{selected_stat_display} Distribution for {selected_player}")
stat_counts = player_df[selected_stat].value_counts().sort_index()
labels = [f"{int(val)}" if val == int(val) else f"{val:.1f}" for val in stat_counts.index]
sizes = stat_counts.values

colors = []
color_categories = {'green': 0, 'red': 0, 'gray': 0}
for val, count in zip(stat_counts.index, stat_counts.values):
    if val > threshold:
        colors.append('green')
        color_categories['green'] += count
    elif val < threshold:
        colors.append('red')
        color_categories['red'] += count
    else:
        colors.append('gray')
        color_categories['gray'] += count

fig1, ax1 = plt.subplots()
ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 10})
ax1.axis('equal')
ax1.set_title(f"{selected_stat_display} Value Distribution")
st.pyplot(fig1)

# Pie chart breakdown
total_entries = sum(color_categories.values())
if total_entries > 0:
    breakdown_data = {
        'Color': ['🟩 Green', '🟥 Red', '⬜ Gray'],
        'Category': [
            f"Above {threshold} {selected_stat_display}",
            f"Below {threshold} {selected_stat_display}",
            f"At {threshold} {selected_stat_display}"
        ],
        'Count': [color_categories['green'], color_categories['red'], color_categories['gray']],
        'Percentage': [
            f"{color_categories['green'] / total_entries:.2%}",
            f"{color_categories['red'] / total_entries:.2%}",
            f"{color_categories['gray'] / total_entries:.2%}"
        ]
    }
    st.table(pd.DataFrame(breakdown_data))
else:
    st.write("No data available to display pie chart.")

# --- TIME SERIES ---
st.subheader(f"{selected_stat_display} Over Time for {selected_player}")
fig2, ax2 = plt.subplots(figsize=(12, 6))
data = player_df[['Date', selected_stat]].dropna()
bars = ax2.bar(data['Date'], data[selected_stat], color='gray', edgecolor='black')

count_above = 0
for bar, val in zip(bars, data[selected_stat]):
    if val > threshold:
        bar.set_color('green')
        count_above += 1
    elif val < threshold:
        bar.set_color('red')
    else:
        bar.set_color('gray')
        count_above += 1

ax2.axhline(y=threshold, color='blue', linestyle='--', linewidth=2, label=f'Threshold: {threshold}')
ax2.set_xlabel("Date")
ax2.set_ylabel(selected_stat_display)
ax2.set_title(f"{selected_stat_display} Over Time")
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
ax2.legend()
st.pyplot(fig2)

# Summary
total_games = len(data)
if total_games > 0:
    st.write(f"Games at or above threshold: {count_above}/{total_games} ({count_above / total_games:.2%})")
else:
    st.write("No data available in selected date range.")
