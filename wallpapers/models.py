# wallpapers/models.py

from django.db import models
from django.utils.text import slugify
import json



# models.py - Add this model
from django.db import models

class WallpaperReport(models.Model):
    """Model for wallpaper reports"""
    
    wallpaper = models.ForeignKey('DesktopWallpaper', on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('copyright', 'Copyright infringement'),
            ('inappropriate', 'Inappropriate content'),
            ('low_quality', 'Low quality'),
            ('wrong_category', 'Wrong category'),
            ('duplicate', 'Duplicate wallpaper'),
            ('other', 'Other')
        ]
    )
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    is_resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Wallpaper Report'
        verbose_name_plural = 'Wallpaper Reports'
    
    def __str__(self):
        return f"Report for {self.wallpaper.title} - {self.get_report_type_display()}"





class Category(models.Model):
    """Category model for organizing wallpapers"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_image_url = models.URLField(max_length=500, blank=True)
    
    # Denormalized counts for performance
    desktop_wallpaper_count = models.PositiveIntegerField(default=0)
    mobile_wallpaper_count = models.PositiveIntegerField(default=0)
    
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_total_wallpapers(self):
        """Get total wallpapers in this category"""
        return self.desktop_wallpaper_count + self.mobile_wallpaper_count
# ==================== UPDATED DESKTOP WALLPAPER MODEL ====================

class DesktopWallpaper(models.Model):
    """Desktop wallpapers table - completely independent from mobile"""
    
    # Basic information
    title = models.CharField(max_length=200)
    # REMOVED: description field
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='desktop_wallpapers'
    )
    
    # Tags and categorization
    tags = models.CharField(max_length=500, blank=True)  # comma-separated
    
    # Color palette extracted from image
    color_palette = models.JSONField(
        default=dict,
        blank=True,
        help_text='JSON: {"primary": "#RRGGBB", "secondary": "#RRGGBB", "accent": "#RRGGBB"}'
    )
    
    # Image URLs
    image_url = models.URLField(max_length=500)
    thumbnail_url = models.URLField(max_length=500)
    
    # Technical specifications
    resolution_width = models.PositiveIntegerField()
    resolution_height = models.PositiveIntegerField()
    aspect_ratio = models.CharField(max_length=20, blank=True)
    file_format = models.CharField(max_length=10, default='JPEG')
    # REMOVED: file_size_kb field
    
    # CDN and quality
    cdn_path = models.CharField(max_length=500, blank=True)
    quality_label = models.CharField(
        max_length=20,
        default='HD',
        choices=[
            ('HD', 'HD (720p)'),
            ('Full HD', 'Full HD (1080p)'),
            ('2K', '2K (1440p)'),
            ('4K', '4K (2160p)'),
            ('8K', '8K (4320p)'),
        ]
    )
    
    # Stats and counters (denormalized for performance)
    likes_count = models.PositiveIntegerField(default=0)
    favorites_count = models.PositiveIntegerField(default=0)
    downloads_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    
    # Trending and featuring
    is_trending = models.BooleanField(default=False)
    trending_percentage = models.PositiveSmallIntegerField(
        default=0,
        help_text="Random percentage 1-3% when trending"
    )
    is_featured = models.BooleanField(default=False)
    
    # For similarity calculations
    similarity_score = models.FloatField(null=True, blank=True)
    
    # Display and ordering
    display_order = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_trending', '-views_count']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['-downloads_count']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.resolution_width}x{self.resolution_height})"
    
    def save(self, *args, **kwargs):
        # Calculate aspect ratio if not set
        if not self.aspect_ratio and self.resolution_width and self.resolution_height:
            self.aspect_ratio = self.calculate_aspect_ratio()
        
        # Calculate similarity score if needed (simplified)
        if not self.similarity_score and self.tags:
            self.similarity_score = self.calculate_similarity_score()
        
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Update category count if this is a new wallpaper
        if is_new:
            self.category.desktop_wallpaper_count = self.category.desktop_wallpapers.count()
            self.category.save(update_fields=['desktop_wallpaper_count'])
    
    def calculate_aspect_ratio(self):
        """Calculate aspect ratio string like '16:9'"""
        from math import gcd
        width = self.resolution_width
        height = self.resolution_height
        
        # Find greatest common divisor
        divisor = gcd(width, height)
        
        if divisor == 0:
            return "0:0"
            
        simplified_width = width // divisor
        simplified_height = height // divisor
        
        return f"{simplified_width}:{simplified_height}"
    
    def calculate_similarity_score(self):
        """Calculate a basic similarity score based on tags"""
        # This is a placeholder - you'll implement your own logic
        # Could be based on tag overlap, color similarity, etc.
        return 0.0
    
    def increment_views(self):
        """Increment view count atomically"""
        self.views_count = models.F('views_count') + 1
        self.save(update_fields=['views_count'])
    
    def increment_downloads(self):
        """Increment download count atomically"""
        self.downloads_count = models.F('downloads_count') + 1
        self.save(update_fields=['downloads_count'])
    
    def increment_likes(self):
        """Increment likes count atomically"""
        self.likes_count = models.F('likes_count') + 1
        self.save(update_fields=['likes_count'])
    
    def increment_favorites(self):
        """Increment favorites count atomically"""
        self.favorites_count = models.F('favorites_count') + 1
        self.save(update_fields=['favorites_count'])


# ==================== UPDATED MOBILE WALLPAPER MODEL ====================

class MobileWallpaper(models.Model):
    """Mobile wallpapers table - completely independent from desktop"""
    
    # Basic information
    title = models.CharField(max_length=200)
    # REMOVED: description field
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='mobile_wallpapers'
    )
    
    # Tags and categorization
    tags = models.CharField(max_length=500, blank=True)  # comma-separated
    
    # Color palette extracted from image
    color_palette = models.JSONField(
        default=dict,
        blank=True,
        help_text='JSON: {"primary": "#RRGGBB", "secondary": "#RRGGBB", "accent": "#RRGGBB"}'
    )
    
    # Image URLs
    image_url = models.URLField(max_length=500)
    thumbnail_url = models.URLField(max_length=500)
    
    # Technical specifications
    resolution_width = models.PositiveIntegerField()
    resolution_height = models.PositiveIntegerField()
    aspect_ratio = models.CharField(max_length=20, blank=True)
    file_format = models.CharField(max_length=10, default='JPEG')
    # REMOVED: file_size_kb field
    
    # CDN and device specifics
    cdn_path = models.CharField(max_length=500, blank=True)
    quality_label = models.CharField(
        max_length=20,
        default='Phone',
        choices=[
            ('Phone', 'Phone'),
            ('Tablet', 'Tablet'),
            ('HD', 'HD'),
        ]
    )
    
    # Device type
    device_type = models.CharField(
        max_length=20,
        default='phone',
        choices=[
            ('phone', 'Phone'),
            ('tablet', 'Tablet'),
            ('both', 'Phone & Tablet'),
        ]
    )
    
    # Stats and counters (denormalized for performance)
    likes_count = models.PositiveIntegerField(default=0)
    favorites_count = models.PositiveIntegerField(default=0)
    downloads_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    
    # Trending and featuring
    is_trending = models.BooleanField(default=False)
    trending_percentage = models.PositiveSmallIntegerField(
        default=0,
        help_text="Random percentage 1-3% when trending"
    )
    is_featured = models.BooleanField(default=False)
    
    # For similarity calculations
    similarity_score = models.FloatField(null=True, blank=True)
    
    # Display and ordering
    display_order = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_trending', '-views_count']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['device_type', '-downloads_count']),
            models.Index(fields=['-downloads_count']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.resolution_width}x{self.resolution_height}) - {self.device_type}"
    
    def save(self, *args, **kwargs):
        # Calculate aspect ratio if not set
        if not self.aspect_ratio and self.resolution_width and self.resolution_height:
            self.aspect_ratio = self.calculate_aspect_ratio()
        
        # Calculate similarity score if needed (simplified)
        if not self.similarity_score and self.tags:
            self.similarity_score = self.calculate_similarity_score()
        
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Update category count if this is a new wallpaper
        if is_new:
            self.category.mobile_wallpaper_count = self.category.mobile_wallpapers.count()
            self.category.save(update_fields=['mobile_wallpaper_count'])
    
    def calculate_aspect_ratio(self):
        """Calculate aspect ratio string like '9:16'"""
        from math import gcd
        width = self.resolution_width
        height = self.resolution_height
        
        # Find greatest common divisor
        divisor = gcd(width, height)
        
        if divisor == 0:
            return "0:0"
            
        simplified_width = width // divisor
        simplified_height = height // divisor
        
        return f"{simplified_width}:{simplified_height}"
    
    def calculate_similarity_score(self):
        """Calculate a basic similarity score based on tags"""
        # This is a placeholder - you'll implement your own logic
        return 0.0
    
    def increment_views(self):
        """Increment view count atomically"""
        self.views_count = models.F('views_count') + 1
        self.save(update_fields=['views_count'])
    
    def increment_downloads(self):
        """Increment download count atomically"""
        self.downloads_count = models.F('downloads_count') + 1
        self.save(update_fields=['downloads_count'])
    
    def increment_likes(self):
        """Increment likes count atomically"""
        self.likes_count = models.F('likes_count') + 1
        self.save(update_fields=['likes_count'])
    
    def increment_favorites(self):
        """Increment favorites count atomically"""
        self.favorites_count = models.F('favorites_count') + 1
        self.save(update_fields=['favorites_count'])

class DownloadAnalytics(models.Model):
    """Track download analytics for both desktop and mobile wallpapers"""
    
    wallpaper_type = models.CharField(
        max_length=10,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
        ]
    )
    wallpaper_id = models.PositiveIntegerField()  # Can't use ForeignKey to two tables
    
    session_id = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(
        max_length=10,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
        ],
        help_text="User's device type"
    )
    user_agent = models.TextField(blank=True)
    
    ip_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA256 hash of IP address for anonymity"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Download Analytics"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['wallpaper_type', 'wallpaper_id']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.wallpaper_type} #{self.wallpaper_id} - {self.timestamp}"
    
class FeaturedSchedule(models.Model):
    """Schedule featured wallpapers (daily featured)"""
    
    wallpaper_type = models.CharField(
        max_length=10,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
        ]
    )
    wallpaper_id = models.PositiveIntegerField()
    
    featured_date = models.DateField()
    is_daily_featured = models.BooleanField(default=True)
    
    display_order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-featured_date', 'display_order']
        unique_together = ['wallpaper_type', 'wallpaper_id', 'featured_date']
        indexes = [
            models.Index(fields=['featured_date', 'is_daily_featured']),
        ]
    
    def __str__(self):
        return f"{self.wallpaper_type} #{self.wallpaper_id} - {self.featured_date}"
    
    def get_wallpaper(self):
        """Get the actual wallpaper object"""
        if self.wallpaper_type == 'desktop':
            return DesktopWallpaper.objects.filter(id=self.wallpaper_id).first()
        else:
            return MobileWallpaper.objects.filter(id=self.wallpaper_id).first()