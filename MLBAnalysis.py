import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Load data
hitters_path = 'data/baseball_data/combined_hitters_data.csv'
pitchers_path = 'data/baseball_data/combined_pitchers_data.csv'

# Read CSVs
hitters_df = pd.read_csv(hitters_path)
pitchers_df = pd.read_csv(pitchers_path)

# Helper: Convert 'Mar_30' to datetime
def convert_date(date_str):
    try:
        return pd.to_datetime(f"{datetime.now().year} {date_str.replace('_', ' ')}", format='%Y %b %d')
    except:
        return pd.NaT

# Apply date conversion
hitters_df['Date'] = hitters_df['Date'].apply(convert_date)
pitchers_df['Date'] = pitchers_df['Date'].apply(convert_date)

# Add Total Bases for hitters: 1B + 2*2B + 3*3B + 4*HR
for col in ['2B', '3B', 'HR', 'H']:
    hitters_df[col] = pd.to_numeric(hitters_df[col], errors='coerce').fillna(0)
hitters_df['1B'] = hitters_df['H'] - hitters_df['2B'] - hitters_df['3B'] - hitters_df['HR']
hitters_df['Total Bases'] = hitters_df['1B'] + 2*hitters_df['2B'] + 3*hitters_df['3B'] + 4*hitters_df['HR']

# Streamlit app
st.title("MLB Player Stat Viewer")

# Date filters
min_date = pd.to_datetime(hitters_df['Date'].min())
max_date = pd.to_datetime(hitters_df['Date'].max())
start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min_date, value=min_date))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", max_value=max_date, value=max_date))

# Player type
player_type = st.sidebar.radio("Select Player Type", ["Hitters", "Pitchers"])

if player_type == "Hitters":
    df = hitters_df
    stat_options = ['HR', 'RBI', 'SB', 'SO', 'Total Bases']
else:
    df = pitchers_df
    stat_options = ['SO', 'BB', 'HBP', 'IP', 'H']  # Lower is better for BB, HBP, H

# Player and stat selection
player_list = df['Players'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))
selected_stat = st.sidebar.selectbox("Select a statistic:", stat_options)

# Filter
df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
player_df = df[df['Players'] == selected_player]
player_df[selected_stat] = pd.to_numeric(player_df[selected_stat], errors='coerce')

# Threshold input
max_val = player_df[selected_stat].max()
default_thresh = player_df[selected_stat].median()
threshold = st.sidebar.number_input("Set Threshold", min_value=0.0, max_value=float(max_val), value=float(default_thresh), step=0.5)

# Pie Chart
st.subheader(f"{selected_stat} Distribution for {selected_player}")
stat_counts = player_df[selected_stat].value_counts().sort_index()
labels = [f"{int(v)}" if v == int(v) else f"{v:.1f}" for v in stat_counts.index]
sizes = stat_counts.values

# Color logic (lower is better for some pitcher stats)
lower_better = player_type == "Pitchers" and selected_stat in ['BB', 'HBP', 'H']
colors = []
color_categories = {'green': 0, 'red': 0, 'gray': 0}
for val, count in zip(stat_counts.index, stat_counts.values):
    if (val < threshold and lower_better) or (val > threshold and not lower_better):
        colors.append('green')
        color_categories['green'] += count
    elif (val > threshold and lower_better) or (val < threshold and not lower_better):
        colors.append('red')
        color_categories['red'] += count
    else:
        colors.append('gray')
        color_categories['gray'] += count

# Plot pie chart
fig1, ax1 = plt.subplots()
ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10})
ax1.axis('equal')
st.pyplot(fig1)

# Pie chart breakdown
total = sum(color_categories.values())
if total > 0:
    st.markdown("**Pie Chart Color Breakdown**")
    breakdown = pd.DataFrame({
        'Color': ['🟩 Green', '🟥 Red', '⬜ Gray'],
        'Category': [
            'Better than threshold' if not lower_better else 'Lower than threshold',
            'Worse than threshold' if not lower_better else 'Higher than threshold',
            'At threshold'
        ],
        'Count': [color_categories['green'], color_categories['red'], color_categories['gray']],
        'Percentage': [f"{v/total:.2%}" for v in color_categories.values()]
    })
    st.table(breakdown)
else:
    st.write("No data to display.")

# Time Series Chart
st.subheader(f"{selected_stat} Over Time for {selected_player}")
data = player_df[['Date', selected_stat]].dropna()
fig2, ax2 = plt.subplots(figsize=(12, 6))
bars = ax2.bar(data['Date'], data[selected_stat], color='gray', edgecolor='black')

count_above = 0
for bar, val in zip(bars, data[selected_stat]):
    if (val < threshold and lower_better) or (val > threshold and not lower_better):
        bar.set_color('green')
        count_above += 1
    elif val == threshold:
        bar.set_color('gray')
        count_above += 1
    else:
        bar.set_color('red')

ax2.axhline(y=threshold, color='blue', linestyle='--', linewidth=2, label=f'Threshold: {threshold}')
ax2.set_title(f"{selected_stat} Over Time")
ax2.set_xlabel("Date")
ax2.set_ylabel(selected_stat)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
ax2.legend()
st.pyplot(fig2)

# Summary
games = len(data)
if games > 0:
    st.write(f"Games at or {'below' if lower_better else 'above'} threshold: {count_above}/{games} ({count_above/games:.2%})")
else:
    st.write("No data in date range.")
