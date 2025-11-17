import json
from pathlib import Path
from shapely.geometry import shape, Point
from shapely import maximum_inscribed_circle
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import cv2 as cv
import numba as nb
from icecream import ic

BASE_DIR = Path(__file__).resolve().parent.parent
DEPENDENCY_DIR = BASE_DIR / "web" / "static" / "dependencies"

def format_longitude(x, pos=None):
    direction = "W" if x < 0 else "E"
    return f"{abs(x):.1f}° {direction}"

def format_latitude(y, pos=None):
    direction = "S" if y < 0 else "N"
    return f"{abs(y):.1f}° {direction}"

@nb.njit(cache=True, parallel=True)
def horizontal_adjacency(grid):
    rows, cols = grid.shape
    result = np.zeros((rows, cols), dtype=np.uint32)
    for r in nb.prange(rows):
        span = 0
        for c in range(cols-1, -1, -1):
            if grid[r, c]:
                span += 1
            else:
                span = 0
            result[r, c] = span
    return result

@nb.njit(cache=True, parallel=True)
def vertical_adjacency(grid):
    rows, cols = grid.shape
    result = np.zeros((rows, cols), dtype=np.uint32)
    for c in nb.prange(cols):
        span = 0
        for r in range(rows-1, -1, -1):
            if grid[r, c]:
                span += 1
            else:
                span = 0
            result[r, c] = span
    return result

@nb.njit(cache=True)
def biggest_span_in_span_map(span_map):
    rows, cols, _ = span_map.shape
    max_area = 0
    best_rect = np.array([0, 0, 0, 0], dtype=np.uint32)
    for r in range(rows):
        for c in range(cols):
            w = span_map[r, c, 0]
            h = span_map[r, c, 1]
            area = w * h
            if area > max_area:
                max_area = area
                best_rect = np.array([c, r, w, h], dtype=np.uint32)
    return best_rect

@nb.njit(cache=True, parallel=True)
def span_map(grid, h_adj, v_adj):
    rows, cols = grid.shape
    span_map = np.zeros((rows, cols, 2), dtype=np.uint32)
    for r in nb.prange(rows):
        for c in range(cols):
            if grid[r, c]:
                max_width = h_adj[r, c]
                max_height = v_adj[r, c]
                max_area = 0
                best_w = 0
                best_h = 0
                for height in range(1, max_height + 1):
                    width = min(max_width, h_adj[r + height - 1, c])
                    area = width * height
                    if area > max_area:
                        max_area = area
                        best_w = width
                        best_h = height
                span_map[r, c, 0] = best_w
                span_map[r, c, 1] = best_h
    return span_map

def largest_inscribed_rectangle_state(state_name, resolution=1000):
    with open(DEPENDENCY_DIR / "states.json") as f:
        data = json.load(f)

    for feature in data['features']:
        if feature['properties']['NAME'].lower() == state_name.lower():
            polygon = shape(feature['geometry'])
            minx, miny, maxx, maxy = polygon.bounds
            width = resolution
            height = int(resolution * (maxy - miny) / (maxx - minx))
            grid = np.zeros((height, width), dtype=np.uint8)

            def to_pixel_coords(x, y):
                px = int((x - minx) / (maxx - minx) * (width - 1))
                py = int((maxy - y) / (maxy - miny) * (height - 1))
                return px, py

            if polygon.geom_type == 'MultiPolygon':
                for poly in polygon.geoms:
                    pts = [to_pixel_coords(x, y) for x, y in poly.exterior.coords]
                    pts = np.array(pts, np.int32).reshape((-1, 1, 2))
                    cv.fillPoly(grid, [pts], 1)
            else:
                pts = [to_pixel_coords(x, y) for x, y in polygon.exterior.coords]
                pts = np.array(pts, np.int32).reshape((-1, 1, 2))
                cv.fillPoly(grid, [pts], 1)

            bool_grid = grid.astype(bool)
            h_adj = horizontal_adjacency(bool_grid)
            v_adj = vertical_adjacency(bool_grid)
            s_map = span_map(bool_grid, h_adj, v_adj)
            rect = biggest_span_in_span_map(s_map)

            def to_lonlat(px, py):
                x = minx + px / (width - 1) * (maxx - minx)
                y = maxy - py / (height - 1) * (maxy - miny)
                return x, y

            ll_pt1 = to_lonlat(rect[0], rect[1])
            ll_pt2 = to_lonlat(rect[0] + rect[2] - 1, rect[1] + rect[3] - 1)

            center_lon = (ll_pt1[0] + ll_pt2[0]) / 2
            center_lat = (ll_pt1[1] + ll_pt2[1]) / 2

            return {
                'rectangle_corners': (ll_pt1, ll_pt2),
                'center': (center_lon, center_lat)
            }
    return None

def combined_largest_centers_and_plot(state_name, print:bool = False, plot:bool = False):
    with open(DEPENDENCY_DIR / "states.json") as f:
        data = json.load(f)
    polygon = None
    for feature in data['features']:
        if feature['properties']['NAME'].lower() == state_name.lower():
            polygon = shape(feature['geometry'])
            break
    if polygon is None:
        print("State not found")
        return

    # Largest inscribed circle center
    mic_line = maximum_inscribed_circle(polygon)
    circle_center_point = Point(mic_line.coords[0])
    boundary_point = Point(mic_line.coords[1])
    radius = circle_center_point.distance(boundary_point)
    circle_center = (circle_center_point.x, circle_center_point.y)

    # Largest inscribed rectangle center
    rect_result = largest_inscribed_rectangle_state(state_name)
    rect_corners = rect_result['rectangle_corners']
    rect_center = rect_result['center']

    # Average center of circle and rectangle centers
    avg_center_lon = (circle_center[0] + rect_center[0]) / 2
    avg_center_lat = (circle_center[1] + rect_center[1]) / 2
    avg_center = (avg_center_lon, avg_center_lat)

    # Plot all
    fig, ax = plt.subplots(figsize=(8,8))

    # Polygon plot
    if polygon.geom_type == 'MultiPolygon':
        for poly in polygon.geoms:
            x, y = poly.exterior.xy
            ax.plot(x, y, color='blue')
    else:
        x, y = polygon.exterior.xy
        ax.plot(x, y, color='blue')

    # Circle plot
    circle_patch = patches.Circle(circle_center, radius, color='green', alpha=0.3, label="Largest Inscribed Circle")
    ax.add_patch(circle_patch)
    ax.plot(circle_center[0], circle_center[1], 'go', label="Circle Center")

    # Rectangle plot
    x1, y1 = rect_corners[0]
    x2, y2 = rect_corners[1]
    rect_width = x2 - x1
    rect_height = y2 - y1
    rect_patch = patches.Rectangle((x1, y1), rect_width, rect_height, edgecolor='red', facecolor='none', linewidth=2, label='Largest Inscribed Rectangle')
    ax.add_patch(rect_patch)
    ax.plot(rect_center[0], rect_center[1], 'ro', label="Rectangle Center")

    # Average center plot
    ax.plot(avg_center[0], avg_center[1], 'ko', label="Average Center")

    ax.xaxis.set_major_formatter(plt.FuncFormatter(format_longitude))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(format_latitude))

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect('equal')
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0)
    plt.tight_layout()
    plt.subplots_adjust(right=0.8)
    ax.set_title(f"Largest Inscribed Circle, Rectangle, and Average Center for {state_name}")

    if plot: plt.show()
    if print:
        # Print centers via icecream
        ic(f"Circle Center (Lat, Lon): ({circle_center[1]}, {circle_center[0]})")
        ic(f"Rectangle Center (Lat, Lon): ({rect_center[1]}, {rect_center[0]})")
        ic(f"Average Center (Lat, Lon): ({avg_center_lat}, {avg_center_lon})")

    return({"circle": circle_center, "rectanle": rect_center, "average": [float(avg_center_lon), float(avg_center_lat)]})

# Example usage:
ic(combined_largest_centers_and_plot("Montana")["circle"])
