# populate_categories_fixed_counts.py
import sqlite3
import os

def connect_to_database():
    """Connect to SQLite database."""
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def update_category_counts(conn):
    """Manually update category counts for all categories."""
    print("\n" + "=" * 60)
    print("UPDATING CATEGORY COUNTS")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    # Get all categories
    cursor.execute("SELECT id, name FROM wallpapers_category")
    categories = cursor.fetchall()
    
    for category in categories:
        category_id = category['id']
        category_name = category['name']
        
        # Count desktop wallpapers in this category
        cursor.execute("SELECT COUNT(*) as count FROM wallpapers_desktopwallpaper WHERE category_id = ?", (category_id,))
        desktop_count = cursor.fetchone()['count']
        
        # Count mobile wallpapers in this category
        cursor.execute("SELECT COUNT(*) as count FROM wallpapers_mobilewallpaper WHERE category_id = ?", (category_id,))
        mobile_count = cursor.fetchone()['count']
        
        # Update the category with both counts
        cursor.execute('''
        UPDATE wallpapers_category 
        SET desktop_wallpaper_count = ?, 
            mobile_wallpaper_count = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (desktop_count, mobile_count, category_id))
        
        print(f"  {category_name:20} - Desktop: {desktop_count:3} | Mobile: {mobile_count:3}")
    
    conn.commit()
    print("\n✅ Category counts updated!")

def check_existing_categories(conn):
    """Check what categories already exist."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, desktop_wallpaper_count, mobile_wallpaper_count FROM wallpapers_category ORDER BY id")
    existing_categories = cursor.fetchall()
    
    print("Existing categories:")
    for cat in existing_categories:
        print(f"  ID: {cat['id']} - {cat['name']:20} Desktop: {cat['desktop_wallpaper_count']} Mobile: {cat['mobile_wallpaper_count']}")
    
    return existing_categories

def ensure_anime_category_exists(conn):
    """Ensure Anime category exists with ID=1."""
    cursor = conn.cursor()
    
    # Check if Anime exists
    cursor.execute("SELECT id FROM wallpapers_category WHERE name = 'Anime'")
    anime_exists = cursor.fetchone()
    
    if anime_exists:
        print(f"Anime category already exists with ID: {anime_exists[0]}")
        return anime_exists[0]
    
    # Check if there's already a category with ID=1
    cursor.execute("SELECT name FROM wallpapers_category WHERE id = 1")
    id_1_exists = cursor.fetchone()
    
    if id_1_exists:
        print(f"Category with ID=1 is: {id_1_exists['name']}")
        # Don't rename, just return existing ID
        return 1
    else:
        # Insert Anime with ID=1
        try:
            cursor.execute("INSERT INTO wallpapers_category (id, name, slug, description, display_order, is_active) VALUES (1, 'Anime', 'anime', 'Anime and manga themed wallpapers', 10, 1)")
            print("Created Anime category with ID=1")
            return 1
        except sqlite3.IntegrityError:
            # If insertion fails due to ID constraint, get next available ID
            cursor.execute("INSERT INTO wallpapers_category (name, slug, description, display_order, is_active) VALUES ('Anime', 'anime', 'Anime and manga themed wallpapers', 10, 1)")
            anime_id = cursor.lastrowid
            print(f"Created Anime category with ID: {anime_id}")
            return anime_id

def create_or_update_category(conn, name, description, display_order, cover_image_url=""):
    """Create or update a category."""
    cursor = conn.cursor()
    
    # Create slug from name
    slug = name.lower().replace(' ', '-').replace('/', '-').replace('&', 'and').replace('(', '').replace(')', '')
    
    # Check if category already exists
    cursor.execute("SELECT id FROM wallpapers_category WHERE name = ? OR slug = ?", (name, slug))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing category
        cursor.execute('''
        UPDATE wallpapers_category 
        SET description = ?, display_order = ?, is_active = ?
        WHERE id = ?
        ''', (description, display_order, 1, existing[0]))
        print(f"  Updated category: {name} (ID: {existing[0]})")
        return existing[0]
    else:
        # Insert new category
        # Check if cover_image_url column exists
        cursor.execute("PRAGMA table_info(wallpapers_category)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'cover_image_url' in columns:
            cursor.execute('''
            INSERT INTO wallpapers_category 
            (name, slug, description, cover_image_url, display_order, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, slug, description, cover_image_url, display_order, 1))
        else:
            cursor.execute('''
            INSERT INTO wallpapers_category 
            (name, slug, description, display_order, is_active)
            VALUES (?, ?, ?, ?, ?)
            ''', (name, slug, description, display_order, 1))
        
        new_id = cursor.lastrowid
        print(f"  Created category: {name} (ID: {new_id})")
        return new_id

def populate_categories():
    """Populate all categories."""
    print("=" * 60)
    print("POPULATING CATEGORIES")
    print("=" * 60)
    
    # Connect to database
    conn = connect_to_database()
    
    # Check existing categories
    print("\nChecking existing categories...")
    existing_categories = check_existing_categories(conn)
    
    # Ensure Anime exists
    print("\nEnsuring Anime category exists...")
    anime_id = ensure_anime_category_exists(conn)
    print(f"Anime category ID: {anime_id}")
    
    # Define all categories with their descriptions and display order
    categories = [
        # Anime is already handled above
        ("Anime", "Anime and manga themed wallpapers featuring characters from popular series", 10, "https://i.ibb.co/k2nnQh7W/JUJUTSU-KAISEN-Hidden-Inventory-Premature-Death-Wallpaper.jpg"),
        
        # All other categories from your list
        ("Abstract", "Abstract art, geometric patterns, and digital designs", 20, ""),
        ("Animals", "Animal photography and illustrations", 30, ""),
        ("Architecture", "Buildings, structures, and urban landscapes", 40, ""),
        ("Bikes", "Motorcycles, bicycles, and riding themes", 50, ""),
        ("Black/Dark", "Dark mode and black-themed wallpapers", 60, ""),
        ("Cars", "Automobiles, supercars, and racing themes", 70, ""),
        ("Celebrations", "Holidays, festivals, and celebration themes", 80, ""),
        ("Cute", "Cute, kawaii, and adorable wallpapers", 90, ""),
        ("Fantasy", "Fantasy art, mythical creatures, and magical worlds", 100, ""),
        ("Flowers", "Floral patterns, botanical art, and garden themes", 110, ""),
        ("Food", "Food photography and culinary themes", 120, ""),
        ("Games", "Video game characters, scenes, and artwork", 130, ""),
        ("Gradients", "Color gradient and smooth color transition wallpapers", 140, ""),
        ("CGI", "Computer-generated imagery and 3D renderings", 150, ""),
        ("Lifestyle", "Everyday life, travel, and lifestyle themes", 160, ""),
        ("Love", "Romantic, love, and relationship themed wallpapers", 170, ""),
        ("Military", "Military equipment, soldiers, and warfare themes", 180, ""),
        ("Minimal", "Minimalist designs with clean lines and simplicity", 190, ""),
        ("Movies", "Movie posters, scenes, and film characters", 200, ""),
        ("Music", "Musical instruments, artists, and concert themes", 210, ""),
        ("Nature", "Landscapes, mountains, oceans, and natural scenery", 220, ""),
        ("People", "Portraits, human figures, and social themes", 230, ""),
        ("Photography", "Professional photography and artistic shots", 240, ""),
        ("Quotes", "Inspirational quotes and typography wallpapers", 250, ""),
        ("Sci-Fi", "Science fiction themes, spaceships, and futuristic cities", 260, ""),
        ("Space", "Space, galaxies, planets, and astronomy themes", 270, ""),
        ("Sports", "Sports action, athletes, and stadium scenes", 280, ""),
        ("Technology", "Tech gadgets, circuits, and digital themes", 290, ""),
        ("World", "World landmarks, countries, and cultural themes", 300, ""),
    ]
    
    print("\nCreating/updating all categories...")
    created_categories = {}
    
    for name, description, display_order, cover_image_url in categories:
        category_id = create_or_update_category(conn, name, description, display_order, cover_image_url)
        created_categories[name] = category_id
    
    conn.commit()
    
    # Update all category counts
    update_category_counts(conn)
    
    # Verify all categories
    print("\n" + "=" * 60)
    print("FINAL CATEGORY LIST WITH COUNTS")
    print("=" * 60)
    
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, name, desktop_wallpaper_count, mobile_wallpaper_count, 
           (desktop_wallpaper_count + mobile_wallpaper_count) as total
    FROM wallpapers_category 
    ORDER BY display_order, id
    ''')
    all_categories = cursor.fetchall()
    
    for cat in all_categories:
        print(f"ID: {cat['id']:3} | {cat['name']:20} | Desktop: {cat['desktop_wallpaper_count']:3} | Mobile: {cat['mobile_wallpaper_count']:3} | Total: {cat['total']:3}")
    
    # Total counts
    cursor.execute("SELECT SUM(desktop_wallpaper_count) as total_desktop, SUM(mobile_wallpaper_count) as total_mobile FROM wallpapers_category")
    totals = cursor.fetchone()
    print(f"\n📊 TOTALS: Desktop: {totals['total_desktop'] or 0} | Mobile: {totals['total_mobile'] or 0} | All: {(totals['total_desktop'] or 0) + (totals['total_mobile'] or 0)}")
    
    conn.close()
    
    print(f"\n✅ Successfully populated all categories!")
    print(f"✅ Category counts are now accurate")

def create_trigger_for_auto_updates(conn):
    """Create SQL triggers to automatically update category counts."""
    print("\n" + "=" * 60)
    print("CREATING TRIGGERS FOR AUTO-UPDATES")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    # Drop existing triggers if they exist
    cursor.execute("DROP TRIGGER IF EXISTS update_desktop_category_count_on_insert")
    cursor.execute("DROP TRIGGER IF EXISTS update_desktop_category_count_on_delete")
    cursor.execute("DROP TRIGGER IF EXISTS update_desktop_category_count_on_update")
    cursor.execute("DROP TRIGGER IF EXISTS update_mobile_category_count_on_insert")
    cursor.execute("DROP TRIGGER IF EXISTS update_mobile_category_count_on_delete")
    cursor.execute("DROP TRIGGER IF EXISTS update_mobile_category_count_on_update")
    
    # Create triggers for desktop wallpapers
    cursor.execute('''
    CREATE TRIGGER update_desktop_category_count_on_insert
    AFTER INSERT ON wallpapers_desktopwallpaper
    BEGIN
        UPDATE wallpapers_category 
        SET desktop_wallpaper_count = (
            SELECT COUNT(*) 
            FROM wallpapers_desktopwallpaper 
            WHERE category_id = NEW.category_id
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.category_id;
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER update_desktop_category_count_on_delete
    AFTER DELETE ON wallpapers_desktopwallpaper
    BEGIN
        UPDATE wallpapers_category 
        SET desktop_wallpaper_count = (
            SELECT COUNT(*) 
            FROM wallpapers_desktopwallpaper 
            WHERE category_id = OLD.category_id
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.category_id;
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER update_desktop_category_count_on_update
    AFTER UPDATE OF category_id ON wallpapers_desktopwallpaper
    BEGIN
        -- Update old category
        UPDATE wallpapers_category 
        SET desktop_wallpaper_count = (
            SELECT COUNT(*) 
            FROM wallpapers_desktopwallpaper 
            WHERE category_id = OLD.category_id
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.category_id;
        
        -- Update new category
        UPDATE wallpapers_category 
        SET desktop_wallpaper_count = (
            SELECT COUNT(*) 
            FROM wallpapers_desktopwallpaper 
            WHERE category_id = NEW.category_id
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.category_id;
    END;
    ''')
    
    # Create triggers for mobile wallpapers
    cursor.execute('''
    CREATE TRIGGER update_mobile_category_count_on_insert
    AFTER INSERT ON wallpapers_mobilewallpaper
    BEGIN
        UPDATE wallpapers_category 
        SET mobile_wallpaper_count = (
            SELECT COUNT(*) 
            FROM wallpapers_mobilewallpaper 
            WHERE category_id = NEW.category_id
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.category_id;
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER update_mobile_category_count_on_delete
    AFTER DELETE ON wallpapers_mobilewallpaper
    BEGIN
        UPDATE wallpapers_category 
        SET mobile_wallpaper_count = (
            SELECT COUNT(*) 
            FROM wallpapers_mobilewallpaper 
            WHERE category_id = OLD.category_id
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.category_id;
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER update_mobile_category_count_on_update
    AFTER UPDATE OF category_id ON wallpapers_mobilewallpaper
    BEGIN
        -- Update old category
        UPDATE wallpapers_category 
        SET mobile_wallpaper_count = (
            SELECT COUNT(*) 
            FROM wallpapers_mobilewallpaper 
            WHERE category_id = OLD.category_id
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.category_id;
        
        -- Update new category
        UPDATE wallpapers_category 
        SET mobile_wallpaper_count = (
            SELECT COUNT(*) 
            FROM wallpapers_mobilewallpaper 
            WHERE category_id = NEW.category_id
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.category_id;
    END;
    ''')
    
    conn.commit()
    print("✅ Created triggers for automatic category count updates")
    print("⚠️  Note: Triggers only work for future INSERT/UPDATE/DELETE operations")

def main():
    """Main function."""
    print("=" * 60)
    print("CATEGORY MANAGEMENT WITH AUTO-UPDATES")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Ensure all categories exist (Anime as primary)")
    print("2. Update category counts accurately")
    print("3. Create triggers for future auto-updates")
    print("4. Fix any existing count mismatches")
    print("=" * 60)
    
    input("\nPress Enter to continue...")
    
    # Connect to database
    conn = connect_to_database()
    
    # First, populate categories and update counts
    populate_categories()
    
    # Create triggers for future automatic updates
    create_trigger_for_auto_updates(conn)
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("SCRIPT COMPLETED!")
    print("=" * 60)
    print("\n✅ All categories are created and counts are accurate")
    print("✅ Triggers created for automatic future updates")
    print("✅ From now on, category counts will update automatically")
    print("\nThe triggers will automatically update category counts when:")
    print("  - New wallpapers are added")
    print("  - Wallpapers are deleted")
    print("  - Wallpapers change categories")

if __name__ == "__main__":
    main()