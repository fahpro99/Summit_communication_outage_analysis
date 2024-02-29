import folium
from folium.plugins import MarkerCluster, HeatMap
from folium.features import GeoJson
import json
import streamlit as st
from filters import get_average_coordinates
import altair as alt
import pandas as pd

# Regular function to replace lambda
def style_function(feature):
    return {
        'fillColor': 'blue',
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.3
    }

@st.cache_data
def create_folium_map(data, selected_district, geo_json_path='bd_jeoson.json'):
    avg_lat, avg_lon = get_average_coordinates(data, selected_district)
    zoom_start = 11 if selected_district != 'Overall' else 6

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=zoom_start)

    # Load GeoJSON data
    geo_json_data = json.load(open(geo_json_path, 'r'))

    # Create GeoJson layer with the style_function
    geojson = GeoJson(
        geo_json_data,
        name="geojson",
        style_function=style_function  # Using regular function instead of lambda
    )

    # Add GeoJson layer to map
    geojson.add_to(m)

    # Extract GeoJSON features and create a list of (latitude, longitude) for heatmap
    heat_data = []
    for feature in geo_json_data['features']:
        geometry = feature['geometry']
        if geometry['type'] == 'Polygon':
            coordinates = geometry['coordinates'][0]  # Extract coordinates for the first ring
            heat_data.extend(coordinates)
        elif geometry['type'] == 'MultiPolygon':
            for polygon_coordinates in geometry['coordinates']:
                heat_data.extend(polygon_coordinates[0])

    # Add HeatMap layer with the GeoJSON geometry data
    HeatMap(heat_data).add_to(m)

    # Add Marker Cluster layer
    marker_cluster = MarkerCluster().add_to(m)

    # Add markers for each incident with tooltip
    for _, row in data.iterrows():
        tooltip_text = f"Time: {row['Event Time']}<br>Client: {row['Client']}<br>District: {row['District']}"
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            tooltip=tooltip_text
        ).add_to(marker_cluster)

    folium.LayerControl().add_to(m)

    return m

def display_total_count(filtered_df):
    total_count = len(filtered_df)
    st.sidebar.markdown(f"<p style='font-size:22px; color:white;'>Total Count: <strong>{total_count}</strong></p>", unsafe_allow_html=True)

def generate_bar_chart(data, district):
    # Filter the data for the specified district if necessary
    if district != 'Overall':
        data = data[data['District'] == district]

    # Calculate the frequency of each reason
    reason_counts = data['Reason'].value_counts().reset_index()
    reason_counts.columns = ['Reason', 'Count']

    # Select the top 10 reasons
    top_reasons = reason_counts.head(10)

    # Create the bar chart using Altair
    chart = alt.Chart(top_reasons).mark_bar().encode(
        x=alt.X('Reason:N', sort='-y'),  # Sort bars by count
        y='Count:Q',
        color=alt.Color('Reason:N', scale=alt.Scale(scheme='viridis')),
        tooltip=['Reason', 'Count']
    ).properties(
        title=f'Top 10 Outage Reasons{" in " + district if district != "Overall" else ""}',
        width=700,
        height=400
    )

    return chart

def generate_outage_time_graph(data, selected_clients):
    if 'Overall' in selected_clients or not selected_clients:
        return None

    client_data = data[data['Client'].isin(selected_clients)]

    # Convert 'Event Time' to 12-hour format with AM/PM
    client_data['Hour_AM_PM'] = client_data['Event Time'].dt.strftime('%I %p').str.lstrip('0').replace(' 12 PM', ' 00 PM').replace(' 12 AM', ' 00 AM')

    # Create a custom sorting order for the hours, starting with '12 AM' up to '11 PM'
    hours_ordered = ['12 AM'] + [f"{i} AM" for i in range(1, 12)] + ['12 PM'] + [f"{i} PM" for i in range(1, 12)]

    # Apply the custom sorting order to the data
    client_data['Hour_AM_PM'] = pd.Categorical(client_data['Hour_AM_PM'], categories=hours_ordered, ordered=True)

    # Group by client and hour, then count occurrences
    client_hourly_counts = client_data.groupby(['Client', 'Hour_AM_PM']).size().reset_index(name='Count')

    # Sort the dataframe by the 'Hour_AM_PM' column to ensure the custom order is applied
    client_hourly_counts.sort_values('Hour_AM_PM', inplace=True)

    chart = alt.Chart(client_hourly_counts).mark_bar().encode(
        x=alt.X('Hour_AM_PM:N', sort=None),
        y=alt.Y('Count:Q', axis=alt.Axis(title='Count')),
        color=alt.Color('Client:N', scale=alt.Scale(scheme='inferno')),  # Applying the 'inferno' color scheme
        tooltip=['Client', 'Hour_AM_PM', 'Count']
    ).properties(
        title='Outage Frequency by Client and Time',
        width=700,
        height=400
    )

    return chart




