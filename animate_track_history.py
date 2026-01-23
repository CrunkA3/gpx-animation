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


class GPXTrackAnimator:
    """GPX Track Animator Klasse zum Erstellen von Animationen aus GPX-Dateien."""

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
        ax.plot(lons, lats, color=color, linewidth=2)

    def load_gpx_files(self):
        """Load all GPX files from the folder"""

        gpx_files = glob.glob(os.path.join(self.gpx_folder, "*.gpx"))
        for gpx_file in gpx_files:
            with open(gpx_file, "r") as f:
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
                self.tracks.append(track)
                self.track_names.append(Path(gpx_file).stem)

    def create_animation(self):
        """Create and save the animation as MP4"""

        # Ensure tracks are loaded
        if not self.tracks:
            print("No tracks loaded. Please load GPX files first.")
            return

        # Animation parameters
        num_tracks = len(self.tracks)
        total_frames = int((self.duration) * self.fps)
        initial_frames = int(self.duration * self.fps)

        # Set up figure and axis
        fig, ax = plt.subplots(figsize=(14, 14), dpi=100)

        # Compute bounding box for all tracks
        all_lats = np.concatenate([[p[0] for p in track] for track in self.tracks])
        all_lons = np.concatenate([[p[1] for p in track] for track in self.tracks])
        min_lat, max_lat = np.min(all_lats), np.max(all_lats)
        min_lon, max_lon = np.min(all_lons), np.max(all_lons)

        # Make bounding box square (quadratisch)
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

        # Distribute starting points evenly in a grid
        grid_cols = int(np.ceil(np.sqrt(num_tracks)))
        grid_rows = int(np.ceil(num_tracks / grid_cols))
        lat_grid = np.linspace(min_lat, max_lat, grid_rows)
        lon_grid = np.linspace(min_lon, max_lon, grid_cols)
        start_positions = []
        for idx in range(num_tracks):
            row = idx // grid_cols
            col = idx % grid_cols
            start_positions.append((lat_grid[row], lon_grid[col]))

        # Video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(
            self.output_video, fourcc, self.fps, (1400, 1400)
        )

        # Animation: move start points to center and distribute on x-axis
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        x_spread = (max_lon - min_lon) * 0.8  # 80% of width
        x_targets = np.linspace(
            center_lon - x_spread / 2, center_lon + x_spread / 2, num_tracks
        )
        y_target = center_lat
        # Get original start positions (first point of each track)
        orig_starts = np.array([[track[0][0], track[0][1]] for track in self.tracks])
        target_starts = np.array([[y_target, x] for x in x_targets])
        n_steps = int(self.fps * self.duration)  # Animation dauert volle duration

        # Orange in BGR für OpenCV: (2, 76, 252)
        orange_rgb = "#FC4C02"
        orange_bgr = (2/255, 76/255, 252/255)  # Matplotlib erwartet Werte 0-1
        
        for step in range(n_steps):
            ax.clear()
            ax.set_xlim(min_lon, max_lon)
            ax.set_ylim(min_lat, max_lat)
            ax.set_aspect("equal")
            alpha = step / (n_steps - 1)
            curr_starts = (1 - alpha) * orig_starts + alpha * target_starts

            # Draw all tracks
            for i, track in enumerate(self.tracks):
                self.draw_track(ax, track, orange_bgr, offset=curr_starts[i])

            # Draw moving start marker
            for i, curr in enumerate(curr_starts):
                ax.plot(curr[1], curr[0], marker="o", color=orange_bgr, markersize=10)


            ax.axis("off")
            fig.canvas.draw()
            img = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
            img = img.reshape(fig.canvas.get_width_height()[::-1] + (4,))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            video_writer.write(cv2.resize(img_rgb, (1400, 1400)))
           

        fig.canvas.draw()
        img = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
        img = img.reshape(fig.canvas.get_width_height()[::-1] + (4,))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        video_writer.write(cv2.resize(img_rgb, (1400, 1400)))

        # Am Ende das letzte Bild für 3 Sekunden halten
        hold_frames = int(self.fps * 3)
        for _ in range(hold_frames):
            video_writer.write(cv2.resize(img_rgb, (1400, 1400)))

        # Save Video
        video_writer.release()
        plt.close(fig)
        print(f"Video saved to {self.output_video}")


def main():
    # Configuration
    gpx_folder = "gpx_files"  # Change this to your GPX folder
    output_video = "output/track_animation.mp4"

    # Create animator and run
    animator = GPXTrackAnimator(
        gpx_folder=gpx_folder, output_video=output_video, fps=30, duration=10
    )

    animator.load_gpx_files()
    animator.create_animation()


if __name__ == "__main__":
    main()
