import streamlit as st
import pyproj
import numpy as np
import pandas as pd

# --- Circle generation function with improvements ---
def generate_circle_from_utm(easting, northing, utm_zone=31, radius_m=50, num_points=17, apply_epoch_correction=False, northern_hemisphere=True):
    epsg_base = 32600 if northern_hemisphere else 32700
    utm_crs = f"EPSG:{epsg_base + utm_zone}"
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
        "Angle (\u00b0)": np.round(angles_deg, 6),
        "Latitude": np.round(lats, 10),
        "Longitude": np.round(lons, 10)
    })

    # Repeat the unrounded first point before rounding
    first_lat, first_lon = lats[0], lons[0]
    df = pd.concat([df, pd.DataFrame({
        "Angle (\u00b0)": [360.0],
        "Latitude": [round(first_lat, 10)],
        "Longitude": [round(first_lon, 10)]
    })], ignore_index=True)

    return df, round(center_lat, 10), round(center_lon, 10)

# --- Streamlit App ---
st.title("UTM Point to WGS84 Circles")
st.image("tr-offshore-survey-logo-yellow-transparent-bg.png", width=150)

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
northern_hemisphere = st.checkbox("Northern Hemisphere", value=True)

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
        center_rows = []
        circle_tables = []

        for idx, (e, n) in enumerate(coords):
            df, lat_c, lon_c = generate_circle_from_utm(
                e, n, utm_zone, radius_m, num_points,
                apply_epoch_correction=apply_correction,
                northern_hemisphere=northern_hemisphere
            )
            label = f"Circle {idx+1}"

            st.markdown(f"### {label} Center")
            st.dataframe(pd.DataFrame([{
                "Latitude": lat_c,
                "Longitude": lon_c
            }]), use_container_width=True, hide_index=True)

            st.markdown(f"### {label} Coordinates")
            st.dataframe(df, use_container_width=True, hide_index=True)

            df["Circle ID"] = label
            circle_tables.append(df)
            center_rows.append({"Circle ID": label, "Latitude": lat_c, "Longitude": lon_c})

        st.markdown("### All Center Coordinates Summary")
        center_df = pd.DataFrame(center_rows)
        st.dataframe(center_df, use_container_width=True, hide_index=True)

        combined_df = pd.concat(circle_tables, ignore_index=True)
        csv = combined_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download All Circle Points as CSV", csv, "circle_points.csv", "text/csv")

        center_csv = center_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Center Coordinates as CSV", center_csv, "circle_centers.csv", "text/csv")
