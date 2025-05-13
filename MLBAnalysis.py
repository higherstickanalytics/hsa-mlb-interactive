import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Paths to the files
hitters_path = 'data/baseball_data/combined_hitters_data.csv'
pitchers_path = 'data/baseball_data/combined_pitchers_data.csv'
schedule_path = 'data/MLB_Schedule.csv'

# Load the data
hitters_df = pd.read_csv(hitters_path)
pitchers_df = pd.read_csv(pitchers_path)
schedule_df = pd.read_csv(schedule_path, parse_dates=['Date'], dayfirst=False)

# Helper function to convert month-day format to full date (adding current year)
def convert_to_full_date(date_str):
    try:
        return pd.to_datetime(f"{datetime.now().year} {date_str}", format='%Y %b %d')
    except ValueError:
        return pd.NaT  # Return Not a Time (NaT) if conversion fails

# Apply the date conversion function
hitters_df['Date'] = hitters_df['Date'].apply(convert_to_full_date)
pitchers_df['Date'] = pitchers_df['Date'].apply(convert_to_full_date)
schedule_df['Date'] = schedule_df['Date'].apply(convert_to_full_date)

# Title of the app
st.title("MLB Data Viewer")

# Ensure min_date and max_date are valid dates
min_date = pd.to_datetime(hitters_df['Date'].min(), errors='coerce')
max_date = pd.to_datetime(hitters_df['Date'].max(), errors='coerce')

# If either min_date or max_date is NaT (invalid), set reasonable defaults
if pd.isna(min_date) or pd.isna(max_date):
    st.error("Invalid date values found in the dataset. Please check the data.")
    min_date = pd.to_datetime('2020-01-01')  # Set a default minimum date
    max_date = pd.to_datetime('2025-12-31')  # Set a default maximum date

# Sidebar: date filter
start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min_date, value=min_date))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", max_value=max_date, value=max_date))

# Sidebar: select player type
player_type = st.sidebar.radio("Select Player Type", ["Hitters", "Pitchers"])

# Select dataset based on player type
if player_type == "Hitters":
    df = hitters_df
    stats = ['BA', 'OBP', 'SLG', 'OPS', 'RBI', 'HR', 'SB']
    stat_names = ['Batting Average', 'On Base Percentage', 'Slugging Percentage', 'On-base Plus Slugging', 'Runs Batted In', 'Home Runs', 'Stolen Bases']
else:
    df = pitchers_df
    stats = ['ERA', 'SO', 'BB', 'HBP', 'SV']
    stat_names = ['Earned Run Average', 'Strikeouts', 'Walks', 'Hit By Pitch', 'Saves']

# Sidebar: player and stat selection
player_list = df['Players'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))
selected_stat_display = st.sidebar.selectbox("Select a statistic:", stat_names)
selected_stat = stats[stat_names.index(selected_stat_display)]

# Filter data based on selected dates and player
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
player_df = df[df['Players'] == selected_player]
player_df[selected_stat] = pd.to_numeric(player_df[selected_stat], errors='coerce').dropna()

# Histogram threshold
max_val = player_df[selected_stat].max()
default_thresh = player_df[selected_stat].median()
threshold = st.sidebar.number_input("Set Threshold", min_value=0.0, max_value=float(max_val), value=float(default_thresh), step=0.5)

# Pie Chart: Stat Distribution with threshold colors
st.subheader(f"{selected_stat_display} Distribution for {selected_player}")

stat_counts = player_df[selected_stat].value_counts().sort_index()
labels = [f"{int(val)}" if val == int(val) else f"{val:.1f}" for val in stat_counts.index]
sizes = stat_counts.values

# Assign red for below threshold, green for above, gray for equal
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
wedges, texts, autotexts = ax1.pie(
    sizes,
    labels=labels,
    autopct='%1.1f%%',
    startangle=140,
    colors=colors,
    textprops={'fontsize': 10}
)
ax1.axis('equal')
ax1.set_title(f"{selected_stat_display} Value Distribution")
st.pyplot(fig1)

# Display color category percentages in a cleaner table format
total_entries = sum(color_categories.values())
if total_entries > 0:
    st.markdown("**Pie Chart Color Breakdown:**")
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
    breakdown_df = pd.DataFrame(breakdown_data)
    st.table(breakdown_df)
else:
    st.write("No data available to display pie chart.")

# Time-Series Histogram
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

# Proportion summary
total_games = len(data)
if total_games > 0:
    st.write(f"Games at or above threshold: {count_above}/{total_games} ({count_above / total_games:.2%})")
else:
    st.write("No data available in selected date range.")
