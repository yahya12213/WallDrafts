from django.urls import path
from . import views
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap, CategorySitemap, WallpaperSitemap
app_name = 'wallpapers'
sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
    'wallpapers': WallpaperSitemap,
}
urlpatterns = [
    # Homepage
    path('', views.home, name='home'),
    
    # Desktop only
    path('desktop/', views.wallpaper_list, name='desktop_list'),
    
    # Categories
    path('categories/', views.category_list, name='categories'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Wallpaper detail
    path('wallpaper/<int:id>/', views.wallpaper_detail, name='wallpaper_detail'),
    
    # Random wallpaper
    path('random/', views.random_wallpaper, name='random_wallpaper'),
    
    # Favorites
    path('favorites/', views.favorites_page, name='favorites'),
    
    # Search
    path('search/', views.search, name='search'),
    
    # Actions
    path('download/<int:id>/', views.download_wallpaper, name='download'),
    path('like/<int:id>/', views.toggle_like, name='like'),
    path('favorite/<int:id>/', views.toggle_favorite, name='favorite'),
    path('like-status/<int:id>/', views.get_like_status, name='like_status'),
    path('favorite-status/<int:id>/', views.get_favorite_status, name='favorite_status'),
    
    # API endpoints
    path('api/wallpapers/', views.api_wallpaper_list, name='api_wallpaper_list'),
    path('api/favorites/', views.api_favorites, name='api_favorites'),
    
    # Trending
    path('trending/', views.trending_wallpapers, name='trending'),
    
    # Legal pages
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
    path('dmca/', views.dmca, name='dmca'),
    
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]