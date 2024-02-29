import pandas as pd
import streamlit as st

@st.cache_data
def load_data(file_name):
    """Load data from a CSV file."""
    return pd.read_csv(file_name)

# Example usage:
# df = load_data('combined.csv')
