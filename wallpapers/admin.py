from django.contrib import admin
from .models import Category, DesktopWallpaper, MobileWallpaper, DownloadAnalytics, FeaturedSchedule
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'desktop_wallpaper_count', 'mobile_wallpaper_count', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')

@admin.register(DesktopWallpaper)
class DesktopWallpaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'resolution_width', 'resolution_height', 'quality_label', 
                    'downloads_count', 'views_count', 'is_trending', 'is_featured', 'created_at')
    list_filter = ('category', 'quality_label', 'is_trending', 'is_featured', 'created_at')
    search_fields = ('title', 'tags')
    readonly_fields = ('downloads_count', 'views_count', 'likes_count', 'favorites_count')
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'category', 'tags')
        }),
        ('Images', {
            'fields': ('image_url', 'thumbnail_url')
        }),
        ('Technical', {
            'fields': ('resolution_width', 'resolution_height', 'aspect_ratio', 'file_format', 'quality_label')
        }),
        ('Colors & CDN', {
            'fields': ('color_palette', 'cdn_path')
        }),
        ('Stats', {
            'fields': ('downloads_count', 'views_count', 'likes_count', 'favorites_count')
        }),
        ('Featured', {
            'fields': ('is_trending', 'trending_percentage', 'is_featured', 'display_order')
        }),
    )
    
    def image_preview(self, obj):
        return format_html(f'<img src="{obj.thumbnail_url}" style="max-height: 100px;" />')

@admin.register(MobileWallpaper)
class MobileWallpaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'device_type', 'resolution_width', 'resolution_height', 
                    'quality_label', 'downloads_count', 'views_count', 'is_trending', 'is_featured')
    list_filter = ('category', 'device_type', 'quality_label', 'is_trending', 'is_featured')
    search_fields = ('title', 'tags')
    readonly_fields = ('downloads_count', 'views_count', 'likes_count', 'favorites_count')

@admin.register(DownloadAnalytics)
class DownloadAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('wallpaper_type', 'wallpaper_id', 'device_type', 'timestamp')
    list_filter = ('wallpaper_type', 'device_type', 'timestamp')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

@admin.register(FeaturedSchedule)
class FeaturedScheduleAdmin(admin.ModelAdmin):
    list_display = ('wallpaper_type', 'wallpaper_id', 'featured_date', 'is_daily_featured')
    list_filter = ('wallpaper_type', 'featured_date', 'is_daily_featured')
    ordering = ('-featured_date', 'display_order')