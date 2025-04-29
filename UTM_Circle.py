import streamlit as st
import pyproj
import numpy as np
import pandas as pd

# Define the circle generation function (updated using pyproj.Transformer)
def generate_circle_from_utm(easting, northing, utm_zone=31, radius_m=50, num_points=17, apply_epoch_correction=False):
    utm_crs = f"+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    transformer = pyproj.Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True)

    lon, lat = transformer.transform(easting, northing)

    # Apply approximate epoch correction if needed (assume 2.5 cm/year eastward, 1.5 cm/year northward for Europe)
    if apply_epoch_correction:
        years_since_1984 = 2025.5 - 1984.0
        east_shift_m = 0.025 * years_since_1984  # meters
        north_shift_m = 0.015 * years_since_1984  # meters

        deg_per_meter = 1 / 111320
        lat += north_shift_m * deg_per_meter
        lon += east_shift_m * deg_per_meter

    angles_deg = np.linspace(0, 360, num_points)
    angles_rad = np.radians(angles_deg)
    deg_per_meter = 1 / 111320
    lat_offset = deg_per_meter * np.sin(angles_rad) * radius_m
    lon_offset = deg_per_meter * np.cos(angles_rad) * radius_m

    latitudes = lat + lat_offset
    longitudes = lon + lon_offset

    return pd.DataFrame({
        "Angle (°)": angles_deg,
        "Latitude": latitudes,
        "Longitude": longitudes
    })

# Streamlit UI
st.title("UTM to WGS84 Circle Generator")
st.write("This tool converts a UTM coordinate to WGS84 and generates a circle of points around it.")

# Input fields
easting = st.number_input("Enter Easting (meters):", value=465177.689)
northing = st.number_input("Enter Northing (meters):", value=5708543.612)
utm_zone = st.number_input("Enter UTM Zone:", min_value=1, max_value=60, value=31)
radius_m = st.number_input("Enter Radius (meters):", value=50)
num_points = st.number_input("Number of Points:", min_value=3, value=17)
apply_correction = st.checkbox("Apply Epoch 2025.5 Correction?", value=False)

if st.button("Generate Circle"):
    circle_df = generate_circle_from_utm(easting, northing, utm_zone, radius_m, num_points, apply_epoch_correction=apply_correction)
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
