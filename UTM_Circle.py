import streamlit as st
import pyproj
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- Circle generation function ---
def generate_circle_from_utm(easting, northing, utm_zone=31, radius_m=50, num_points=17, apply_epoch_correction=False):
    utm_crs = f"EPSG:{32600 + utm_zone}"
    transformer = pyproj.Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True)

    # Epoch correction
    if apply_epoch_correction:
        years_since_1984 = 2025.5 - 1984.0
        easting += 0.025 * years_since_1984
        northing += 0.015 * years_since_1984

    angles_deg = np.linspace(0, 360, num_points)
    angles_rad = np.radians(angles_deg)
    eastings = easting + radius_m * np.cos(angles_rad)
    northings = northing + radius_m * np.sin(angles_rad)
    lons, lats = transformer.transform(np.array(eastings), np.array(northings))
    center_lon, center_lat = transformer.transform(easting, northing)

    df = pd.DataFrame({
        "Angle (°)": np.round(angles_deg, 6),
        "Latitude": np.round(lats, 10),
        "Longitude": np.round(lons, 10),
        "Center Latitude": round(center_lat, 10),
        "Center Longitude": round(center_lon, 10)
    })
    return df, center_lat, center_lon

# --- Streamlit UI ---
st.title("Multiple UTM Circles to WGS84")
st.write("Generate multiple WGS84 circles from UTM centers with radius and epoch correction.")

num_circles = st.number_input("Number of Circles", min_value=1, max_value=10, value=1)
utm_zone = st.number_input("UTM Zone", min_value=1, max_value=60, value=31)
radius_m = st.number_input("Radius (m)", value=50)
num_points = st.number_input("Points per Circle", min_value=3, value=17)
apply_correction = st.checkbox("Apply Epoch 2025.5 Correction", value=True)

# Use form to preserve input state
with st.form("circle_form"):
    circle_inputs = []
    for i in range(num_circles):
        with st.expander(f"Circle {i+1} Input"):
            e = st.number_input(f"Easting {i+1}", key=f"e_{i}")
            n = st.number_input(f"Northing {i+1}", key=f"n_{i}")
            circle_inputs.append((e, n))
    submit = st.form_submit_button("Generate Circles")

# On form submit
if submit:
    all_circles = []
    map_center = [0, 0]
    m = folium.Map(location=[0, 0], zoom_start=2)

    for idx, (e, n) in enumerate(circle_inputs):
        circle_df, lat_c, lon_c = generate_circle_from_utm(e, n, utm_zone, radius_m, num_points, apply_epoch_correction=apply_correction)
        circle_df["Circle ID"] = f"Circle {idx+1}"
        all_circles.append(circle_df)

        # Draw on map
        folium.PolyLine(
            locations=list(zip(circle_df["Latitude"], circle_df["Longitude"])),
            color="blue", weight=2, tooltip=f"Circle {idx+1}"
        ).add_to(m)
        folium.Marker(
            location=[lat_c, lon_c],
            popup=f"Center {idx+1}",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    combined_df = pd.concat(all_circles, ignore_index=True)
    st.success(f"{num_circles} circle(s) generated.")
    st.markdown("### Circle Coordinates")
    st.dataframe(combined_df)

    # Column copy interface
    st.markdown("### 📋 Copy a Column")
    column_to_copy = st.selectbox("Select column to copy", combined_df.columns)
    st.text_area("Copy below:", "\n".join(map(str, combined_df[column_to_copy].tolist())), height=200)

    # Map display
    center_lat = combined_df["Center Latitude"].iloc[0]
    center_lon = combined_df["Center Longitude"].iloc[0]
    m.location = [center_lat, center_lon]
    st_folium(m, width=700, height=500)

    # Download
    csv = combined_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "multi_circle_points.csv", "text/csv")
