import requests
import datetime
import streamlit as st
from data_loading import load_data

from filters import (
    get_districts_in_region,
    get_clients_in_district_and_region,
    filter_by_region,
    filter_by_district,
    filter_by_date_range,
    filter_by_clients
)
from visualization import (
    create_folium_map,
    display_total_count,
    generate_bar_chart,
    generate_outage_time_graph
)
import pandas as pd
import altair as alt
from streamlit_folium import folium_static
# Path to your logo and target URL

# Path to your logo and target URL
logo_path = 'logo.png'
target_url = 'https://www.summitcommunications.net/'

# Display the logo
st.sidebar.image(logo_path, width=250)


def get_weather(city, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code.
        return response.json()
    except requests.exceptions.HTTPError as errh:
        st.sidebar.write("HTTP Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        st.sidebar.write("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        st.sidebar.write("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        st.sidebar.write("Error:", err)
    return None


# Function to display weather
def display_weather(weather_data):
    if weather_data:
        temp = weather_data['main']['temp']
        weather_description = weather_data['weather'][0]['description'].capitalize()


        # Optionally, add an emoji or icon based on the weather description
        weather_icons = {
            "Clear": "☀️",
            "Clouds": "☁️",
            "Rain": "🌧️",
            "Snow": "❄️",
            "Thunderstorm": "⛈️",
            "Drizzle": "🌦️",
            "Mist": "🌫️"
        }
        weather_main = weather_data['weather'][0]['main']
        icon = weather_icons.get(weather_main, "")
        st.sidebar.markdown(f"#### **Current Temperature:** {temp}°C")
        st.sidebar.markdown(f"#### **Weather:** {weather_description}  {icon}")


# Your OpenWeatherMap API key
api_key = "6e9d76b662e4cbf91a2fabe38bd53138"

# Assuming you want to display the weather for a specific city
city = "Dhaka"  # Replace with your city of interest

# Get current date and time
current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Using Markdown for formatting and adding an emoji
st.sidebar.markdown(f"#### 🕒 **Current Date and Time:**\n`{current_date}`")


# Fetch and display weather
weather_data = get_weather(city, api_key)
display_weather(weather_data)





# Load the data
df = load_data('final_csv.csv')

# Convert 'Event Time' column to datetime
df['Event Time'] = pd.to_datetime(df['Event Time'])

# Count the frequency of each district, region, and client
district_counts = df['District'].value_counts().reset_index()
district_counts.columns = ['District', 'Count']
region_counts = df['Region'].value_counts().reset_index()
region_counts.columns = ['Region', 'Count']
client_counts = df['Client'].value_counts().reset_index()
client_counts.columns = ['Client', 'Count']

# Define the custom order for regions
custom_region_order = ['RIO-1', 'RIO-2', 'RIO-3', 'RIO-4']
# Sort the regions based on the custom order
sorted_regions = sorted(region_counts['Region'].unique(), key=lambda x: custom_region_order.index(x) if x in custom_region_order else float('inf'))

# Streamlit app title
st.title("SComm Network Outages in Bangladesh")

# Sidebar widgets for selecting region, district, and clients
selected_region = st.sidebar.radio("Select a Region", ['Overall'] + sorted_regions)
districts_in_selected_region = get_districts_in_region(df, selected_region)
selected_district = st.sidebar.selectbox("Select a District", ['Overall'] + districts_in_selected_region)

clients_in_selected_district_and_region = get_clients_in_district_and_region(df, selected_district, selected_region)
sorted_clients = sorted([str(client) if client is not None else "" for client in clients_in_selected_district_and_region])

selected_clients = st.sidebar.multiselect("Select Clients", ['Overall'] + sorted_clients)

date_range = st.sidebar.date_input("Select Date Range", [df['Event Time'].min(), df['Event Time'].max()], key="daterange")

# Apply filters
filtered_data = filter_by_region(df, selected_region)
filtered_data = filter_by_district(filtered_data, selected_district)
filtered_data = filter_by_date_range(filtered_data, date_range)
filtered_data = filter_by_clients(filtered_data, selected_clients)

# Display total count based on the applied filters
display_total_count(filtered_data)

# Button for loading the map
if st.button('Load Map'):
    # Create and display Folium map
    folium_map = create_folium_map(filtered_data, selected_district)
    folium_static(folium_map)
else:
    # Display a placeholder or message
    st.write("Click the button above to load the map.")

# Display the bar chart for the selected district or overall
if selected_district != 'Overall':
    st.subheader(f'Outage Reasons in {selected_district}')
    bar_chart = generate_bar_chart(filtered_data, selected_district)
    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.subheader('Outage Reasons Overall')
    overall_bar_chart = generate_bar_chart(filtered_data, 'Overall')
    st.altair_chart(overall_bar_chart, use_container_width=True)

# Check if specific clients are selected
if not selected_clients or 'Overall' in selected_clients:
    st.subheader("No specific client is selected.")
else:
    # Display the outage-time graph for selected clients
    client_outage_time_graph = generate_outage_time_graph(filtered_data, selected_clients)
    if client_outage_time_graph:
        st.altair_chart(client_outage_time_graph, use_container_width=True)

# Convert 'Event Time' to datetime if not already
filtered_data['Event Time'] = pd.to_datetime(filtered_data['Event Time'])

# Resample and count occurrences by month and client
time_series_data_client = filtered_data.groupby(['Client']).resample('ME', on='Event Time').size().reset_index(name='Counts')

# Convert the 'Event Time' to a more readable format, like 'YYYY-MM'
time_series_data_client['Month'] = time_series_data_client['Event Time'].dt.strftime('%Y-%m')

# Create the time series line chart
time_series_chart = alt.Chart(time_series_data_client).mark_line().encode(
    x=alt.X('Month:T', axis=alt.Axis(title='Month')),
    y=alt.Y('Counts:Q', axis=alt.Axis(title='Event Counts')),
    color='Client:N',
    tooltip=['Client', 'Month', 'Counts']
).properties(
    title='Monthly Event Frequency by Client',
    width=700,
    height=400
)

# Display the chart
st.altair_chart(time_series_chart, use_container_width=True)

# Distribution analysis by Region
region_chart_filtered = alt.Chart(filtered_data).mark_bar().encode(
    x='Region:N',
    y='count():Q',
    color='Region:N'
).properties(
    title='Distribution of Events by Region (Filtered Data)',
    width=700,
    height=400
)

st.altair_chart(region_chart_filtered, use_container_width=True)

# Select the top 10 clients by count
top_clients = client_counts.head(10)

# Filter the original data for only the top 10 clients
filtered_top_clients_data = filtered_data[filtered_data['Client'].isin(top_clients['Client'])]

# Create the bar chart with the filtered data
client_chart_filtered = alt.Chart(filtered_top_clients_data).mark_bar().encode(
    x=alt.X('Client:N', sort='-y'),  # Sort by the count in descending order
    y=alt.Y('count():Q', title='Frequency of Events')
).properties(
    title='Frequency of Events by Client (Filtered Data)',
    width=700,
    height=400
)

# Display the chart in a Streamlit application
st.altair_chart(client_chart_filtered, use_container_width=True)
