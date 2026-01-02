# populate_wallpapers_with_category.py - FIXED FOR SIMILAR FILENAMES
import sqlite3
import os
import random
import re
import json
import datetime
from PIL import Image
import numpy as np
from math import gcd
import hashlib
import shutil
from difflib import SequenceMatcher

def connect_to_database():
    """Connect to SQLite database."""
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_categories(conn):
    """Get all categories from database."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM wallpapers_category ORDER BY id")
    return cursor.fetchall()

def display_categories(categories):
    """Display all categories."""
    print("\n" + "=" * 60)
    print("DATABASE CATEGORIES")
    print("=" * 60)
    print(f"{'ID':<5} {'Category Name':<25}")
    print("-" * 60)
    
    for cat in categories:
        print(f"{cat['id']:<5} {cat['name']:<25}")
    
    print("=" * 60)

def find_category_folder(category_name, base_folder="."):
    """Find folder for a category."""
    # Try different folder name variations
    folder_variants = [
        category_name,
        category_name.replace("/", "_"),
        category_name.replace("/", "-"),
        category_name.lower(),
        category_name.upper(),
        category_name.title(),
    ]
    
    for variant in folder_variants:
        folder_path = os.path.join(base_folder, variant)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            return folder_path, variant
    
    return None, None

def similarity(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()

def find_best_match(base_name, candidates, threshold=0.7):
    """Find the best matching filename among candidates."""
    best_match = None
    best_score = 0
    
    base_name_clean = os.path.splitext(base_name)[0].lower()
    
    for candidate in candidates:
        candidate_clean = os.path.splitext(candidate)[0].lower()
        
        # Try exact match first (common prefixes)
        if candidate_clean.startswith(base_name_clean[:20]):
            return candidate
        
        # Calculate similarity
        score = similarity(base_name_clean, candidate_clean)
        
        # Extra points for containing the base name
        if base_name_clean in candidate_clean:
            score += 0.3
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate
    
    return best_match

def scan_category_images(folder_path):
    """Scan for images in a category folder - handles similar filenames."""
    images_found = []
    
    if not os.path.exists(folder_path):
        return images_found
    
    print(f"    📁 Scanning: {os.path.basename(folder_path)}")
    
    # Check for organized structure first
    wallpapers_dir = os.path.join(folder_path, "Wallpapers")
    thumbnails_dir = os.path.join(folder_path, "Thumbnails")
    
    if os.path.exists(wallpapers_dir) and os.path.exists(thumbnails_dir):
        print("    ✅ Found organized structure (Wallpapers/ + Thumbnails/)")
        return get_matching_images_with_similar_names(wallpapers_dir, thumbnails_dir)
    else:
        print("    ⚠ Checking for images in main folder...")
        return get_all_images_from_folder(folder_path)

def get_matching_images_with_similar_names(wallpapers_dir, thumbnails_dir):
    """Find matching wallpapers and thumbnails with similar (not identical) names."""
    images_found = []
    
    # Get all files
    wallpaper_files = []
    for file in os.listdir(wallpapers_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            wallpaper_files.append(file)
    
    thumbnail_files = []
    for file in os.listdir(thumbnails_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            thumbnail_files.append(file)
    
    print(f"    📊 Found {len(wallpaper_files)} wallpapers, {len(thumbnail_files)} thumbnails")
    
    # Match files
    matched_wallpapers = set()
    matched_thumbnails = set()
    
    # First pass: Try exact matches
    for wp_file in wallpaper_files:
        if wp_file in thumbnail_files:
            wp_path = os.path.join(wallpapers_dir, wp_file)
            thumb_path = os.path.join(thumbnails_dir, wp_file)
            images_found.append({
                'wallpaper_path': wp_path,
                'thumbnail_path': thumb_path,
                'filename': wp_file,
                'match_type': 'exact'
            })
            matched_wallpapers.add(wp_file)
            matched_thumbnails.add(wp_file)
    
    # Second pass: Try similar names
    unmatched_wallpapers = [f for f in wallpaper_files if f not in matched_wallpapers]
    unmatched_thumbnails = [f for f in thumbnail_files if f not in matched_thumbnails]
    
    print(f"    🔍 Matching {len(unmatched_wallpapers)} unmatched wallpapers...")
    
    for wp_file in unmatched_wallpapers:
        # Find best matching thumbnail
        best_thumb = find_best_match(wp_file, unmatched_thumbnails, threshold=0.6)
        
        if best_thumb:
            wp_path = os.path.join(wallpapers_dir, wp_file)
            thumb_path = os.path.join(thumbnails_dir, best_thumb)
            
            # Show what we matched
            wp_base = os.path.splitext(wp_file)[0]
            thumb_base = os.path.splitext(best_thumb)[0]
            print(f"        🔗 {wp_base[:40]}...")
            print(f"          → {thumb_base[:40]}...")
            
            images_found.append({
                'wallpaper_path': wp_path,
                'thumbnail_path': thumb_path,
                'filename': wp_file,  # Use wallpaper filename
                'match_type': 'similar'
            })
            matched_wallpapers.add(wp_file)
            matched_thumbnails.add(best_thumb)
            # Remove from unmatched
            if best_thumb in unmatched_thumbnails:
                unmatched_thumbnails.remove(best_thumb)
    
    # Third pass: Create thumbnails for remaining wallpapers
    for wp_file in [f for f in wallpaper_files if f not in matched_wallpapers]:
        wp_path = os.path.join(wallpapers_dir, wp_file)
        images_found.append({
            'wallpaper_path': wp_path,
            'thumbnail_path': wp_path,  # Same file as fallback
            'filename': wp_file,
            'match_type': 'no_thumb'
        })
    
    print(f"    ✅ Matched {len(images_found)} pairs")
    return images_found

def get_all_images_from_folder(folder_path):
    """Get all images from a folder and try to pair them."""
    images_found = []
    all_files = []
    
    for file in os.listdir(folder_path):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            file_path = os.path.join(folder_path, file)
            all_files.append({
                'path': file_path,
                'name': file,
                'size': os.path.getsize(file_path)
            })
    
    if not all_files:
        return images_found
    
    print(f"    📊 Found {len(all_files)} images")
    
    # Sort by size (wallpapers are usually larger than thumbnails)
    all_files.sort(key=lambda x: x['size'], reverse=True)
    
    # Group by similarity
    processed = set()
    
    for i, file_info in enumerate(all_files):
        if file_info['name'] in processed:
            continue
        
        # This is likely a wallpaper (larger file)
        wallpaper_candidate = file_info
        
        # Look for matching thumbnail (smaller, similar name)
        thumbnail_candidate = None
        for j in range(i + 1, len(all_files)):
            other_file = all_files[j]
            if other_file['name'] in processed:
                continue
            
            # Check if names are similar
            similarity_score = similarity(
                os.path.splitext(wallpaper_candidate['name'])[0].lower(),
                os.path.splitext(other_file['name'])[0].lower()
            )
            
            if similarity_score > 0.6:
                thumbnail_candidate = other_file
                break
        
        if thumbnail_candidate:
            images_found.append({
                'wallpaper_path': wallpaper_candidate['path'],
                'thumbnail_path': thumbnail_candidate['path'],
                'filename': wallpaper_candidate['name'],
                'match_type': 'size_based'
            })
            processed.add(wallpaper_candidate['name'])
            processed.add(thumbnail_candidate['name'])
        else:
            # No matching thumbnail found
            images_found.append({
                'wallpaper_path': wallpaper_candidate['path'],
                'thumbnail_path': wallpaper_candidate['path'],  # Same file
                'filename': wallpaper_candidate['name'],
                'match_type': 'no_match'
            })
            processed.add(wallpaper_candidate['name'])
    
    return images_found

def extract_title_from_filename(filename):
    """Extract title from filename - IMPROVED for car names."""
    # Remove extension
    title = os.path.splitext(filename)[0]
    
    # Remove common suffixes
    suffixes_to_remove = [
        '_wallpaper', '_wall', '_background', '_bg', '_desktop',
        '_5k', '_4k', '_2k', '_hd', '_fullhd', '_uhd',
        'wallpaper', 'background', 'desktop', 'mobile'
    ]
    
    for suffix in suffixes_to_remove:
        if title.lower().endswith(suffix):
            title = title[:-len(suffix)]
            break
    
    # Clean up special characters
    title = title.replace('_', ' ').replace(',', ' ').replace('  ', ' ')
    
    # Extract year if present (for cars)
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', title)
    year = year_match.group(0) if year_match else ""
    
    if year:
        # Remove year from title for cleaner processing
        title = title.replace(year, '').strip()
    
    # Clean up
    title = ' '.join(title.split())  # Remove extra spaces
    
    # Capitalize appropriately
    words = title.split()
    capitalized_words = []
    
    for word in words:
        # Preserve known acronyms
        if word.upper() in ['BMW', 'SUV', 'GT', 'GTR', 'HD', '4K', '5K']:
            capitalized_words.append(word.upper())
        # Preserve Roman numerals
        elif re.match(r'^(I{1,3}|IV|V|VI{1,3}|IX|X)$', word.upper()):
            capitalized_words.append(word.upper())
        # Capitalize other words
        else:
            capitalized_words.append(word.capitalize())
    
    title = ' '.join(capitalized_words)
    
    # Add year back at the beginning if it exists
    if year:
        title = f"{year} {title}"
    
    return title.strip() if title else "Untitled Wallpaper"

def generate_tags_from_title(title):
    """Generate tags from title - IMPROVED for cars."""
    # Common car-related tags
    car_brands = [
        'ford', 'chevrolet', 'chev', 'dodge', 'toyota', 'honda', 'bmw', 'mercedes', 
        'audi', 'porsche', 'ferrari', 'lamborghini', 'mustang', 'camaro', 'corvette',
        'charger', 'challenger', 'supra', 'gtr', 'skyline', 'viper', 'jesko'
    ]
    
    car_terms = [
        'muscle', 'sports', 'supercar', 'hypercar', 'race', 'racing', 'drift',
        'drag', 'turbo', 'v8', 'v12', 'engine', 'horsepower', 'torque',
        'modified', 'custom', 'tuned', 'stock', 'concept', 'prototype'
    ]
    
    colors = [
        'black', 'white', 'red', 'blue', 'green', 'yellow', 'orange', 'purple',
        'silver', 'gray', 'gold', 'matte', 'gloss', 'chrome'
    ]
    
    # Extract words from title
    title_lower = title.lower()
    words = re.findall(r'\b[a-zA-Z0-9]+\b', title_lower)
    
    tags = []
    
    # Add car brands
    for brand in car_brands:
        if brand in title_lower:
            tags.append(brand.capitalize())
    
    # Add car terms
    for term in car_terms:
        if term in title_lower:
            tags.append(term.capitalize())
    
    # Add colors
    for color in colors:
        if color in title_lower:
            tags.append(color.capitalize())
    
    # Add other significant words (not too common)
    common_words = {
        'the', 'and', 'or', 'but', 'with', 'for', 'from', 'to', 'in', 'on',
        'at', 'by', 'of', 'a', 'an', 'this', 'that', 'these', 'those',
        'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
        'car', 'cars', 'vehicle', 'auto', 'automobile'
    }
    
    for word in words:
        if (word not in common_words and 
            len(word) > 2 and 
            word not in [t.lower() for t in tags]):
            tags.append(word.capitalize())
    
    # Limit to 8 tags and remove duplicates
    tags = list(dict.fromkeys(tags))[:8]
    
    # If no tags found, add some defaults
    if not tags:
        tags = ['Automotive', 'Vehicle', 'Car']
    
    return ', '.join(tags)

def get_image_info(image_path):
    """Get image resolution and format."""
    try:
        with Image.open(image_path) as img:
            return img.width, img.height, img.format
    except Exception as e:
        print(f"        ❌ Error reading image: {e}")
        return None, None, None

def calculate_aspect_ratio(width, height):
    """Calculate aspect ratio."""
    if width == 0 or height == 0:
        return "0:0"
    
    divisor = gcd(width, height)
    if divisor == 0:
        return "0:0"
    
    simplified_width = width // divisor
    simplified_height = height // divisor
    
    common_ratios = {
        (16, 9): "16:9",
        (4, 3): "4:3",
        (1, 1): "1:1",
        (21, 9): "21:9",
        (9, 16): "9:16",
        (3, 4): "3:4",
        (3, 2): "3:2",
        (2, 3): "2:3",
    }
    
    for (w, h), ratio_str in common_ratios.items():
        if abs(simplified_width/simplified_height - w/h) < 0.1:
            return ratio_str
    
    return f"{simplified_width}:{simplified_height}"

def determine_wallpaper_type(width, height):
    """Determine if desktop or mobile."""
    if height == 0:
        return 'desktop'
    ratio = width / height
    return 'desktop' if ratio >= 1.0 else 'mobile'

def get_quality_label(width, height, wallpaper_type):
    """Get quality label."""
    if wallpaper_type == 'desktop':
        if width >= 3840 or height >= 2160:
            return '4K'
        elif width >= 2560 or height >= 1440:
            return '2K'
        elif width >= 1920 or height >= 1080:
            return 'Full HD'
        else:
            return 'HD'
    else:
        if width >= 1440 or height >= 2560:
            return 'HD'
        elif width >= 1080 or height >= 1920:
            return 'Phone'
        else:
            return 'Tablet'

def extract_color_palette(image_path):
    """Extract color palette from image."""
    try:
        with Image.open(image_path) as img:
            # Resize for processing
            img_small = img.resize((50, 50))
            if img_small.mode != 'RGB':
                img_small = img_small.convert('RGB')
            
            # Get average color
            pixels = np.array(img_small)
            avg_color = pixels.mean(axis=(0, 1)).astype(int)
            
            # Create variations
            primary = tuple(avg_color)
            secondary = tuple((avg_color * 0.8).astype(int))
            accent = tuple((avg_color * 1.2).astype(int))
            
            # Ensure values are in range
            primary = tuple(max(0, min(255, c)) for c in primary)
            secondary = tuple(max(0, min(255, c)) for c in secondary)
            accent = tuple(max(0, min(255, c)) for c in accent)
            
            def rgb_to_hex(rgb):
                return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
            
            palette = {
                "primary": rgb_to_hex(primary),
                "secondary": rgb_to_hex(secondary),
                "accent": rgb_to_hex(accent)
            }
            
            return json.dumps(palette)
            
    except Exception as e:
        print(f"        ⚠ Color extraction error: {e}")
        # Fallback palette
        fallback_palettes = [
            {"primary": "#1a237e", "secondary": "#3949ab", "accent": "#7986cb"},
            {"primary": "#311b92", "secondary": "#5e35b1", "accent": "#9575cd"},
            {"primary": "#004d40", "secondary": "#00695c", "accent": "#26a69a"},
            {"primary": "#bf360c", "secondary": "#e64a19", "accent": "#ff8a65"},
        ]
        return json.dumps(random.choice(fallback_palettes))

def generate_cdn_paths(wallpaper_path, thumbnail_path, category_id, index):
    """Generate CDN paths for image and thumbnail."""
    # Create hash-based unique name
    with open(wallpaper_path, 'rb') as f:
        wp_hash = hashlib.md5(f.read()).hexdigest()[:8]
    
    ext = os.path.splitext(wallpaper_path)[1].lower()
    
    # Simulate CDN paths
    wp_filename = f"cat{category_id:02d}_wp{index:03d}_{wp_hash}{ext}"
    thumb_filename = f"cat{category_id:02d}_thumb{index:03d}_{wp_hash}{ext}"
    
    image_url = f"https://cdn.example.com/wallpapers/{category_id}/{wp_filename}"
    thumbnail_url = f"https://cdn.example.com/thumbnails/{category_id}/{thumb_filename}"
    cdn_path = f"/wallpapers/{category_id}/{wp_filename}"
    
    return image_url, thumbnail_url, cdn_path

def insert_wallpaper(conn, wallpaper_data, category_id, is_desktop=True):
    """Insert wallpaper into database."""
    cursor = conn.cursor()
    
    # Generate random stats
    likes_count = random.randint(1000, 10000)
    favorites_count = random.randint(500, 8000)
    downloads_count = random.randint(100, 5000)
    views_count = random.randint(5000, 50000)
    trending_percentage = random.randint(10, 95) if random.random() > 0.7 else 0
    is_trending = random.random() > 0.7
    is_featured = random.random() > 0.7
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if is_desktop:
        cursor.execute('''
        INSERT INTO wallpapers_desktopwallpaper 
        (title, category_id, tags, color_palette, image_url, thumbnail_url,
         resolution_width, resolution_height, aspect_ratio, file_format,
         cdn_path, quality_label, likes_count, favorites_count, downloads_count,
         views_count, is_trending, trending_percentage, is_featured,
         similarity_score, display_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            wallpaper_data['title'],
            category_id,
            wallpaper_data['tags'],
            wallpaper_data['color_palette'],
            wallpaper_data['image_url'],
            wallpaper_data['thumbnail_url'],
            wallpaper_data['width'],
            wallpaper_data['height'],
            wallpaper_data['aspect_ratio'],
            wallpaper_data['file_format'],
            wallpaper_data['cdn_path'],
            wallpaper_data['quality_label'],
            likes_count,
            favorites_count,
            downloads_count,
            views_count,
            is_trending,
            trending_percentage,
            is_featured,
            0.0,  # similarity_score
            wallpaper_data['display_order'],
            current_time,
            current_time
        ))
        
        # Update desktop count
        cursor.execute('''
        UPDATE wallpapers_category 
        SET desktop_wallpaper_count = desktop_wallpaper_count + 1
        WHERE id = ?
        ''', (category_id,))
    else:
        cursor.execute('''
        INSERT INTO wallpapers_mobilewallpaper 
        (title, category_id, tags, color_palette, image_url, thumbnail_url,
         resolution_width, resolution_height, aspect_ratio, file_format,
         cdn_path, quality_label, device_type, likes_count, favorites_count,
         downloads_count, views_count, is_trending, trending_percentage,
         is_featured, similarity_score, display_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            wallpaper_data['title'],
            category_id,
            wallpaper_data['tags'],
            wallpaper_data['color_palette'],
            wallpaper_data['image_url'],
            wallpaper_data['thumbnail_url'],
            wallpaper_data['width'],
            wallpaper_data['height'],
            wallpaper_data['aspect_ratio'],
            wallpaper_data['file_format'],
            wallpaper_data['cdn_path'],
            wallpaper_data['quality_label'],
            wallpaper_data['device_type'],
            likes_count,
            favorites_count,
            downloads_count,
            views_count,
            is_trending,
            trending_percentage,
            is_featured,
            0.0,  # similarity_score
            wallpaper_data['display_order'],
            current_time,
            current_time
        ))
        
        # Update mobile count
        cursor.execute('''
        UPDATE wallpapers_category 
        SET mobile_wallpaper_count = mobile_wallpaper_count + 1
        WHERE id = ?
        ''', (category_id,))
    
    wallpaper_id = cursor.lastrowid
    conn.commit()
    return wallpaper_id

def process_category(conn, category_id, category_name, base_folder="."):
    """Process all wallpapers for a specific category."""
    print(f"\n📂 Processing: {category_name} (ID: {category_id})")
    
    # Find category folder
    folder_path, actual_folder_name = find_category_folder(category_name, base_folder)
    if not folder_path:
        print(f"    ❌ Folder not found for category: {category_name}")
        return 0, 0, 0, 0
    
    print(f"    📁 Found folder: {actual_folder_name}")
    
    # Scan for images
    images = scan_category_images(folder_path)
    
    if not images:
        print(f"    ⚠ No images found in {actual_folder_name}")
        return 0, 0, 0, 0
    
    print(f"    📊 Processing {len(images)} wallpapers...")
    
    success_count = 0
    error_count = 0
    desktop_count = 0
    mobile_count = 0
    
    # Process each wallpaper
    for i, img_info in enumerate(images, 1):
        wallpaper_path = img_info['wallpaper_path']
        thumbnail_path = img_info['thumbnail_path']
        filename = img_info['filename']
        match_type = img_info.get('match_type', 'unknown')
        
        print(f"\n    [{i}/{len(images)}] {filename[:50]}...")
        print(f"        🔗 Match type: {match_type}")
        
        try:
            # Get image info
            width, height, file_format = get_image_info(wallpaper_path)
            if not width or not height:
                error_count += 1
                continue
            
            # Determine wallpaper type
            wallpaper_type = determine_wallpaper_type(width, height)
            
            # Calculate aspect ratio
            aspect_ratio = calculate_aspect_ratio(width, height)
            
            # Get quality label
            quality_label = get_quality_label(width, height, wallpaper_type)
            
            # Extract title
            title = extract_title_from_filename(filename)
            print(f"        📝 {title}")
            
            # Generate tags
            tags = generate_tags_from_title(title)
            print(f"        🔖 Tags: {tags}")
            
            # Extract color palette
            color_palette = extract_color_palette(wallpaper_path)
            
            # Generate CDN paths
            image_url, thumbnail_url, cdn_path = generate_cdn_paths(
                wallpaper_path, thumbnail_path, category_id, i
            )
            
            # Prepare wallpaper data
            wallpaper_data = {
                'title': title,
                'tags': tags,
                'color_palette': color_palette,
                'image_url': image_url,
                'thumbnail_url': thumbnail_url,
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio,
                'file_format': file_format.upper() if file_format else 'JPEG',
                'cdn_path': cdn_path,
                'quality_label': quality_label,
                'display_order': i * 10,
            }
            
            # Insert into database
            if wallpaper_type == 'desktop':
                wallpaper_id = insert_wallpaper(conn, wallpaper_data, category_id, is_desktop=True)
                desktop_count += 1
                print(f"        ✅ Desktop Wallpaper (ID: {wallpaper_id})")
            else:
                wallpaper_data['device_type'] = 'phone' if width < 1200 else 'tablet'
                wallpaper_id = insert_wallpaper(conn, wallpaper_data, category_id, is_desktop=False)
                mobile_count += 1
                print(f"        ✅ Mobile Wallpaper (ID: {wallpaper_id})")
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"        ❌ Error: {str(e)[:100]}")
    
    return success_count, error_count, desktop_count, mobile_count

def main():
    """Main function."""
    print("=" * 70)
    print("WALLPAPERS DATABASE POPULATOR - SIMILAR FILENAMES FIX")
    print("=" * 70)
    print("This version handles similar (not identical) wallpaper/thumbnail names.")
    
    # Connect to database
    conn = connect_to_database()
    
    # Get all categories
    categories = get_all_categories(conn)
    display_categories(categories)
    
    # Test with Cars category first (ID: 9)
    print("\n⚠ RECOMMENDATION: Test with Cars category first (ID: 9)")
    print("This will show how well it matches similar filenames.")
    
    cat_id = input("\nEnter category ID to test (or press Enter for ID 9): ").strip()
    
    if not cat_id:
        cat_id = "9"
    
    # Find the category
    selected_category = None
    for cat in categories:
        if str(cat['id']) == cat_id:
            selected_category = cat
            break
    
    if not selected_category:
        print(f"❌ Category ID {cat_id} not found")
        conn.close()
        return
    
    print(f"\n✅ Selected: {selected_category['name']} (ID: {selected_category['id']})")
    
    # Process the category
    success, errors, desktop, mobile = process_category(
        conn, selected_category['id'], selected_category['name']
    )
    
    # Show results
    print(f"\n{'='*70}")
    print(f"RESULTS for {selected_category['name']}")
    print(f"{'='*70}")
    print(f"Wallpapers added: {success}")
    print(f"Failed: {errors}")
    print(f"Desktop: {desktop}")
    print(f"Mobile: {mobile}")
    
    # Ask if user wants to process more
    more = input(f"\nProcess another category? (y/n): ").lower()
    
    if more == 'y':
        # Process all categories
        print(f"\n{'='*70}")
        print("PROCESSING ALL CATEGORIES")
        print("="*70)
        
        total_stats = {
            'success': success,
            'errors': errors,
            'desktop': desktop,
            'mobile': mobile,
            'categories': 1 if success > 0 else 0
        }
        
        for cat in categories:
            if cat['id'] == selected_category['id']:
                continue  # Already processed
            
            print(f"\n📂 Processing: {cat['name']} (ID: {cat['id']})")
            s, e, d, m = process_category(conn, cat['id'], cat['name'])
            
            total_stats['success'] += s
            total_stats['errors'] += e
            total_stats['desktop'] += d
            total_stats['mobile'] += m
            total_stats['categories'] += 1 if s > 0 else 0
        
        # Final summary
        print(f"\n{'='*70}")
        print("FINAL SUMMARY")
        print("="*70)
        print(f"Categories processed: {total_stats['categories']}")
        print(f"Total wallpapers added: {total_stats['success']}")
        print(f"Total failed: {total_stats['errors']}")
        print(f"Desktop: {total_stats['desktop']}")
        print(f"Mobile: {total_stats['mobile']}")
    
    # Show updated category counts
    print(f"\n{'='*70}")
    print("UPDATED CATEGORY COUNTS")
    print("="*70)
    print(f"{'ID':<5} {'Category Name':<20} {'Desktop':<10} {'Mobile':<10} {'Total':<10}")
    print("-" * 70)
    
    cursor = conn.cursor()
    for cat in categories:
        cursor.execute("SELECT desktop_wallpaper_count, mobile_wallpaper_count FROM wallpapers_category WHERE id = ?", (cat['id'],))
        counts = cursor.fetchone()
        if counts:
            total = counts['desktop_wallpaper_count'] + counts['mobile_wallpaper_count']
            print(f"{cat['id']:<5} {cat['name']:<20} {counts['desktop_wallpaper_count']:<10} {counts['mobile_wallpaper_count']:<10} {total:<10}")
    
    conn.close()
    print(f"\n✅ All done!")

if __name__ == "__main__":
    main()