# save_urls_simple.py

import os
import sys
import django

# Setup Django
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WallPic.settings')

django.setup()

from wallpapers.models import DesktopWallpaper, MobileWallpaper
from datetime import datetime

# Get timestamp for filename
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Get all wallpapers
desktop_wps = DesktopWallpaper.objects.all()
mobile_wps = MobileWallpaper.objects.all()

# Save ALL image URLs to one file
image_file = f"all_image_urls_{timestamp}.txt"
with open(image_file, 'w') as f:
    # Desktop images
    for wp in desktop_wps:
        f.write(f"{wp.image_url}\n")
    
    # Mobile images
    for wp in mobile_wps:
        f.write(f"{wp.image_url}\n")

print(f"✓ Saved {desktop_wps.count() + mobile_wps.count()} image URLs to: {image_file}")

# Save ALL thumbnail URLs to one file
thumb_file = f"all_thumbnail_urls_{timestamp}.txt"
with open(thumb_file, 'w') as f:
    # Desktop thumbnails
    for wp in desktop_wps:
        f.write(f"{wp.thumbnail_url}\n")
    
    # Mobile thumbnails
    for wp in mobile_wps:
        f.write(f"{wp.thumbnail_url}\n")

print(f"✓ Saved {desktop_wps.count() + mobile_wps.count()} thumbnail URLs to: {thumb_file}")

# Summary
print(f"\nSummary:")
print(f"Desktop wallpapers: {desktop_wps.count()}")
print(f"Mobile wallpapers: {mobile_wps.count()}")
print(f"Total wallpapers: {desktop_wps.count() + mobile_wps.count()}")