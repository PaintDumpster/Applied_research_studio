import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
import osmnx as ox
import geemap
import ee
import rasterio
from geopy.geocoders import Nominatim
from PIL import Image
import time

cities_list=["samara, russia"]

## gee credentials

# Authenticate and initialize
ee.Authenticate()  # Run this only once; follow the on-screen instructions
# Explicitly set the project ID
ee.Initialize(project='ee-salvadorcantuarias') # Replace 'your-project-id' with your actual Google Cloud project ID

def get_osm_boundary(city_name):
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(city_name, exactly_one=True)
    
    if location:
        bbox = location.raw['boundingbox']
        lat_min, lat_max, lon_min, lon_max = map(float, bbox)
        return (lat_min, lat_max, lon_min, lon_max)  # Return the bounding box as a tuple
    else:
        return None

def generateStreetLayout(city_name):
    # Generate graph using boundary coordinates
    bbox = get_osm_boundary(city_name)
    if bbox is None:
        print(f"City '{city_name}' not found or has no bounding box.")
        return None

    lat_min, lat_max, lon_min, lon_max = bbox

    try:
        graph = ox.graph_from_bbox(bbox, network_type='drive')
        fig, ax = ox.plot_graph(graph, node_size=0, bgcolor='#FFFFFF', edge_color='#000000', edge_linewidth=0.2)
        image_path = f"rcs/street_img/{city_name}_street_network.png"
        fig.savefig(image_path, dpi=400, bbox_inches='tight')
        return fig, ax
    except Exception as e:
        print(f"An error occurred while generating the street layout: {e}")
        return None


def generate_elevation_numpy(city_name):
    print(f"🔍 Searching for {city_name} in OpenStreetMap...")

    # Step 1: Fetch city boundary from OSM (instead of FAO/GAUL)
    bbox = get_osm_boundary(city_name)
    if bbox is None:
        print(f"❌ Error: Could not find {city_name} boundary in OSM.")
        return None, None

    print(f"✅ City boundary found! Clipping elevation map to {city_name}...")

    # Step 2: Load the NASADEM elevation dataset
    dataset = ee.Image('NASA/NASADEM_HGT/001')
    elevation = dataset.select('elevation')

    # Step 3: Clip the elevation data to the city's bounding box
    lat_min, lat_max, lon_min, lon_max = bbox
    region = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])
    elevation_city = elevation.clip(region)

    # Step 4: Define export file paths
    tif_file = f"rcs/elevation_img/elevation_tif/{city_name}_elevation.tif"
    png_file = f"rcs/elevation_img/elevation_png/{city_name}_elevation.png"
    npy_file = f"rcs/elevation_img/elevation_npy/{city_name}_elevation.npy"

    # Step 5: Export the elevation map as GeoTIFF
    export_scale = 100  # Adjust resolution if needed
    geemap.ee_export_image(
        elevation_city, filename=tif_file, scale=export_scale, region=region, file_per_band=False
    )
    print(f"✅ GeoTIFF saved: {tif_file}")

    # Step 6: Convert GeoTIFF to PNG & NumPy Array
    if os.path.exists(tif_file):
        with rasterio.open(tif_file) as src:
            array = src.read(1)  # Read first band

            # Replace NoData values with 0
            array[array == src.nodata] = 0

            # Save as NumPy array for AI processing
            np.save(npy_file, array)
            print(f"✅ NumPy array saved: {npy_file}")

            # Normalize elevation values (0-255 grayscale) for visualization
            min_val, max_val = np.percentile(array, (2, 98))
            normalized_array = ((array - min_val) / (max_val - min_val)) * 255
            normalized_array = np.clip(normalized_array, 0, 255).astype(np.uint8)

            # Convert to grayscale image
            img = Image.fromarray(normalized_array)
            img = img.convert("L")

            # Save the PNG
            img.save(png_file)

            print(f"✅ PNG saved: {png_file}")

        return npy_file, png_file
    else:
        print("❌ Error: GeoTIFF file not found.")
        return None, None

# Function to overlay elevation and street layout maps
def overlay_maps(city_name):
    # Define file paths
    elevation_file = f"rcs/elevation_img/elevation_png/{city_name}_elevation.png"
    street_file = f"rcs/street_img/{city_name}_street_network.png"
    overlay_file = f"rcs/overlay_img/{city_name}_overlay.png"

    # Check if both files exist
    if not os.path.exists(elevation_file):
        print(f"❌ Error: Elevation map for {city_name} not found!")
        return None
    if not os.path.exists(street_file):
        print(f"❌ Error: Street layout for {city_name} not found!")
        return None

    # Load images
    elevation_img = cv2.imread(elevation_file, cv2.IMREAD_GRAYSCALE)  # Load elevation as grayscale
    street_img = cv2.imread(street_file, cv2.IMREAD_UNCHANGED)  # Load street layout as color

    # Ensure both images have the same size
    elevation_resized = cv2.resize(elevation_img, (street_img.shape[1], street_img.shape[0]))

    # Convert elevation to 3-channel grayscale (so it can blend with color)
    elevation_colored = cv2.cvtColor(elevation_resized, cv2.COLOR_GRAY2BGR)

    # Convert street layout to white lines on transparent background
    street_edges = cv2.Canny(street_img, 50, 150)  # Edge detection
    street_overlay = np.zeros_like(elevation_colored)
    street_overlay[street_edges > 0] = (0, 0, 255)  # Color edges red (change color if needed)

    # Blend the images with transparency
    overlay_result = cv2.addWeighted(elevation_colored, 1, street_overlay, 1, 0)

    # Save the overlay image
    cv2.imwrite(overlay_file, overlay_result)
    print(f"✅ Overlay saved: {overlay_file}")

    # Show the overlay image
    plt.figure(figsize=(8, 8))
    plt.imshow(cv2.cvtColor(overlay_result, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.title(f"Overlay of {city_name} Elevation & Streets")
    plt.show()

    # Download the overlay image
    '''files.download(overlay_file)'''

    return overlay_file




## FOR LOOP WITH CITIES

# ✅ Loop through the list of cities and generate maps
for city in cities_list:
    print(f"\n🌍 Processing: {city}...\n")

    try:
        # Define file paths
        elevation_file = f"rcs/elevation_img/elevation_png/{city}_elevation.png"
        street_file = f"rcs/street_img/{city}_street_network.png"
        overlay_file = f"rcs/overlay_img/{city}_overlay.png"
        npy_file = f"rcs/elevation_img/elevation_png/{city}_elevation.npy"

        # ✅ Check if files already exist to skip processing
        if os.path.exists(overlay_file):
            print(f"⚠️ {city} already processed, skipping...")
            continue

        # ✅ Generate Topography (Elevation) Map
        print("🔄 Generating elevation map...")
        elevation_result = generate_elevation_numpy(city)
        if elevation_result is None:
            print(f"⚠️ Skipping {city} due to missing elevation data.")
            continue

        # ✅ Generate Street Layout Map
        print("🔄 Generating street layout map...")
        street_result = generateStreetLayout(city)
        if street_result is None:
            print(f"⚠️ Skipping {city} due to missing street data.")
            continue

        # ✅ Generate Overlay of Topography & Street Layout
        print("🔄 Generating overlay map...")
        overlay_result = overlay_maps(city)
        if overlay_result is None:
            print(f"⚠️ Skipping {city} due to overlay generation failure.")
            continue

        print(f"✅ Completed: {city} ✅\n")

        # ✅ Add a short delay to avoid API rate limits
        time.sleep(2)

    except Exception as e:
        print(f"❌ Error processing {city}: {e}")