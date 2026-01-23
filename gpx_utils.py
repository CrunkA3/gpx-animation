"""
GPX Utility Funktionen zum Parsen von GPX-Dateien.
"""

import datetime
import xml.etree.ElementTree as ET

def parse_gpx(filename):
    """
    Parsed eine GPX-Datei und extrahiert die Trackpunkte.

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
            elevation = round(elevation, 1)
        time_parsed = None
        if time_elem is not None:
            time_str = time_elem.text
            time_parsed = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        points.append((lat, lon, time_parsed, elevation))
    return points
