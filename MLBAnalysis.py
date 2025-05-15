import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Load data
hitters_path = 'data/baseball_data/combined_hitters_data.csv'
pitchers_path = 'data/baseball_data/combined_pitchers_data.csv'

hitters_df = pd.read_csv(hitters_path)
pitchers_df = pd.read_csv(pitchers_path)

# Function to convert 'Date' strings like 'Mar_30' to datetime with current year
def convert_to_date(date_str):
    try:
        return pd.to_datetime(f"{datetime.now().year} {date_str.replace('_', ' ')}", format='%Y %b %d')
    except Exception:
        return pd.NaT

# Apply date conversion
hitters_df['Date'] = hitters_df['Date'].apply(convert_to_date)
pitchers_df['Date'] = pitchers_df['Date'].apply(convert_to_date)

# Calculate Total Bases for hitters
for col in ['2B', '3B', 'HR', 'H']:
    hitters_df[col] = pd.to_numeric(hitters_df[col], errors='coerce')
hitters_df['1B'] = hitters_df['H'] - hitters_df['2B'] - hitters_df['3B'] - hitters_df['HR']
hitters_df['Total Bases'] = hitters_df['1B'] + 2 * hitters_df['2B'] + 3 * hitters_df['3B'] + 4 * hitters_df['HR']

# Streamlit app title
st.title("MLB Stat Viewer")

# Prepare min and max dates for date_input widgets (convert pandas Timestamp to datetime.date)
min_date = hitters_df['Date'].min()
max_date = hitters_df['Date'].max()
min_date = min_date.date() if pd.notna(min_date) else datetime.now().date()
max_date = max_date.date() if pd.notna(max_date) else datetime.now().date()

# Sidebar date inputs with bounds
start_date = st.sidebar.date_input("Start Date", min_value=min_date, value=min_date)
end_date = st.sidebar.date_input("End Date", max_value=max_date, value=max_date)

# Sidebar to select player type
player_type = st.sidebar.radio("Select Player Type", ["Hitters", "Pitchers"])

# Select dataset and stats dictionary based on player type
if player_type == "Hitters":
    df = hitters_df
    stats = {
        "Home Runs": "HR",
        "Runs Batted In": "RBI",
        "Stolen Bases": "SB",
        "Strikeouts": "SO",
        "Total Bases": "Total Bases"
    }
else:
    df = pitchers_df
    stats = {
        "Strikeouts": "SO",
        "Walks": "BB",
        "Hit By Pitch": "HBP",
        "Innings Pitched": "IP",
        "Hits Allowed": "H"
    }

# Get unique player list and select player
player_list = df['Player'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))

# Select stat
stat_label = st.sidebar.selectbox("Select a statistic:", list(stats.keys()))
selected_stat = stats[stat_label]

# Filter data by date range and player
df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]
player_df = df[df['Player'] == selected_player]

# Convert selected stat to numeric and drop missing values
player_df[selected_stat] = pd.to_numeric(player_df[selected_stat], errors='coerce')
player_df = player_df.dropna(subset=[selected_stat])

# Handle empty data
if player_df.empty:
    st.write("No data available for this player and date range.")
    st.stop()

# Determine threshold for coloring
max_val = player_df[selected_stat].max()
default_thresh = player_df[selected_stat].median()
threshold = st.sidebar.number_input("Set Threshold", min_value=0.0, max_value=float(max_val), value=float(default_thresh), step=0.5)

# Prepare data for pie chart
stat_counts = player_df[selected_stat].value_counts().sort_index()
labels = [f"{int(val)}" if val == int(val) else f"{val:.1f}" for val in stat_counts.index]
sizes = stat_counts.values

# Coloring logic for pie chart slices
colors = []
color_categories = {'green': 0, 'red': 0, 'gray': 0}
reverse_color = player_type == "Pitchers" and selected_stat in ["H", "BB", "HBP"]

for val, count in zip(stat_counts.index, stat_counts.values):
    if (val > threshold and not reverse_color) or (val < threshold and reverse_color):
        colors.append("green")
        color_categories["green"] += count
    elif (val < threshold and not reverse_color) or (val > threshold and reverse_color):
        colors.append("red")
        color_categories["red"] += count
    else:
        colors.append("gray")
        color_categories["gray"] += count

# Pie chart
fig1, ax1 = plt.subplots()
ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
ax1.axis('equal')
ax1.set_title(f"{stat_label} Distribution for {selected_player}")
st.pyplot(fig1)

# Pie chart color breakdown table
total_entries = sum(color_categories.values())
if total_entries > 0:
    st.markdown("**Pie Chart Color Breakdown:**")
    breakdown_df = pd.DataFrame({
        "Color": ["🟩 Green", "🟥 Red", "⬜ Gray"],
        "Category": [
            f"Above {threshold} {stat_label}" if not reverse_color else f"Below {threshold} {stat_label}",
            f"Below {threshold} {stat_label}" if not reverse_color else f"Above {threshold} {stat_label}",
            f"At {threshold} {stat_label}"
        ],
        "Count": [color_categories['green'], color_categories['red'], color_categories['gray']],
        "Percentage": [
            f"{color_categories['green'] / total_entries:.2%}",
            f"{color_categories['red'] / total_entries:.2%}",
            f"{color_categories['gray'] / total_entries:.2%}"
        ]
    })
    st.table(breakdown_df)

# Time-series bar chart of stat over time
st.subheader(f"{stat_label} Over Time for {selected_player}")
fig2, ax2 = plt.subplots(figsize=(12, 6))
data = player_df[['Date', selected_stat]].dropna()
bars = ax2.bar(data['Date'], data[selected_stat], color='gray', edgecolor='black')

count_above = 0
for bar, val in zip(bars, data[selected_stat]):
    if (val > threshold and not reverse_color) or (val < threshold and reverse_color):
        bar.set_color("green")
        count_above += 1
    elif (val < threshold and not reverse_color) or (val > threshold and reverse_color):
        bar.set_color("red")
    else:
        bar.set_color("gray")
        count_above += 1

ax2.axhline(y=threshold, color='blue', linestyle='--', linewidth=2, label=f"Threshold: {threshold}")
ax2.set_xlabel("Date")
ax2.set_ylabel(stat_label)
ax2.set_title(f"{stat_label} Over Time")
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
ax2.legend()
st.pyplot(fig2)

# Show proportion of games at or above threshold
total_games = len(data)
if total_games > 0:
    st.write(f"Games at or above threshold: {count_above}/{total_games} ({count_above / total_games:.2%})")
else:
    st.write("No data available for selected range.")
