import pandas as pd
import streamlit as st

@st.cache_data
def get_districts_in_region(data, selected_region):
    if selected_region != 'Overall':
        return list(data[data['Region'] == selected_region]['District'].unique())
    return list(data['District'].unique())

@st.cache_data
def get_clients_in_district_and_region(data, selected_district, selected_region):
    if selected_district != 'Overall' and selected_region != 'Overall':
        return list(data[(data['District'] == selected_district) & (data['Region'] == selected_region)]['Client'].unique())
    elif selected_district != 'Overall':
        return list(data[data['District'] == selected_district]['Client'].unique())
    elif selected_region != 'Overall':
        return list(data[data['Region'] == selected_region]['Client'].unique())
    return list(data['Client'].unique())

@st.cache_data
def filter_by_region(data, selected_region):
    if selected_region != 'Overall':
        return data[data['Region'] == selected_region]
    return data

@st.cache_data
def filter_by_district(data, selected_district):
    if selected_district != 'Overall':
        return data[data['District'] == selected_district]
    return data

@st.cache_data
def filter_by_date_range(data, date_range):
    # Ensure that the 'Event Time' column is in datetime format
    data['Event Time'] = pd.to_datetime(data['Event Time'])

    # Check if both date range values are provided
    if date_range and len(date_range) == 2 and date_range[0] and date_range[1]:
        start_date = pd.to_datetime(date_range[0]).date()
        end_date = pd.to_datetime(date_range[1]).date()
        # Filter the data
        return data[(data['Event Time'].dt.date >= start_date) & (data['Event Time'].dt.date <= end_date)]

    return data

@st.cache_data
def filter_by_clients(data, selected_clients):
    if selected_clients:
        return data[data['Client'].isin(selected_clients)]
    return data

def get_average_coordinates(data, selected_district):
    if selected_district != 'Overall':
        district_data = data[data['District'] == selected_district]
        avg_lat = district_data['Latitude'].mean()
        avg_lon = district_data['Longitude'].mean()
        return avg_lat, avg_lon
    return 23.6850, 90.3563  # Default coordinates for BD
