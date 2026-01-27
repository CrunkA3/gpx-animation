"""GPX Track Animator zum Erstellen von Animationen aus GPX-Dateien."""

import os
import glob
from pathlib import Path
import gpxpy
import numpy as np
import matplotlib
import cv2

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle


MARKERSIZE = 20

class GPXTrackAnimator:
    """GPX Track Animator Klasse zum Erstellen von Animationen aus GPX-Dateien."""

    def export_svg_with_smil(self, output_svg="output/track_animation.svg", width=1400, height=1400, duration=5):
        """
        Exportiert die geladenen Tracks als animiertes SVG mit SMIL-Einblendung.
        Jeder Track wird als Polyline mit <animate> (opacity) versehen.
        """
        if not self.tracks:
            print("No tracks loaded. Please load GPX files first.")
            return

        # Bounding Box berechnen
        all_lats = np.concatenate([[p[0] for p in track] for track in self.tracks])
        all_lons = np.concatenate([[p[1] for p in track] for track in self.tracks])
        min_lat, max_lat = np.min(all_lats), np.max(all_lats)
        min_lon, max_lon = np.min(all_lons), np.max(all_lons)

        # Quadratische Bounding Box
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        if lat_range > lon_range:
            pad = (lat_range - lon_range) / 2
            min_lon -= pad
            max_lon += pad
        elif lon_range > lat_range:
            pad = (lon_range - lat_range) / 2
            min_lat -= pad
            max_lat += pad

        def geo_to_svg(lat, lon):
            # y-Achse invertieren (SVG: y nach unten)
            x = (lon - min_lon) / (max_lon - min_lon) * width
            y = height - (lat - min_lat) / (max_lat - min_lat) * height
            return x, y

        svg_elements = []
        svg_elements.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="background:black">')

        # Orange für SVG
        orange = "#fc4c02"
        fadein_time = duration  # Sekunden für alle
        per_track_delay = fadein_time / max(1, len(self.tracks))

        for i, track in enumerate(self.tracks):
            points = [geo_to_svg(p[0], p[1]) for p in track]
            points_str = " ".join(f"{int(x)},{int(y)}" for x, y in points)
            polyline_id = f"track{i}"
            # SMIL: opacity von 0 auf 1, zeitlich versetzt
            begin = f"{i*per_track_delay:.2f}s"
            svg_elements.append(f'<polyline id="{polyline_id}" points="{points_str}" stroke="{orange}" stroke-width="6" fill="none" opacity="0">')
            svg_elements.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.8s" begin="{begin}" fill="freeze" />')
            svg_elements.append(f'</polyline>')
            # Startmarker (Kreis)
            x0, y0 = points[0]
            svg_elements.append(f'<circle cx="{int(x0)}" cy="{int(y0)}" r="{MARKERSIZE}" fill="{orange}" opacity="0">')
            svg_elements.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.8s" begin="{begin}" fill="freeze" />')
            svg_elements.append(f'</circle>')

        svg_elements.append('</svg>')
        svg_code = "\n".join(svg_elements)
        os.makedirs(os.path.dirname(output_svg), exist_ok=True)
        with open(output_svg, "w", encoding="utf-8") as f:
            f.write(svg_code)
        print(f"SVG saved to {output_svg}")

    def __init__(
        self, gpx_folder, output_video="output/track_animation.mp4", fps=30, duration=10
    ):
        """
        Initialize the GPX Track Animator

        Args:
            gpx_folder: Folder containing GPX files
            output_video: Output MP4 filename
            fps: Frames per second for the video
            duration: Total duration of the animation in seconds
        """
        self.gpx_folder = gpx_folder
        self.output_video = output_video
        self.fps = fps
        self.duration = duration
        self.tracks = []
        self.track_names = []

    def draw_track(self, ax, track, color, offset=None):
        """Draw a track, optionally offsetting the startpunkt to a new position (lat, lon)."""
        lats = [p[0] for p in track]
        lons = [p[1] for p in track]
        if offset is not None:
            # Shift the whole track so that the first point is at offset
            dlat = offset[0] - lats[0]
            dlon = offset[1] - lons[0]
            lats = [lat + dlat for lat in lats]
            lons = [lon + dlon for lon in lons]
        ax.plot(lons, lats, color=color, linewidth=4)

    def load_gpx_files(self):
        """Load all GPX files from the folder"""


        gpx_files = sorted(glob.glob(os.path.join(self.gpx_folder, "*.gpx")), key=lambda x: Path(x).stem)
        tracks_and_names = []
        for gpx_file in gpx_files:
            with open(gpx_file, "r", encoding="utf-8") as f:
                gpx = gpxpy.parse(f)
                track = []
                for track_segment in gpx.tracks[0].segments:
                    for point in track_segment.points:
                        track.append(
                            (
                                point.latitude,
                                point.longitude,
                                point.elevation or 0,
                                point.time or None,
                            )
                        )
                tracks_and_names.append((track, Path(gpx_file).stem))
        # Nach Name sortieren
        tracks_and_names.sort(key=lambda x: x[1])
        self.tracks = [t for t, n in tracks_and_names]
        self.track_names = [n for t, n in tracks_and_names]

def main():
    # Configuration
    gpx_folder = "gpx_files"  # Change this to your GPX folder
    output_svg = "output/track_animation.svg"

    # Create animator and run
    animator = GPXTrackAnimator(
        gpx_folder=gpx_folder, output_video="", fps=30, duration=5
    )

    animator.load_gpx_files()
    animator.export_svg_with_smil(output_svg=output_svg, width=1400, height=1400, duration=5)


if __name__ == "__main__":
    main()
