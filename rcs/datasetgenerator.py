import cv2
import os
import time
import matplotlib as plt
import numpy as np
import osmnx
from geopy.geocoders import Nominatim
import ee
import geemap
import rasterio
from PIL import Image



# list of cities
cities_list_2 = [
    "Tokyo, Japan", "Delhi, India", "Shanghai, China", "Sao Paulo, Brazil", "Cairo, Egypt",
    "Mumbai, India", "Beijing, China", "Dhaka, Bangladesh", "Mexico City, Mexico", "Osaka, Japan",
    "Karachi, Pakistan", "Chongqing, China", "Istanbul, Turkey", "Buenos Aires, Argentina", "Kolkata, India",
    "Kinshasa, DR Congo", "Lagos, Nigeria", "Manila, Philippines", "Rio de Janeiro, Brazil", "Guangzhou, China",
    "Los Angeles, USA", "Moscow, Russia", "Shenzhen, China", "Lahore, Pakistan", "Bangalore, India",
    "Paris, France", "Bogota, Colombia", "Jakarta, Indonesia", "Chennai, India", "Lima, Peru",
    "Bangkok, Thailand", "Hyderabad, India", "Seoul, South Korea", "Nagoya, Japan", "London, UK",
    "New York, USA", "Ho Chi Minh City, Vietnam", "Hong Kong, China", "Ahmadabad, India", "Kuala Lumpur, Malaysia",
    "Foshan, China", "Hanoi, Vietnam", "Santiago, Chile", "Baghdad, Iraq", "Madrid, Spain",
    "Toronto, Canada", "Belo Horizonte, Brazil", "Singapore, Singapore", "Pune, India", "Houston, USA",
    "Riyadh, Saudi Arabia", "Dallas, USA", "Dalian, China", "Guadalajara, Mexico", "Miami, USA",
    "Philadelphia, USA", "Atlanta, USA", "Fukuoka, Japan", "Zhengzhou, China", "Sydney, Australia",
    "Saint Petersburg, Russia", "Shenyang, China", "Changsha, China", "Chengdu, China", "Chicago, USA",
    "Nanjing, China", "Wuhan, China", "Luanda, Angola", "Dar es Salaam, Tanzania", "Kabul, Afghanistan",
    "Accra, Ghana", "Khartoum, Sudan", "San Francisco, USA", "Montreal, Canada", "Barcelona, Spain",
    "Qingdao, China", "Jinan, China", "Algiers, Algeria", "Melbourne, Australia", "Casablanca, Morocco",
    "Alexandria, Egypt", "Taipei, Taiwan", "Abidjan, Ivory Coast", "Cape Town, South Africa", "Hefei, China",
    "Tianjin, China", "Dongguan, China", "Faisalabad, Pakistan", "Addis Ababa, Ethiopia", "Surat, India",
    "Johannesburg, South Africa", "Shijiazhuang, China", "Rome, Italy", "Harbin, China", "Ankara, Turkey",
    "Brasilia, Brazil", "Munich, Germany", "Naples, Italy", "Milan, Italy", "Porto Alegre, Brazil",
    "Monterrey, Mexico", "Phoenix, USA", "Bandung, Indonesia", "Tashkent, Uzbekistan", "Vienna, Austria",
    "Jeddah, Saudi Arabia", "Lisbon, Portugal", "Budapest, Hungary", "Aleppo, Syria", "Baku, Azerbaijan",
    "Xian, China", "Antananarivo, Madagascar", "Hong Kong", "Sofia, Bulgaria", "San Diego, USA",
    "Porto, Portugal", "Helsinki, Finland", "Hamburg, Germany", "Stuttgart, Germany", "Liverpool, UK",
    "Cleveland, USA", "Charlotte, USA", "Edinburgh, UK", "Oslo, Norway", "Copenhagen, Denmark",
    "Brisbane, Australia", "Athens, Greece", "Perth, Australia", "Detroit, USA", "St Louis, USA",
    "Boston, USA", "Prague, Czech Republic", "Brussels, Belgium", "Warsaw, Poland", "Kiev, Ukraine",
    "Zurich, Switzerland", "Stockholm, Sweden", "Lviv, Ukraine", "Belgrade, Serbia", "Bucharest, Romania",
    "Santo Domingo, Dominican Republic", "San Jose, Costa Rica", "Manama, Bahrain", "Islamabad, Pakistan",
    "Kingston, Jamaica", "Doha, Qatar", "Panama City, Panama", "Nassau, Bahamas", "Reykjavik, Iceland",
    "Luxembourg City, Luxembourg", "San Salvador, El Salvador", "La Paz, Bolivia", "Suva, Fiji",
    "Thimphu, Bhutan", "Bandar Seri Begawan, Brunei", "Minsk, Belarus", "Nicosia, Cyprus", "Ljubljana, Slovenia",
    "Tallinn, Estonia", "Riga, Latvia", "Vilnius, Lithuania", "Tirana, Albania", "Podgorica, Montenegro",
    "Skopje, North Macedonia", "Sarajevo, Bosnia and Herzegovina", "Malabo, Equatorial Guinea", "Port Moresby, Papua New Guinea",
    "San Juan, Puerto Rico", "Honiara, Solomon Islands", "Apia, Samoa", "Port Louis, Mauritius", "Basseterre, Saint Kitts and Nevis",
    "Castries, Saint Lucia", "Kingstown, Saint Vincent and the Grenadines", "Paramaribo, Suriname", "Dili, East Timor",
    "N'Djamena, Chad", "Nouakchott, Mauritania", "Banjul, Gambia", "Port-au-Prince, Haiti", "Conakry, Guinea",
    "Porto-Novo, Benin", "Lome, Togo", "Niamey, Niger", "Kigali, Rwanda", "Praia, Cape Verde",
    "Majuro, Marshall Islands", "Palikir, Micronesia", "Yamoussoukro, Ivory Coast", "Rabat, Morocco", "Sanaa, Yemen",
]

cities_list3=["Talca, chile", "Fukuoka, Japan", "Palikir, Micronesia", "Majuro, Marshall Islands", "Tirana, Albania"]

cities_list=["samara, russia"]

#_____________________________________________________________________________________________________________________________________________________________________

## gee credentials

# Authenticate and initialize
ee.Authenticate()  # Run this only once; follow the on-screen instructions
# Explicitly set the project ID
ee.Initialize(project='ee-salvadorcantuarias') # Replace 'your-project-id' with your actual Google Cloud project ID

#_____________________________________________________________________________________________________________________________________________________________________
def generateStreetLayout(city_name):
    graph = osmnx.graph_from_place(city_name, network_type='drive')
    _, edges = osmnx.graph_to_gdfs(graph)

    # plotting the projection
    fig, ax = osmnx.plot_graph(graph, node_size= 0, bgcolor= '#FFFFFF', edge_color='#000000', edge_linewidth= 0.2)
    image_path = f"rcs/street_img/{city_name}_street_network.png"
    fig.savefig(image_path, dpi=400, bbox_inches='tight')
    return fig, ax

def get_osm_boundary(city_name):
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(city_name, exactly_one=True)

    if location:
        bbox = location.raw['boundingbox']
        lat_min, lat_max, lon_min, lon_max = map(float, bbox)
        return ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])  # Use OSM boundary
    else:
        return None

# ✅ Function to generate elevation as a NumPy array
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
    elevation_city = elevation.clip(bbox)

    # Step 4: Define export file paths
    tif_file = f"rcs/elevation_img/elevation_tif/{city_name}_elevation.tif"
    png_file = f"rcs/elevation_img/elevation_png/{city_name}_elevation.png"
    npy_file = f"rcs/elevation_img/elevation_npy/{city_name}_elevation.npy"

    # Step 5: Export the elevation map as GeoTIFF
    export_scale = 100  # Adjust resolution if needed
    geemap.ee_export_image(
        elevation_city, filename=tif_file, scale=export_scale, region=bbox, file_per_band=False
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

            # Step 7: Show the processed elevation map
            '''plt.figure(figsize=(8, 8))
            plt.imshow(img, cmap="gray")
            plt.axis("off")
            plt.title(f"{city_name} Elevation Map")
            plt.show()'''

        print(f"✅ PNG saved: {png_file}")

        # ✅ Download both PNG and NumPy files
        '''files.download(png_file)
        files.download(npy_file)'''

        return npy_file, png_file

    else:
        print("❌ Error: GeoTIFF file not found.")
        return None, None


# ✅ Function to overlay elevation and street layout maps
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

