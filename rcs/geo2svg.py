import geopandas
import matplotlib.pyplot as plt
import osmnx
import seaborn as sns
from shapely.geometry import Point, LineString

def getRoute(placeName):

  graph = osmnx.graph_from_place(placeName, network_type='drive')
  _, edges = osmnx.graph_to_gdfs(graph)

  # plotting the projection
  fig, ax = osmnx.plot_graph(graph, node_size= 0, bgcolor= '#FFFFFF', edge_color='#000000', edge_linewidth= 0.3)
  image_path = f"rcs/img/{placeName}_street_network.png"
  fig.savefig(image_path, dpi=400, bbox_inches='tight')


getRoute("leipzig")