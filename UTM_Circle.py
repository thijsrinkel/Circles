import streamlit as st
import pyproj
import numpy as np
import pandas as pd

# --- Circle generation function ---
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
        "Longitude": np.round(lons, 10)
    })
    return df, round(center_lat, 10), round(center_lon, 10)

# --- Streamlit App ---
st.title("UTM Circles to WGS84 (Stable Final Version)")

st.markdown(
    "Paste UTM coordinates (Easting, Northing) below, one pair per line, comma- or space-separated.  \n"
    "**Example:**  \n"
    "`465177.689,5708543.612`  \n"
    "`465154.25 5708490.11`"
)

coord_text = st.text_area("Input Coordinates", height=200)
utm_zone = st.number_input("UTM Zone", min_value=1, max_value=60, value=31)
radius_m = st.number_input("Circle Radius (m)", value=50)
num_points = st.number_input("Points per Circle", min_value=3, value=17)
apply_correction = st.checkbox("Apply Epoch 2025.5 Correction", value=True)

if st.button("Generate Circles"):
    lines = coord_text.strip().splitlines()
    coords = []
    errors = []

    for line in lines:
        parts = line.replace(",", " ").split()
        if len(parts) == 2:
            try:
                e, n = float(parts[0]), float(parts[1])
                coords.append((e, n))
            except ValueError:
                errors.append(f"Invalid number format: {line}")
        else:
            errors.append(f"Wrong format: {line}")

    if errors:
        for err in errors:
            st.error(err)

    if coords:
        all_dfs = []
        centers = []

        for idx, (e, n) in enumerate(coords):
            df, lat_c, lon_c = generate_circle_from_utm(
                e, n, utm_zone, radius_m, num_points, apply_epoch_correction=apply_correction
            )
            df["Circle ID"] = f"Circle {idx+1}"
            all_dfs.append(df)
            centers.append({"Circle ID": f"Circle {idx+1}", "Latitude": lat_c, "Longitude": lon_c})

        final_df = pd.concat(all_dfs, ignore_index=True)
        center_df = pd.DataFrame(centers)

        st.success(f"Generated {len(coords)} circle(s) with {num_points} points each.")
        st.markdown("### Circle Coordinates")
        st.dataframe(final_df)

        st.markdown("### WGS84 Center Coordinates (one per circle)")
        st.dataframe(center_df)

        st.markdown("### 📋 Copy a Column")
        selected_col = st.selectbox("Select column to copy", final_df.columns)
        try:
            copy_content = "\n".join(map(str, final_df[selected_col].dropna()))
            st.text_area("Copy below:", copy_content, height=200)
        except Exception as e:
            st.warning(f"Unable to copy selected column: {e}")

        csv = final_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "circle_points.csv", "text/csv")
