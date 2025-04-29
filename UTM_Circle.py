import streamlit as st
import pyproj
import numpy as np
import pandas as pd

# Define the correct circle generation function (stay in UTM and then transform)
def generate_circle_from_utm(easting, northing, utm_zone=31, radius_m=50, num_points=17, apply_epoch_correction=False):
    utm_crs = f"+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    transformer = pyproj.Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True)

    # Apply approximate epoch correction if needed (assume 2.5 cm/year eastward, 1.5 cm/year northward for Europe)
    if apply_epoch_correction:
        years_since_1984 = 2025.5 - 1984.0
        east_shift_m = 0.025 * years_since_1984  # meters
        north_shift_m = 0.015 * years_since_1984  # meters
        easting += east_shift_m
        northing += north_shift_m

    angles_deg = np.linspace(0, 360, num_points)
    angles_rad = np.radians(angles_deg)

    # Generate points directly in UTM meters
    eastings = easting + radius_m * np.cos(angles_rad)
    northings = northing + radius_m * np.sin(angles_rad)

    # Transform all UTM points to WGS84 lat/lon
    lons, lats = transformer.transform(eastings, northings)

    return pd.DataFrame({
        "Angle (°)": np.round(angles_deg, 6),
        "Latitude": np.round(lats, 10),
        "Longitude": np.round(lons, 10)
    })

# Streamlit UI
st.title("UTM to WGS84 Circle Generator")
st.write("This tool converts a UTM coordinate to WGS84 and generates a true circle of points around it.")

# Input fields
easting = st.number_input("Enter Easting (meters):", value=465177.689)
northing = st.number_input("Enter Northing (meters):", value=5708543.612)
utm_zone = st.number_input("Enter UTM Zone:", min_value=1, max_value=60, value=31)
radius_m = st.number_input("Enter Radius (meters):", value=50)
num_points = st.number_input("Number of Points:", min_value=3, value=17)
apply_correction = st.checkbox("Apply Epoch 2025.5 Correction?", value=False)

if st.button("Generate Circle"):
    circle_df = generate_circle_from_utm(easting, northing, utm_zone, radius_m, num_points, apply_epoch_correction=apply_correction)
    # Add first point again to close the circle
    circle_df = pd.concat([circle_df, circle_df.iloc[[0]]], ignore_index=True)
    
    st.success("Circle points generated!")
    st.dataframe(circle_df)

    # Download as CSV
    csv = circle_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Circle Points as CSV",
        data=csv,
        file_name='circle_points.csv',
        mime='text/csv'
    )

