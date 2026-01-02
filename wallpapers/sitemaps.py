from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import DesktopWallpaper, Category
from django.utils import timezone

class StaticViewSitemap(Sitemap):
    """Sitemap for static pages (home, categories, legal pages, etc.)"""
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return [
            'wallpapers:home',           # Homepage
            'wallpapers:categories',     # Categories page
            'wallpapers:trending',       # Trending wallpapers
            'wallpapers:favorites',      # Favorites page
            'wallpapers:search',         # Search page
            'wallpapers:random_wallpaper',  # Random wallpaper
            'wallpapers:terms_of_service',  # Terms of Service
            'wallpapers:privacy_policy',    # Privacy Policy
            'wallpapers:cookie_policy',     # Cookie Policy
            'wallpapers:dmca',              # DMCA Policy
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        # Return today's date for all static pages
        return timezone.now().date()

class CategorySitemap(Sitemap):
    """Sitemap for wallpaper categories"""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Get all active categories
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        # Use updated_at if available, otherwise created_at
        return obj.updated_at.date() if obj.updated_at else obj.created_at.date()

    def location(self, obj):
        return reverse('wallpapers:category_detail', args=[obj.slug])

class WallpaperSitemap(Sitemap):
    """Sitemap for individual wallpapers"""
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        # Get all wallpapers (you might want to filter if you have many)
        return DesktopWallpaper.objects.all().order_by('-created_at')

    def lastmod(self, obj):
        # Use updated_at if available, otherwise created_at
        return obj.updated_at.date() if obj.updated_at else obj.created_at.date()

    def location(self, obj):
        return reverse('wallpapers:wallpaper_detail', args=[obj.id])

# If you have thousands of wallpapers, consider paginating:
class PaginatedWallpaperSitemap(Sitemap):
    """Paginated sitemap for large number of wallpapers"""
    changefreq = "monthly"
    priority = 0.6
    limit = 5000  # Google's limit per sitemap file

    def items(self):
        return DesktopWallpaper.objects.all().order_by('id')

    def location(self, obj):
        return reverse('wallpapers:wallpaper_detail', args=[obj.id])