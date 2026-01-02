import os
import sys
import django
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
import time
import random
from pathlib import Path

# -----------------------------
# Django Setup - FIXED
# -----------------------------
# Get the directory containing the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up two levels to reach the project root
project_root = os.path.dirname(os.path.dirname(current_dir))

# Add project root to Python path
sys.path.append(project_root)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WallPic.settings')

# Configure Django
try:
    django.setup()
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    print(f"📁 Current directory: {current_dir}")
    print(f"📁 Project root: {project_root}")
    print(f"🔧 DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    sys.exit(1)

from wallpapers.models import Category, DesktopWallpaper

# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "https://4kwallpapers.com"

# Map category names to database Category IDs
CATEGORY_MAPPING = {
    "Black/Dark": 8,
    "Cars": 9,
    "Celebrations": 10,
    "Cute": 11,
    "Fantasy": 12,
    "Flowers": 13,
    "Food": 14,
    "Games": 15,
    "Gradients": 16,
    "CGI": 17,
    "Lifestyle": 18,
    "Love": 19,
    "Military": 20,
    "Minimal": 21,
    "Movies": 22,
    "Music": 23,
    "nature": 3,
    "People": 24,
    "Photography": 25,
    "Quotes": 26,
    "Sci-Fi": 27,
    "Space": 28,
    "Sports": 29,
    "Technology": 30,
    "World": 31,
}

# Define ALL categories to scrape
ALL_CATEGORIES = [
    "nature",
]

# -----------------------------
# Helper Functions
# -----------------------------
def clean(text):
    """Clean text for use in filenames or titles"""
    if not text:
        return ""
    return re.sub(r"\s+", "_", re.sub(r"[\\/*?:\"<>|]", "", text.strip()))

def extract_title_from_text(text, category_name):
    """Extract and format title from text"""
    if not text:
        return f"{category_name} Wallpaper"
    
    # Clean the title
    title = text.replace('_', ' ').replace('-', ' ')
    title = re.sub(r'\b\d+K\b', '', title)  # Remove resolution like 5K, 8K
    title = re.sub(r'\b\d+\s*K\b', '', title)
    title = re.sub(r'\b\d{4}\b', '', title)  # Remove years
    title = re.sub(r'\(\d+\)', '', title)  # Remove numbers in parentheses
    title = re.sub(r'[^\w\s-]', '', title)  # Remove special chars
    title = re.sub(r'\s+', ' ', title).strip()  # Remove extra spaces
    
    # Capitalize words
    title = ' '.join(word.capitalize() for word in title.split())
    
    # Handle common terms
    title = title.replace('Amoled', 'AMOLED')
    title = title.replace('Ai ', 'AI ')
    title = title.replace('3d', '3D')
    title = title.replace('Ultrawide', 'Ultrawide')
    title = title.replace('Vs ', 'vs ')
    
    # Add category context if title is generic
    if len(title.split()) < 2:
        title = f"{category_name} {title}"
    
    return title if title else f"{category_name} Wallpaper"

def get_random_resolution(category_name=None):
    """Get random desktop resolution based on category"""
    # Base resolutions with weights
    resolutions = [
        (1920, 1080),  # Full HD (most common)
        (2560, 1440),  # 2K
        (3840, 2160),  # 4K (common for wallpapers)
        (5120, 2880),  # 5K
        (7680, 4320),  # 8K
    ]
    
    weights = [0.3, 0.2, 0.4, 0.05, 0.05]  # Weighted probabilities
    
    # Adjust based on category
    if category_name in ['Photography', 'Nature', 'Architecture', 'Space']:
        # Higher quality for these categories
        return random.choices([(3840, 2160), (5120, 2880), (7680, 4320)], 
                             weights=[0.6, 0.3, 0.1])[0]
    elif category_name in ['Abstract', 'Minimal', 'Black/Dark', 'Gradients']:
        # Standard resolutions for these
        return random.choices([(1920, 1080), (2560, 1440), (3840, 2160)], 
                             weights=[0.4, 0.3, 0.3])[0]
    else:
        return random.choices(resolutions, weights=weights)[0]

def get_quality_label(resolution_height):
    """Get quality label based on resolution height"""
    if resolution_height <= 720:
        return 'HD'
    elif resolution_height <= 1080:
        return 'Full HD'
    elif resolution_height <= 1440:
        return '2K'
    elif resolution_height <= 2160:
        return '4K'
    else:
        return '8K'

def get_color_palette_for_category(category_name):
    """Generate appropriate color palette based on category"""
    
    # Category-specific color palettes
    category_colors = {
        'Anime': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'],
        'nature': ['#2E8B57', '#228B22', '#32CD32', '#9ACD32', '#6B8E23', '#556B2F'],
        'Space': ['#000033', '#000066', '#330066', '#6600CC', '#9933FF', '#CC99FF'],
        'Sci-Fi': ['#00FFFF', '#00CED1', '#20B2AA', '#008B8B', '#5F9EA0', '#4682B4'],
        'Love': ['#FF69B4', '#FF1493', '#DB7093', '#C71585', '#FFB6C1', '#FFC0CB'],
        'Abstract': ['#FF4500', '#FF8C00', '#FFD700', '#ADFF2F', '#7FFF00', '#00FF7F'],
        'Minimal': ['#FFFFFF', '#F5F5F5', '#E8E8E8', '#D3D3D3', '#A9A9A9', '#696969'],
        'Black/Dark': ['#000000', '#1C1C1C', '#2F2F2F', '#4F4F4F', '#696969', '#808080'],
        'Architecture': ['#708090', '#778899', '#B0C4DE', '#4682B4', '#5F9EA0', '#6495ED'],
        'Technology': ['#1E90FF', '#00BFFF', '#87CEEB', '#000080', '#191970', '#4169E1'],
        'Animals': ['#8B4513', '#A0522D', '#CD853F', '#D2691E', '#F4A460', '#DEB887'],
        'Food': ['#FF6347', '#FF4500', '#FF8C00', '#FFD700', '#FFA500', '#FF7F50'],
        'Flowers': ['#FF69B4', '#FF1493', '#DB7093', '#C71585', '#DA70D6', '#EE82EE'],
        'Fantasy': ['#9370DB', '#8A2BE2', '#9400D3', '#9932CC', '#BA55D3', '#DDA0DD'],
        'Games': ['#32CD32', '#00FA9A', '#00FF7F', '#3CB371', '#2E8B57', '#228B22'],
        'Movies': ['#DC143C', '#B22222', '#8B0000', '#FF0000', '#FF4500', '#FF6347'],
        'Music': ['#FFD700', '#FFA500', '#FF8C00', '#FF6347', '#FF4500', '#FF0000'],
        'Sports': ['#1E90FF', '#0000FF', '#0000CD', '#000080', '#191970', '#4169E1'],
        'World': ['#008000', '#006400', '#228B22', '#2E8B57', '#3CB371', '#32CD32'],
        'Cars': ['#FF0000', '#DC143C', '#B22222', '#8B0000', '#FF4500', '#FF6347'],
        'Bikes': ['#FF0000', '#FF4500', '#FF8C00', '#FFA500', '#FFD700', '#FFFF00'],
        'Military': ['#556B2F', '#6B8E23', '#808000', '#9ACD32', '#ADFF2F', '#7FFF00'],
        'People': ['#FFB6C1', '#FFC0CB', '#FF69B4', '#FF1493', '#DB7093', '#C71585'],
        'Lifestyle': ['#87CEEB', '#87CEFA', '#00BFFF', '#1E90FF', '#6495ED', '#4682B4'],
        'Celebrations': ['#FFD700', '#FFA500', '#FF8C00', '#FF6347', '#FF4500', '#FF0000'],
        'Cute': ['#FFB6C1', '#FFC0CB', '#FF69B4', '#FF1493', '#DB7093', '#C71585'],
        'Gradients': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'],
        'CGI': ['#00FFFF', '#00CED1', '#20B2AA', '#008B8B', '#5F9EA0', '#4682B4'],
        'Quotes': ['#FFFFFF', '#F5F5F5', '#E8E8E8', '#D3D3D3', '#A9A9A9', '#696969'],
        'Photography': ['#2F4F4F', '#708090', '#778899', '#B0C4DE', '#4682B4', '#5F9EA0'],
    }
    
    # Get colors for category or use default
    colors = category_colors.get(category_name, [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ])
    
    return {
        "primary": random.choice(colors),
        "secondary": random.choice(colors),
        "accent": random.choice(colors),
    }

def get_tags_from_title(title, category_name):
    """Extract tags from title"""
    tags = set()
    
    # Add category name as tag
    tags.add(category_name.lower())
    
    # Category-specific tags
    category_tags = {
        'Anime': ['anime', 'manga', 'japanese', 'cartoon', 'character', 'fanart'],
        'nature': ['nature', 'outdoor', 'landscape', 'scenery', 'environment'],
        'Space': ['space', 'cosmos', 'universe', 'stars', 'galaxy', 'astronomy'],
        'Sci-Fi': ['scifi', 'futuristic', 'technology', 'cyberpunk', 'future'],
        'Love': ['love', 'romance', 'heart', 'affection', 'relationship'],
        'Abstract': ['abstract', 'art', 'design', 'pattern', 'colorful'],
        'Photography': ['photography', 'photo', 'camera', 'shot', 'picture'],
        'Architecture': ['architecture', 'building', 'city', 'urban', 'structure'],
        'Technology': ['technology', 'tech', 'digital', 'innovation', 'future'],
        'Minimal': ['minimal', 'simple', 'clean', 'modern', 'minimalist'],
        'Animals': ['animals', 'wildlife', 'pet', 'creature', 'animal'],
        'Food': ['food', 'cuisine', 'cooking', 'delicious', 'meal'],
        'Flowers': ['flowers', 'blossom', 'bloom', 'garden', 'plant'],
        'Fantasy': ['fantasy', 'magical', 'mythical', 'legend', 'dream'],
        'Games': ['games', 'gaming', 'video games', 'play', 'entertainment'],
        'Movies': ['movies', 'film', 'cinema', 'hollywood', 'actor'],
        'Music': ['music', 'song', 'instrument', 'melody', 'sound'],
        'Sports': ['sports', 'game', 'athlete', 'competition', 'team'],
        'World': ['world', 'global', 'earth', 'planet', 'travel'],
        'Cars': ['cars', 'automobile', 'vehicle', 'racing', 'speed'],
        'Bikes': ['bikes', 'motorcycle', 'cycling', 'ride', 'speed'],
        'Military': ['military', 'army', 'soldier', 'defense', 'war'],
        'People': ['people', 'human', 'person', 'portrait', 'face'],
        'Lifestyle': ['lifestyle', 'living', 'culture', 'style', 'trend'],
        'Celebrations': ['celebration', 'party', 'festival', 'event', 'holiday'],
        'Cute': ['cute', 'adorable', 'sweet', 'lovely', 'charming'],
        'Gradients': ['gradient', 'colorful', 'rainbow', 'spectrum', 'blend'],
        'CGI': ['cgi', '3d', 'computer graphics', 'digital art', 'render'],
        'Quotes': ['quotes', 'inspiration', 'motivation', 'words', 'text'],
        'Black/Dark': ['dark', 'black', 'gothic', 'night', 'moody'],
    }
    
    # Add category-specific tags
    if category_name in category_tags:
        for tag in category_tags[category_name]:
            tags.add(tag)
    
    # Add generic tags
    generic_tags = ['wallpaper', 'art', 'digital', 'illustration', 'background', 'desktop', '4k', 'hd', 'high quality']
    for tag in generic_tags:
        tags.add(tag)
    
    # Add words from title as tags
    words = title.lower().split()
    for word in words:
        if len(word) > 2 and word not in ['the', 'and', 'for', 'with', 'from', 'this', 'that']:
            tags.add(word)
    
    # Join tags as comma-separated string
    return ', '.join(sorted(list(tags))[:15])  # Limit to 15 tags

# -----------------------------
# Scraping Functions - CORRECTED
# -----------------------------
def get_wallpaper_data(category, page):
    """Scrape wallpaper data from list page - FIXED PAGINATION"""
    # Format URL path based on category
    if category == "Black/Dark":
        path = "black-dark"
    elif category == "Sci-Fi":
        path = "sci-fi"
    elif category == "CGI":
        path = "3d"
    else:
        path = category.lower().replace(" ", "-").replace("/", "-")
    
    # FIXED: Always use page parameter, even for page 1
    url = f"{BASE_URL}/{path}?page={page}"
    
    print(f"      Fetching: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=30)
        
        # Check if page exists
        if r.status_code != 200:
            print(f"      ❌ Failed with status: {r.status_code}")
            return [], False
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Check if page has content (not a "no results" page)
        no_results = soup.select_one(".no-results, .nothing-found, .error-404")
        if no_results:
            print(f"      ⚠️  No more results on page {page}")
            return [], False
        
        # Try different selectors for wallpaper items
        selectors = [".wallpapers__item", "article", ".item", ".wallpaper-item", ".grid-item"]
        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break
        
        if not items:
            # If no items found with selectors, try to find any wallpaper containers
            items = soup.find_all(class_=re.compile(r'(wallpaper|item|article)'))
        
        data = []
        for item in items:
            # Try to find link and image
            a = None
            img = None
            
            # Try different ways to find the link
            for selector in ["a[href$='.html']", "a.detail-link", "a[href*='/wallpaper/']", "a"]:
                a = item.select_one(selector)
                if a and '.html' in a.get('href', ''):
                    break
            
            # Try different ways to find the image
            for selector in ["img", "img.lazyload", "img[data-src]", "img.thumbnail"]:
                img = item.select_one(selector)
                if img:
                    break
            
            if not a or not img:
                continue
            
            # Get title from alt text or generate from URL
            title = img.get("alt") or ""
            if not title:
                # Extract from URL as fallback
                href = a.get("href", "")
                if href:
                    title = href.split('/')[-1].replace('.html', '').replace('-', ' ')
            
            # Get image source
            img_src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
            
            # Only add if we have valid data
            if title or img_src:
                data.append({
                    "title": clean(title),
                    "detail_url": urljoin(BASE_URL, a["href"]),
                    "thumbnail": urljoin(BASE_URL, img_src) if img_src else "",
                })
        
        # FIXED: Remove faulty pagination detection
        # We'll let the main loop control pagination based on max_pages
        # and stop when we get no data or hit an error
        
        print(f"      Found {len(data)} wallpapers on page {page}")
        
        # Return data and True to continue if we found items
        if data:
            return data, True
        else:
            print(f"      ⚠️  No wallpapers found on page {page}, stopping")
            return [], False
        
    except Exception as e:
        print(f"      ❌ Error scraping page {page}: {str(e)[:100]}")
        return [], False

def extract_full_image(detail_url):
    """Extract full image URL from detail page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        r = requests.get(detail_url, headers=headers, timeout=30)
        if r.status_code != 200:
            return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Strategy 1: Look for download buttons
        download_selectors = [
            "a.download", "a[href*='download']", "a[href*='original']",
            "a[href*='full']", "a[href*='4k']", "a[href*='UHD']",
            "a.btn-download", "a[class*='download']"
        ]
        
        for selector in download_selectors:
            for a in soup.select(selector):
                href = a.get("href")
                if href and any(ext in href.lower() for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]):
                    full_url = urljoin(BASE_URL, href)
                    print(f"        Found via download button: {full_url[:80]}...")
                    return full_url
        
        # Strategy 2: Look for high-resolution image links in content
        for a in soup.select("a[href]"):
            href = a.get("href")
            if href:
                href_lower = href.lower()
                if any(ext in href_lower for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]):
                    # Check for resolution indicators
                    if any(indicator in href_lower for indicator in ['4k', 'uhd', 'hd', '3840', '2160', '5120', '2880']):
                        full_url = urljoin(BASE_URL, href)
                        print(f"        Found via resolution link: {full_url[:80]}...")
                        return full_url
        
        # Strategy 3: Find the main wallpaper image
        img_selectors = [
            "img.wallpaper", "img.full", "img.original",
            "img[src*='4k']", "img[src*='wallpaper']", "img[src*='UHD']",
            "img#wallpaper", "img.main-image", ".wallpaper img",
            "img[src*='/wallpapers/']", "img[src*='/full/']"
        ]
        
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img and img.get("src"):
                full_url = urljoin(BASE_URL, img["src"])
                print(f"        Found via image selector: {full_url[:80]}...")
                return full_url
        
        # Strategy 4: Look for meta tags with image URLs
        meta_tags = soup.select("meta[property='og:image'], meta[name='og:image'], meta[content*='.jpg'], meta[content*='.png']")
        for meta in meta_tags:
            content = meta.get("content")
            if content and any(ext in content.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                full_url = urljoin(BASE_URL, content)
                print(f"        Found via meta tag: {full_url[:80]}...")
                return full_url
        
        # Strategy 5: Last resort - find largest image
        images = soup.find_all("img", src=True)
        if images:
            # Prefer images with certain keywords
            for img in images:
                src = img.get("src")
                if src and any(keyword in src.lower() for keyword in ['wallpaper', '4k', 'full', 'original']):
                    full_url = urljoin(BASE_URL, src)
                    print(f"        Found via keyword match: {full_url[:80]}...")
                    return full_url
            
            # Return first valid image as fallback
            for img in images:
                src = img.get("src")
                if src and src.startswith('http'):
                    full_url = urljoin(BASE_URL, src)
                    print(f"        Found via fallback: {full_url[:80]}...")
                    return full_url
        
        print(f"        ⚠️  Could not find full image")
        return None
        
    except Exception as e:
        print(f"        ❌ Error extracting full image: {str(e)[:100]}")
        return None

# -----------------------------
# Database Functions - MODIFIED (REMOVED DUPLICATE CHECK)
# -----------------------------
def save_wallpaper_to_db(wallpaper_data, category_obj, item_num):
    """Save a wallpaper to the database - NO DUPLICATE CHECKING"""
    try:
        # Skip if no image URL
        if not wallpaper_data.get("wallpaper") and not wallpaper_data.get("thumbnail"):
            return "error"
        
        # Use full image URL for duplicate check, fallback to thumbnail
        image_url = wallpaper_data.get("wallpaper") or wallpaper_data.get("thumbnail", "")
        
        if not image_url:
            return "error"
        
        # Extract and format title
        title = extract_title_from_text(wallpaper_data["title"], category_obj.name)
        
        # Make title unique if needed
        base_title = title
        counter = 1
        while DesktopWallpaper.objects.filter(title=title, category=category_obj).exists():
            title = f"{base_title} {counter}"
            counter += 1
        
        # Get resolution
        width, height = get_random_resolution(category_obj.name)
        
        # Generate tags
        tags = get_tags_from_title(title, category_obj.name)
        
        # Generate engagement metrics with some randomness
        likes = random.randint(50, 2500)
        views = random.randint(1000, 50000)
        downloads = random.randint(100, 10000)
        
        # Calculate trending probability (higher for newer items)
        is_trending_prob = min(0.15 + (item_num / 100), 0.3)  # Up to 30% chance
        is_trending = random.random() < is_trending_prob
        
        # Create wallpaper entry
        wallpaper = DesktopWallpaper(
            title=title,
            category=category_obj,
            tags=tags,
            color_palette=get_color_palette_for_category(category_obj.name),
            image_url=wallpaper_data.get("wallpaper") or wallpaper_data.get("thumbnail", ""),
            thumbnail_url=wallpaper_data.get("thumbnail", ""),
            resolution_width=width,
            resolution_height=height,
            aspect_ratio=f"{width}:{height}",
            file_format='JPEG',
            quality_label=get_quality_label(height),
            likes_count=likes,
            favorites_count=random.randint(0, int(likes * 0.7)),
            downloads_count=downloads,
            views_count=views,
            is_trending=is_trending,
            trending_percentage=random.randint(1, 5) if is_trending else 0,
            is_featured=random.random() < 0.03,  # 3% chance to be featured
            display_order=item_num,
        )
        
        wallpaper.save()
        return "success"
        
    except Exception as e:
        print(f"      ❌ Error saving to DB: {str(e)}")
        return "error"

# -----------------------------
# Main Scraping Function - CORRECTED
# -----------------------------
def scrape_and_insert_category(category_name, max_pages=16, max_items=500):
    """Scrape a category and insert directly into database - FIXED PAGINATION"""
    print(f"\n🚀 SCRAPING: {category_name}")
    
    # Get category from database
    if category_name not in CATEGORY_MAPPING:
        print(f"   ❌ Category '{category_name}' not in mapping!")
        return {"total": 0, "success": 0, "errors": 0}
    
    category_id = CATEGORY_MAPPING[category_name]
    try:
        category_obj = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        print(f"   ❌ Category ID {category_id} not found in database!")
        return {"total": 0, "success": 0, "errors": 0}
    
    page = 1
    total_scraped = 0
    stats = {"total": 0, "success": 0, "errors": 0}
    
    while page <= max_pages and total_scraped < max_items:
        print(f"   📄 Page {page}/{max_pages}...")
        
        # Scrape wallpaper data - FIXED: This now correctly paginates
        data, has_more = get_wallpaper_data(category_name, page)
        
        # If no data returned, stop scraping this category
        if not data:
            print(f"   ⚠️  No data returned on page {page}, stopping category")
            break
        
        # Process each wallpaper
        for i, wp in enumerate(data):
            if total_scraped >= max_items:
                print(f"   ⚠️  Reached max items ({max_items}) for category")
                break
                
            print(f"      [{total_scraped + 1}/{max_items}] Processing...", end="\r")
            
            # Extract full image URL
            wp["wallpaper"] = extract_full_image(wp["detail_url"])
            
            # Save to database
            result = save_wallpaper_to_db(wp, category_obj, total_scraped)
            
            stats["total"] += 1
            if result == "success":
                stats["success"] += 1
                print(f"      ✅ Added: {wp['title'][:50]}...")
            else:
                stats["errors"] += 1
                print(f"      ❌ Error: {wp['title'][:50]}...")
            
            total_scraped += 1
            
            # Small delay to be polite to the server
            time.sleep(0.5)
        
        print(f"   ✅ Page {page} completed: {len(data)} items processed")
        
        # FIXED: Check if we should continue to next page
        # Continue to next page only if:
        # 1. We haven't reached max_pages
        # 2. We haven't reached max_items
        # 3. The last page had data (has_more is True)
        if page >= max_pages or total_scraped >= max_items or not has_more:
            break
            
        page += 1
        time.sleep(2)  # Longer delay between pages to be polite
    
    print(f"   🎯 Category completed: {total_scraped} items total")
    
    # Update category count
    if stats["success"] > 0:
        category_obj.desktop_wallpaper_count = category_obj.desktop_wallpapers.count()
        category_obj.save(update_fields=['desktop_wallpaper_count'])
    
    return stats

# -----------------------------
# Main Function
# -----------------------------
def main():
    """Main function - scrape and insert wallpapers"""
    print("\n" + "="*80)
    print("🌐 COMPLETE WALLPAPER SCRAPER & DATABASE INSERTER - NO DUPLICATE CHECK")
    print("="*80)
    
    # Show database summary
    try:
        total_categories = Category.objects.count()
        total_desktop = DesktopWallpaper.objects.count()
        
        print(f"\n📊 DATABASE SUMMARY:")
        print(f"   Categories: {total_categories}")
        print(f"   Existing Wallpapers: {total_desktop:,}")
    except Exception as e:
        print(f"\n⚠️  Could not access database: {e}")
        print("Please check your Django setup and database connection.")
        return
    
    # Show all categories to scrape
    print(f"\n🎯 ALL CATEGORIES TO SCRAPE ({len(ALL_CATEGORIES)}):")
    print("-" * 80)
    for i, cat in enumerate(ALL_CATEGORIES, 1):
        category_id = CATEGORY_MAPPING.get(cat, "N/A")
        try:
            category_obj = Category.objects.get(id=category_id)
            existing_count = category_obj.desktop_wallpaper_count
        except:
            existing_count = 0
        print(f"   {i:2}. {cat:20} (DB ID: {category_id:2}) - Existing: {existing_count:4}")
    print("-" * 80)
    
    # Get user input with defaults
    print("\n" + "-"*80)
    print("CONFIGURATION (Press Enter for defaults):")
    print("-"*80)
    
    try:
        max_pages_input = input(f"Max pages per category (1-20, default 16): ").strip()
        max_pages = int(max_pages_input) if max_pages_input else 16
        max_pages = max(1, min(20, max_pages))
        
        max_items_input = input(f"Max items per category (1-2000, default 500): ").strip()
        max_items = int(max_items_input) if max_items_input else 500
        max_items = max(1, min(2000, max_items))
        
        # Ask which categories to scrape
        print(f"\nSelect categories to scrape:")
        print("   [A] All categories ({})".format(len(ALL_CATEGORIES)))
        print("   [S] Select specific categories")
        
        choice = input("Your choice (A/S, default A): ").strip().upper() or "A"
        
        if choice == "S":
            print("\nAvailable categories:")
            for i, cat in enumerate(ALL_CATEGORIES, 1):
                print(f"   {i:2}. {cat}")
            
            selections = input("\nEnter category numbers (comma separated, e.g., 1,3,5): ").strip()
            if selections:
                indices = [int(x.strip()) - 1 for x in selections.split(",") if x.strip().isdigit()]
                categories_to_scrape = [ALL_CATEGORIES[i] for i in indices if 0 <= i < len(ALL_CATEGORIES)]
                if not categories_to_scrape:
                    print("⚠️  No valid categories selected, using all categories")
                    categories_to_scrape = ALL_CATEGORIES
            else:
                categories_to_scrape = ALL_CATEGORIES
        else:
            categories_to_scrape = ALL_CATEGORIES
        
        print(f"\nWill scrape {len(categories_to_scrape)} categories:")
        for cat in categories_to_scrape:
            print(f"   - {cat}")
        
        confirm = input(f"\nStart scraping? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Operation cancelled.")
            return
            
    except ValueError:
        print("Invalid input. Using defaults.")
        max_pages = 16
        max_items = 500
        categories_to_scrape = ALL_CATEGORIES
    
    print("\n" + "="*80)
    print("STARTING MASS SCRAPING PROCESS")
    print("="*80)
    print(f"Settings: Max {max_pages} pages, Max {max_items} items per category")
    
    total_stats = {"total": 0, "success": 0, "errors": 0}
    start_time = time.time()
    
    # Scrape each category
    for i, category in enumerate(categories_to_scrape, 1):
        print(f"\n[{i}/{len(categories_to_scrape)}] ", end="")
        
        category_start = time.time()
        stats = scrape_and_insert_category(category, max_pages, max_items)
        category_time = time.time() - category_start
        
        # Accumulate totals
        for key in total_stats:
            total_stats[key] += stats[key]
        
        print(f"   ⏱️  Time: {category_time:.1f}s")
        print(f"   📊 Results: ✅ {stats['success']} added, ❌ {stats['errors']} errors")
        
        # Save progress after each category
        progress = {
            "category": category,
            "stats": stats,
            "time_seconds": category_time,
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Create progress directory if it doesn't exist
        os.makedirs("scraping_logs", exist_ok=True)
        progress_file = f"scraping_logs/progress_{time.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(progress_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(progress) + "\n")
        
        # Brief pause between categories
        if i < len(categories_to_scrape):
            print(f"\n   ⏳ Pausing 5 seconds before next category...")
            time.sleep(5)
    
    total_time = time.time() - start_time
    
    # Final summary
    print("\n" + "="*80)
    print("SCRAPING COMPLETE - FINAL SUMMARY")
    print("="*80)
    
    print(f"\n⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Categories processed: {len(categories_to_scrape)}")
    print(f"   ✅ New wallpapers added: {total_stats['success']:,}")
    print(f"   ❌ Errors encountered: {total_stats['errors']:,}")
    print(f"   📄 Total processed: {total_stats['total']:,}")
    
    if total_stats['total'] > 0:
        success_rate = (total_stats['success'] / total_stats['total']) * 100
        print(f"   📈 Success rate: {success_rate:.1f}%")
    
    # Show updated category counts
    try:
        print(f"\n📈 UPDATED CATEGORY COUNTS:")
        print("-" * 50)
        categories = Category.objects.filter(id__in=[CATEGORY_MAPPING[c] for c in categories_to_scrape]).order_by('id')
        for cat in categories:
            print(f"   {cat.name:20}: {cat.desktop_wallpaper_count:4} wallpapers")
        
        # Total count
        new_total = DesktopWallpaper.objects.count()
        added = new_total - total_desktop
        
        print("\n" + "="*80)
        print(f"🏁 TOTAL WALLPAPERS IN DATABASE: {new_total:,}")
        print(f"📥 Added in this session: {added:,}")
        print("="*80)
    except Exception as e:
        print(f"\n⚠️  Could not retrieve final database counts: {e}")
    
    # Save comprehensive summary to JSON file
    summary = {
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_time_seconds": total_time,
        "categories_scraped": categories_to_scrape,
        "max_pages_per_category": max_pages,
        "max_items_per_category": max_items,
        "results": total_stats,
        "success_rate_percentage": (total_stats['success'] / total_stats['total'] * 100) if total_stats['total'] > 0 else 0,
    }
    
    try:
        summary["final_total"] = DesktopWallpaper.objects.count()
        summary["added_this_session"] = summary["final_total"] - total_desktop
        
        # Add per-category details
        summary["category_details"] = {}
        for cat in categories_to_scrape:
            if cat in CATEGORY_MAPPING:
                try:
                    category_obj = Category.objects.get(id=CATEGORY_MAPPING[cat])
                    summary["category_details"][cat] = {
                        "id": category_obj.id,
                        "final_count": category_obj.desktop_wallpaper_count
                    }
                except:
                    pass
    except:
        pass
    
    summary_file = f"scraping_logs/summary_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📁 Summary saved to: {summary_file}")
    print(f"📊 Progress logs saved to: scraping_logs/")
    
    # Create a simple HTML report
    html_report = f"""
    <html>
    <head><title>Scraping Report - {time.strftime('%Y-%m-%d %H:%M:%S')}</title></head>
    <body>
    <h1>Wallpaper Scraping Report</h1>
    <p>Date: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Total Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)</p>
    <h2>Results</h2>
    <ul>
        <li>Categories processed: {len(categories_to_scrape)}</li>
        <li>New wallpapers added: {total_stats['success']:,}</li>
        <li>Errors encountered: {total_stats['errors']:,}</li>
        <li>Total processed: {total_stats['total']:,}</li>
        <li>Success rate: {(total_stats['success'] / total_stats['total'] * 100) if total_stats['total'] > 0 else 0:.1f}%</li>
    </ul>
    </body>
    </html>
    """
    
    html_file = f"scraping_logs/report_{time.strftime('%Y%m%d_%H%M%S')}.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_report)
    
    print(f"📄 HTML report saved to: {html_file}")

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    try:
        main()
        print("\n✨ All done! Press Enter to exit...")
        input()
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nPress Enter to exit...")
        input()