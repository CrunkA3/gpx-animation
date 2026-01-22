"""
Erstellt Statistiken aus einer GPX-Datei und generiert ein Bild mit den Statistiken.
"""

import datetime
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# GPX-Datei parsen
def parse_gpx(filename):
    """
    parsed eine GPX-Datei und extrahiert die Trackpunkte.

    :param filename:  GPX datei pfad
    :return: Liste von Trackpunkten als Tupel (lat, lon, time, elevation)
    """
    tree = ET.parse(filename)
    root = tree.getroot()

    # Namespace für GPX
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    # Alle Trackpunkte extrahieren
    points = []
    for trkpt in root.findall(".//gpx:trkpt", ns):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        time_elem = trkpt.find("gpx:time", ns)
        elevation = trkpt.find("gpx:ele", ns)
        if elevation is not None:
            elevation = float(elevation.text)

        # Parse time
        time_parsed = None
        if time_elem is not None:
            time_str = time_elem.text
            time_parsed = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")

        points.append((lat, lon, time_parsed, elevation))

    return points


def create_stats_image(
    stats, font_color=(255, 255, 255, 255), shadow_color=(0, 0, 0, 128)
):
    """Erstellt ein Bild mit den Statistiken in einem 2x2 Grid mit geblurten Drop-Shadow."""
    width, height = 800, 400
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))  # Transparent background
    draw = ImageDraw.Draw(img)

    # Create shadow image
    shadow_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)

    try:
        font_small = ImageFont.truetype("C:\\Windows\\Fonts\\consola.ttf", 32)
        font_large = ImageFont.truetype("C:\\Windows\\Fonts\\consola.ttf", 48)
        font_small_bold = ImageFont.truetype("C:\\Windows\\Fonts\\consolab.ttf", 32)
        font_large_bold = ImageFont.truetype("C:\\Windows\\Fonts\\consolab.ttf", 48)
    except:
        font_small = ImageFont.load_default()
        font_large = ImageFont.load_default()

    # Positions
    col1_x = 40
    col2_x = 440
    row1_y = 40
    row2_y = 200
    shadow_offset = 0
    detail_offset = 50

    # Calculate values
    total_seconds = stats["total_time_s"]
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)

    pace_min = int(stats["pace_s_per_km"] // 60)
    pace_sec = int(stats["pace_s_per_km"] % 60)

    dist_text = f"{stats['total_distance_m'] / 1000:.2f} km"
    time_text = f"{hours}:{minutes:02d} h"
    pace_text = (
        f"{pace_min}:{pace_sec:02d} /km"
        if stats["pace_s_per_km"] is not None
        else "N/A"
    )
    elev_text = f"{stats['elevation_gain_m']:.0f} m"

    # Define elements to draw
    elements = [
        {
            "x": col1_x,
            "y": row1_y,
            "text": "Distanz",
            "font": font_small,
            "font_bold": font_small_bold,
        },
        {
            "x": col1_x,
            "y": row1_y + detail_offset,
            "text": dist_text,
            "font": font_large,
            "shadow_font": font_large_bold,
        },
        {
            "x": col2_x,
            "y": row1_y,
            "text": "Zeit",
            "font": font_small,
            "font_bold": font_small_bold,
        },
        {
            "x": col2_x,
            "y": row1_y + detail_offset,
            "text": time_text,
            "font": font_large,
            "shadow_font": font_large_bold,
        },
        {
            "x": col1_x,
            "y": row2_y,
            "text": "Pace",
            "font": font_small,
            "font_bold": font_small_bold,
        },
        {
            "x": col1_x,
            "y": row2_y + detail_offset,
            "text": pace_text,
            "font": font_large,
            "shadow_font": font_large_bold,
        },
        {
            "x": col2_x,
            "y": row2_y,
            "text": "Höhenmeter",
            "font": font_small,
            "font_bold": font_small_bold,
        },
        {
            "x": col2_x,
            "y": row2_y + detail_offset,
            "text": elev_text,
            "font": font_large,
            "shadow_font": font_large_bold,
        },
    ]

    # Draw all shadows
    for elem in elements:
        shadow_draw.text(
            (elem["x"] + shadow_offset, elem["y"] + shadow_offset),
            elem["text"],
            font=elem["font_bold"],
            fill=shadow_color,
        )

    # Blur the shadow
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(4))

    # Composite shadow onto main image
    img = Image.alpha_composite(img, shadow_img)

    # Recreate draw object after compositing
    draw = ImageDraw.Draw(img)

    # Draw all main text
    for elem in elements:
        draw.text(
            (elem["x"], elem["y"]), elem["text"], font=elem["font"], fill=font_color
        )
    return img


def calculate_track_stats(points):
    """Berechnet Statistiken für die gegebenen Trackpunkte."""

    lats = np.array([p[0] for p in points])
    lons = np.array([p[1] for p in points])

    total_distance = 0.0
    total_time = 0.0
    elevation_gain = 0.0

    for i in range(1, len(points)):
        # Haversine-Formel zur Berechnung der Distanz zwischen zwei Punkten
        R = 6371e3  # Erdradius in Metern
        phi1 = np.radians(lats[i - 1])
        phi2 = np.radians(lats[i])
        delta_phi = np.radians(lats[i] - lats[i - 1])
        delta_lambda = np.radians(lons[i] - lons[i - 1])

        a = (
            np.sin(delta_phi / 2) ** 2
            + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2) ** 2
        )
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        distance = R * c
        total_distance += distance

        # Calculate elevation gain with threshold to filter noise
        if points[i][3] is not None and points[i - 1][3] is not None:
            delta = points[i][3] - points[i - 1][3]
            if delta > 0.3:  # Only count gains over 0.3 meter to reduce noise
                elevation_gain += delta

    # Calculate total time
    if points and points[0][2] is not None and points[-1][2] is not None:
        total_time = (points[-1][2] - points[0][2]).total_seconds()
    else:
        total_time = 0.0

    return {
        "total_distance_m": total_distance,
        "total_time_s": total_time,
        "elevation_gain_m": elevation_gain,
        "pace_s_per_km": (total_time / (total_distance / 1000))
        if total_distance > 0
        else None,
    }


# Hauptprogramm
if __name__ == "__main__":
    gpx_file = "gpx_files/22_31.gpx"

    print("Parse GPX-Datei...")
    track_points = parse_gpx(gpx_file)
    print(f"Gefunden: {len(track_points)} Trackpunkte")

    stats = calculate_track_stats(track_points)
    print(f"Gesamtdistanz: {stats['total_distance_m'] / 1000:.2f} km")
    print(
        f"Gesamtzeit: {int(stats['total_time_s'] // 3600)}:{int((stats['total_time_s'] % 3600) // 60):02d}:{int(stats['total_time_s'] % 60):02d}"
    )
    if stats["pace_s_per_km"] is not None:
        pace_min = int(stats["pace_s_per_km"] // 60)
        pace_sec = int(stats["pace_s_per_km"] % 60)
        print(f"Pace: {pace_min}:{pace_sec:02d} min/km")
    else:
        print("Pace: N/A")
    print(f"Höhenmeter: {stats['elevation_gain_m']:.0f} m")
    # Erstelle und speichere das Stats-Bild
    stats_img = create_stats_image(
        stats, (255, 255, 255, 255), (0, 0, 0, 128)
    )  # Weiße Schrift
    stats_img.save("output/stats_white.png")
    stats_img = create_stats_image(
        stats, (0, 0, 0, 255), (255, 255, 255, 128)
    )  # Schwarze Schrift
    stats_img.save("output/stats_black.png")
    stats_img = create_stats_image(
        stats, (252, 82, 0, 255), (207, 64, 23, 128)
    )  # Orange Schrift
    stats_img.save("output/stats_orange.png")
    print("Stats-Bilder gespeichert")

    print("Fertig!")
