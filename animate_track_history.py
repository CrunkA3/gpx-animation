import os
import glob
import gpxpy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import cv2
from pathlib import Path


class GPXTrackAnimator:
    def __init__(self, gpx_folder, output_video='track_animation.mp4', fps=30, duration_initial=3, duration_sort=4):
        """
        Initialize the GPX Track Animator
        
        Args:
            gpx_folder: Folder containing GPX files
            output_video: Output MP4 filename
            fps: Frames per second for the video
            duration_initial: Seconds to show tracks side by side initially
            duration_sort: Seconds for tracks to sort and straighten
        """
        self.gpx_folder = gpx_folder
        self.output_video = output_video
        self.fps = fps
        self.duration_initial = duration_initial
        self.duration_sort = duration_sort
        self.tracks = []
        self.track_names = []
        
    def load_gpx_files(self):
        """Load all GPX files from the folder"""
        gpx_files = glob.glob(os.path.join(self.gpx_folder, '*.gpx'))
        
        if not gpx_files:
            print(f"No GPX files found in {self.gpx_folder}")
            return
        
        for gpx_file in sorted(gpx_files):
            try:
                with open(gpx_file, 'r') as f:
                    gpx = gpxpy.parse(f)
                
                # Extract track points
                points = []
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            points.append([point.latitude, point.longitude, point.elevation or 0])
                
                if points:
                    points = np.array(points)
                    self.tracks.append(points)
                    self.track_names.append(Path(gpx_file).stem)
                    print(f"Loaded {gpx_file}: {len(points)} points")
            except Exception as e:
                print(f"Error loading {gpx_file}: {e}")
    
    def normalize_tracks(self):
        """Normalize tracks to a consistent coordinate system"""
        if not self.tracks:
            return
        
        # Find global bounds
        all_points = np.vstack(self.tracks)
        self.min_lat = all_points[:, 0].min()
        self.max_lat = all_points[:, 0].max()
        self.min_lon = all_points[:, 1].min()
        self.max_lon = all_points[:, 1].max()
        
        # Add padding
        lat_range = self.max_lat - self.min_lat
        lon_range = self.max_lon - self.min_lon
        padding = 0.1
        
        self.min_lat -= lat_range * padding
        self.max_lat += lat_range * padding
        self.min_lon -= lon_range * padding
        self.max_lon += lon_range * padding
        
        # Normalize each track to 0-1 range
        self.normalized_tracks = []
        for track in self.tracks:
            normalized = track.copy()
            normalized[:, 0] = (track[:, 0] - self.min_lat) / (self.max_lat - self.min_lat)
            normalized[:, 1] = (track[:, 1] - self.min_lon) / (self.max_lon - self.min_lon)
            self.normalized_tracks.append(normalized)
    
    def create_animation(self):
        """Create and save the animation as MP4"""
        if not self.tracks:
            print("No tracks loaded. Please load GPX files first.")
            return
        
        self.normalize_tracks()
        
        num_tracks = len(self.tracks)
        total_frames = int((self.duration_initial + self.duration_sort) * self.fps)
        initial_frames = int(self.duration_initial * self.fps)
        
        # Set up figure and axis
        fig, ax = plt.subplots(figsize=(14, 10), dpi=100)
        
        # Video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(
            self.output_video,
            fourcc,
            self.fps,
            (1400, 1000)
        )
        
        def animate(frame):
            ax.clear()
            
            # Determine animation phase
            if frame < initial_frames:
                # Phase 1: Show tracks side by side
                progress = 0
                phase = 'initial'
            else:
                # Phase 2: Sort and straighten tracks
                progress = (frame - initial_frames) / (total_frames - initial_frames)
                phase = 'sort'
            
            # Draw tracks
            colors = plt.cm.tab20(np.linspace(0, 1, num_tracks))
            
            for i, track in enumerate(self.normalized_tracks):
                x = track[:, 1]  # longitude
                y = track[:, 0]  # latitude
                
                if phase == 'initial':
                    # Side by side layout
                    x_offset = (i - num_tracks / 2 + 0.5) * 0.15
                    x_pos = x * 0.08 + x_offset
                    y_pos = y * 0.8 + 0.1
                else:
                    # Transition to sorted vertical layout
                    # Smooth easing function
                    eased_progress = progress ** 0.5
                    
                    # Initial position (side by side)
                    x_offset_initial = (i - num_tracks / 2 + 0.5) * 0.15
                    x_pos_initial = x * 0.08 + x_offset_initial
                    y_pos_initial = y * 0.8 + 0.1
                    
                    # Final position (vertical line)
                    x_pos_final = x * 0.1 + 0.45
                    y_pos_final = (1 - i / (num_tracks + 1)) * 0.8 + 0.1
                    
                    # Interpolate
                    x_pos = x_pos_initial + (x_pos_final - x_pos_initial) * eased_progress
                    y_pos = y_pos_initial + (y_pos_final - y_pos_initial) * eased_progress
                
                ax.plot(x_pos, y_pos, color=colors[i], linewidth=2, label=self.track_names[i], alpha=0.7)
            
            ax.set_xlim(-0.2, 1.2)
            ax.set_ylim(0, 1)
            ax.set_aspect('equal')
            ax.legend(loc='upper right', fontsize=8)
            ax.set_title(f'GPX Track Animation - Frame {frame + 1}/{total_frames}', fontsize=14)
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            ax.grid(True, alpha=0.3)
            
            # Render to image
            fig.canvas.draw()
            width, height = fig.canvas.get_width_height()
            image = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(height, width, 4)
            image_rgb = image[:, :, :3]  # Remove alpha channel
            image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            video_writer.write(image_bgr)
        
        # Generate animation
        for frame in range(total_frames):
            animate(frame)
            print(f"Frame {frame + 1}/{total_frames}")
        
        video_writer.release()
        plt.close(fig)
        print(f"Video saved to {self.output_video}")


def main():
    # Configuration
    gpx_folder = r'c:\Users\micha\source\repos\gpx-animation\gpx_files'  # Change this to your GPX folder
    output_video = 'track_animation.mp4'
    
    # Create animator and run
    animator = GPXTrackAnimator(
        gpx_folder=gpx_folder,
        output_video=output_video,
        fps=30,
        duration_initial=3,
        duration_sort=4
    )
    
    animator.load_gpx_files()
    animator.create_animation()


if __name__ == '__main__':
    main()
