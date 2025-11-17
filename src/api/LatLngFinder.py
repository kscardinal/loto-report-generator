from shapely.geometry import shape, Point
from shapely import maximum_inscribed_circle
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = Path(__file__).resolve().parent.parent
DEPENDENCY_DIR = BASE_DIR / "web" / "static" / "dependencies"

def format_longitude(x, pos=None):
    direction = "W" if x < 0 else "E"
    return f"{abs(x):.1f}° {direction}"

def format_latitude(y, pos=None):
    direction = "S" if y < 0 else "N"
    return f"{abs(y):.1f}° {direction}"

def largest_inscribed_circle_center(state_name):
    with open(DEPENDENCY_DIR / "states.json") as f:
        data = json.load(f)
    for feature in data['features']:
        if feature['properties']['NAME'].lower() == state_name.lower():
            polygon = shape(feature['geometry'])
            mic_line = maximum_inscribed_circle(polygon)
            
            center_point = Point(mic_line.coords[0])
            boundary_point = Point(mic_line.coords[1])
            radius = center_point.distance(boundary_point)
            center = (center_point.x, center_point.y)

            # Plotting
            fig, ax = plt.subplots(figsize=(8,8))

            # Plot polygon boundaries; handle MultiPolygon or Polygon
            if polygon.geom_type == 'MultiPolygon':
                for poly in polygon.geoms:
                    x, y = poly.exterior.xy
                    ax.plot(x, y, color="blue")
            else:
                x, y = polygon.exterior.xy
                ax.plot(x, y, color="blue")

            # Plot largest inscribed circle
            circle_patch = patches.Circle(center, radius, color='red', alpha=0.3, label="Largest Inscribed Circle")
            ax.add_patch(circle_patch)

            # Mark the center point
            ax.plot(center[0], center[1], 'ko', label="Circle Center")

            # Format the longitude and latitude labels with N/S E/W
            ax.xaxis.set_major_formatter(plt.FuncFormatter(format_longitude))
            ax.yaxis.set_major_formatter(plt.FuncFormatter(format_latitude))

            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.set_aspect('equal')
            ax.legend()
            ax.set_title(f"Largest Inscribed Circle for {state_name}")

            # Add full coordinate label under the x-axis
            coord_label = f"Center Coordinate: {abs(center[1]):.5f}° {'N' if center[1]>=0 else 'S'}, {abs(center[0]):.5f}° {'E' if center[0]>=0 else 'W'}"
            fig.text(0.5, 0.01, coord_label, ha='center', fontsize=10)

            plt.show()

            return center
    return None

# Example usage:
center = largest_inscribed_circle_center("Montana")
print("Center:", center)


def get_state_center(state_name):
    with open(DEPENDENCY_DIR / "states.json") as f:
        data = json.load(f)
    for feature in data['features']:
        if feature['properties']['NAME'].lower() == state_name.lower():
            polygon = shape(feature['geometry'])
            mic_line = maximum_inscribed_circle(polygon)

            center_point = Point(mic_line.coords[0])
            boundary_point = Point(mic_line.coords[1])
            # Radius computed if needed, not used here
            # radius = center_point.distance(boundary_point)

            # Longitude: negative for West (US convention)
            longitude = -abs(center_point.x) if center_point.x > 0 else center_point.x
            latitude = center_point.y if center_point.y >= 0 else -center_point.y  # always positive north

            return longitude, latitude
    return None

#center = get_state_center("Ohio")
#print("Latitude (N):", center[0], "Longitude (W):", center[1])
