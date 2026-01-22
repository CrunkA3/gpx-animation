"""
Dieses Skript liest eine GPX-Datei ein, extrahiert die Trackpunkte und erstellt
eine animierte GIF-Datei, die den Track mit einem Leuchteffekt darstellt.
"""

import io
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from PIL import Image


# GPX-Datei parsen
def parse_gpx(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    # Namespace für GPX
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    # Alle Trackpunkte extrahieren
    points = []
    for trkpt in root.findall(".//gpx:trkpt", ns):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        points.append((lat, lon))

    return points


# Animation erstellen
def create_animation(
    points,
    output_file="track_animation.gif",
    duration=5,
    frame_skip=1,
    line_color="b",
    line_width=2
):
    fig, ax = plt.subplots(figsize=(24, 20))
    fig.patch.set_alpha(0)  # Transparenter Figure-Hintergrund
    ax.patch.set_alpha(0)  # Transparenter Axes-Hintergrund

    # Daten vorbereiten
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]

    # Plot-Grenzen setzen
    ax.set_xlim(min(lons) - 0.001, max(lons) + 0.001)
    ax.set_ylim(min(lats) - 0.001, max(lats) + 0.001)
    ax.set_aspect("equal")
    ax.axis("off")  # Keine Achsen und kein Grid

    # Linie für den Track
    (glow1,) = ax.plot(
        [], [], "-", color=line_color, linewidth=line_width * 4, alpha=0.1
    )
    (glow2,) = ax.plot(
        [], [], "-", color=line_color, linewidth=line_width * 3.5, alpha=0.15
    )
    (glow3,) = ax.plot(
        [], [], "-", color=line_color, linewidth=line_width * 3, alpha=0.2
    )
    (glow4,) = ax.plot(
        [], [], "-", color=line_color, linewidth=line_width * 2.5, alpha=0.25
    )
    (glow5,) = ax.plot(
        [], [], "-", color=line_color, linewidth=line_width * 2, alpha=0.3
    )
    (line,) = ax.plot([], [], "-", color=line_color, linewidth=line_width)

    # Frame-Bilder speichern
    frames = []

    def animate(frame):
        if frame > 0:
            # Track bis zu diesem Punkt zeichnen
            glow1.set_data(lons[:frame], lats[:frame])
            glow2.set_data(lons[:frame], lats[:frame])
            glow3.set_data(lons[:frame], lats[:frame])
            glow4.set_data(lons[:frame], lats[:frame])
            glow5.set_data(lons[:frame], lats[:frame])
            line.set_data(lons[:frame], lats[:frame])

        # Frame als Bild speichern
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
        buf.seek(0)
        img = Image.open(buf).convert("RGBA")
        # Konvertiere zu P-Modus für GIF-Transparenz
        img = img.quantize(colors=256)
        frames.append(img)

        return line, glow1, glow2, glow3, glow4, glow5

    # Animation berechnen
    print(
        f"{len(points)} Punkte, Frames werden alle {frame_skip} Punkte gespeichert..."
    )
    for i in range(len(points)):
        if i % frame_skip == 0:
            animate(i)

    # GIF speichern
    if frames:
        num_frames = len(frames)
        frame_duration_ms = (duration * 1000) / num_frames if num_frames > 0 else 0
        frames[0].save(
            output_file,
            save_all=True,
            append_images=frames[1:],
            duration=int(frame_duration_ms),
            loop=0,
            transparency=0,
        )
        print(f"Animation gespeichert: {output_file}")
        # Letzten Frame als PNG speichern
        frames[-1].save("last_frame.png")
        print("Letzter Frame gespeichert: last_frame.png")


# Hauptprogramm
if __name__ == "__main__":
    gpx_file = "gpx_files/22_31.gpx"

    print("Parse GPX-Datei...")
    track_points = parse_gpx(gpx_file)
    print(f"Gefunden: {len(track_points)} Trackpunkte")

    print("Erstelle Animation...")
    frame_skip = 10  # Jeder 10. Frame wird gespeichert
    create_animation(
        track_points,
        output_file="track_animation.gif",
        duration=5,
        frame_skip=frame_skip,
        line_color="#FC4C02",
        line_width=4
    )

    print("Fertig!")
