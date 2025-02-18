import os
import osmnx as ox
import ee
import matplotlib.pyplot as plt

# Initialize the Earth Engine library
ee.Authenticate()
# Explicitly set the project ID
ee.Initialize(project='ee-salvadorcantuarias')

def getBoundary(city_name):
    """
    Takes a city name and returns a bounding box of the city in a list of 4 coordinates.
    """
    geolocator = ox.geocode_to_gdf(city_name)
    bbox = geolocator.geometry.union_all().bounds
    return [bbox[1], bbox[0], bbox[3], bbox[2]]  # [south, west, north, east]

def getStreetLayout(city_name):
    """
    Takes a city name, gets the bounding box, and returns a plot of the street layout.
    """
    bbox = getBoundary(city_name)
    G = ox.graph_from_bbox((bbox[0], bbox[2], bbox[1], bbox[3]), network_type='all')
    fig, ax = ox.plot_graph(G)
    return fig

def getGeeFeatures(city_name):
    """
    Takes a city name, gets the bounding box, and returns datasets from Google Earth Engine.
    """
    bbox = getBoundary(city_name)
    geometry = ee.Geometry.BBox(bbox[1], bbox[0], bbox[3], bbox[2])
    
    # Get elevation dataset
    elevation = ee.ImageCollection('NASA/NASADEM_HGT/001').select('elevation').filterBounds(geometry).mosaic().clip(geometry)
    
    # Get building height dataset
    building_height = ee.ImageCollection('GOOGLE/Research/open-buildings-temporal/v1').select('building_height').filterBounds(geometry).mosaic().clip(geometry)
    
    return elevation, building_height, geometry

def overLap(city_name):
    """
    Overlaps the street layout, elevation, and building height datasets, and saves each layer and the overlap image.
    """
    # Get the street layout plot
    street_plot = getStreetLayout(city_name)
    
    # Get the datasets
    elevation, building_height, geometry = getGeeFeatures(city_name)
    
    # Save each layer in the "new_images" folder
    base_directory = os.path.join(os.getcwd(), "new_images", city_name)
    os.makedirs(base_directory, exist_ok=True)
    
    street_layout_directory = os.path.join(base_directory, "street_layout")
    elevation_directory = os.path.join(base_directory, "elevation")
    building_height_directory = os.path.join(base_directory, "building_height")
    overlap_directory = os.path.join(base_directory, "overlap")
    
    os.makedirs(street_layout_directory, exist_ok=True)
    os.makedirs(elevation_directory, exist_ok=True)
    os.makedirs(building_height_directory, exist_ok=True)
    os.makedirs(overlap_directory, exist_ok=True)
    
    street_plot.savefig(os.path.join(street_layout_directory, 'street_layout.png'))
    
    # Export elevation and building height datasets as images
    elevation_path = os.path.join(elevation_directory, 'elevation.tif')
    building_height_path = os.path.join(building_height_directory, 'building_height.tif')
    
    elevation_url = elevation.getDownloadURL({'scale': 30, 'region': geometry.bounds().getInfo()})
    building_height_url = building_height.getDownloadURL({'scale': 30, 'region': geometry.bounds().getInfo()})
    
    # Combine and save overlap image
    combined_fig, combined_ax = plt.subplots()
    street_plot_ax = street_plot.gca()
    combined_ax.imshow(street_plot_ax.images[0].get_array(), cmap='gray', alpha=0.5)
    
    # Assuming you have a way to overlay elevation and building height images in matplotlib (requires further processing)
    # combined_ax.imshow(elevation_data, cmap='terrain', alpha=0.5)
    # combined_ax.imshow(building_height_data, cmap='cool', alpha=0.5)
    
    combined_fig.savefig(os.path.join(overlap_directory, 'overlap.png'))

# Example usage:
city_name = "Barcelona, Spain"
overLap(city_name)
