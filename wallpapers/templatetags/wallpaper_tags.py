# wallpapers/templatetags/wallpaper_tags.py
from django import template
from wallpapers.models import DesktopWallpaper, MobileWallpaper

register = template.Library()

@register.filter
def get_wallpaper_type(wallpaper):
    """Returns 'desktop' or 'mobile' based on the wallpaper instance"""
    if isinstance(wallpaper, DesktopWallpaper):
        return 'desktop'
    elif isinstance(wallpaper, MobileWallpaper):
        return 'mobile'
    return 'unknown'

@register.filter
def is_desktop(wallpaper):
    """Returns True if wallpaper is DesktopWallpaper"""
    return isinstance(wallpaper, DesktopWallpaper)

@register.filter
def is_mobile(wallpaper):
    """Returns True if wallpaper is MobileWallpaper"""
    return isinstance(wallpaper, MobileWallpaper)