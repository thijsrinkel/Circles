import streamlit as st
import pyproj
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium

def generate_circle_from_utm(easting, northing, utm_zone=31, radius_m=50, num_points=17, apply_epoch_correction=False):
    utm_crs = f"EPSG:{32600 + utm_zone}"
    transformer = pyproj.Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True)

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

# --- Streamlit App ---
st.title("UTM Circles to WGS84 (Stable Map Version)")

st.markdown(
    "Paste UTM coordinates (Easting, Northing) below, one pair per line, comma- or space-separated. "
    "Example:\n465177.689,5708543.612\n465154.25 5708490.11"
)

coord_text = st.text_area("Input Coordinates", height=200)
utm_zone = st.number_input("UTM Zone", min_value=1, max_value=60, value=31)
radius_m = st.number_input("Circle Radius (m)", value=50)
num_points = st.number_input("Points per Circle", min_value=3, value=17)
apply_correction = st.checkbox("Apply Epoch 2025.5 Correction", value=True)

if st.button("Generate Circles"):
    lines = coord_text.strip().splitlines()
    coords = []

    for line in lines:
        parts = line.replace(",", " ").split()
        if len(parts) == 2:
            try:
                e, n = float(parts[0]), float(parts[1])
                coords.append((e, n))
            except ValueError:
                st.error(f"Invalid numbers in line: {line}")
        else:
            st.error(f"Line ignored (wrong format): {line}")

    if coords:
        all_circles = []
        first_latlon = None

        for idx, (e, n) in enumerate(coords):
            circle_df, lat_c, lon_c = generate_circle_from_utm(
                e, n, utm_zone, radius_m, num_points, apply_epoch_correction=apply_correction
            )
            circle_df["Circle ID"] = f"Circle {idx+1}"
            all_circles.append(circle_df)
            if first_latlon is None:
                first_latlon = [lat_c, lon_c]

        combined_df = pd.concat(all_circles, ignore_index=True)
        st.success(f"{len(coords)} circle(s) generated.")
        st.markdown("### Circle Coordinates")
        st.dataframe(combined_df)

        st.markdown("### 📋 Copy a Column")
        col_to_copy = st.selectbox("Select column to copy", combined_df.columns)
        st.text_area("Copy below:", "\n".join(map(str, combined_df[col_to_copy].tolist())), height=200)

        # Initialize the map once with real center
        m = folium.Map(location=first_latlon, zoom_start=17)

        for idx, (e, n) in enumerate(coords):
            circle_df, lat_c, lon_c = generate_circle_from_utm(
                e, n, utm_zone, radius_m, num_points, apply_epoch_correction=apply_correction
            )
            folium.PolyLine(
                locations=list(zip(circle_df["Latitude"], circle_df["Longitude"])),
                color="blue", weight=2, tooltip=f"Circle {idx+1}"
            ).add_to(m)

            folium.Marker(
                location=[lat_c, lon_c],
                popup=f"Center {idx+1}",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)

        st_folium(m, width=700, height=500)

        csv = combined_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "circle_points.csv", "text/csv")
