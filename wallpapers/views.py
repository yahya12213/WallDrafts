from django.db.models import Q, F, Count, Sum, Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta
import hashlib
import random
from .models import DesktopWallpaper, Category, DownloadAnalytics
import os
from urllib.parse import urlparse
import requests
from django.conf import settings
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt

def download_wallpaper(request, id):
    """Download wallpaper view - DESKTOP ONLY"""
    wallpaper = get_object_or_404(DesktopWallpaper, id=id)
    
    try:
        # Increment download count atomically
        DesktopWallpaper.objects.filter(id=id).update(
            downloads_count=F('downloads_count') + 1
        )
        
        # Refresh to get updated count
        wallpaper.refresh_from_db()
        
        # Create analytics record
        ip_address = request.META.get('REMOTE_ADDR', '')
        if ip_address:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:64]
        else:
            ip_hash = ''
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        try:
            DownloadAnalytics.objects.create(
                wallpaper_type='desktop',
                wallpaper_id=id,
                session_id=request.session.session_key or '',
                device_type='desktop',
                user_agent=user_agent,
                ip_hash=ip_hash
            )
        except Exception as e:
            print(f"Analytics error: {e}")
        
        # Get file extension from URL
        image_url = wallpaper.image_url
        parsed_url = urlparse(image_url)
        filename = os.path.basename(parsed_url.path)
        
        if not filename or '.' not in filename:
            # Create a safe filename
            safe_title = ''.join(
                c if c.isalnum() or c in (' ', '-', '_') else '_' 
                for c in (wallpaper.title or 'wallpaper')
            ).strip().replace(' ', '_')
            
            # Get file extension
            file_format = wallpaper.file_format or 'jpg'
            if file_format.lower() in ['jpeg', 'jpg']:
                extension = 'jpg'
            elif file_format.lower() == 'png':
                extension = 'png'
            elif file_format.lower() == 'webp':
                extension = 'webp'
            else:
                extension = 'jpg'
            
            filename = f"{safe_title}_{wallpaper.resolution_width}x{wallpaper.resolution_height}.{extension}"
        
        # For external URLs, we need to fetch the image first
        if image_url.startswith('http'):
            try:
                # Fetch the image
                response = requests.get(image_url, stream=True, timeout=30)
                response.raise_for_status()
                
                # Create HTTP response with image data
                img_data = BytesIO(response.content)
                img_response = HttpResponse(img_data.getvalue(), content_type=response.headers.get('Content-Type', 'image/jpeg'))
                
                # Set Content-Disposition header to trigger download
                img_response['Content-Disposition'] = f'attachment; filename="{filename}"'
                img_response['Content-Length'] = len(response.content)
                
                return img_response
                
            except requests.RequestException as e:
                print(f"Error fetching image: {e}")
                # Fallback: redirect to image URL
                return redirect(image_url)
        else:
            # For local files
            file_path = os.path.join(settings.MEDIA_ROOT, image_url)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='image/jpeg')
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    return response
            else:
                return redirect(image_url)
                
    except Exception as e:
        print(f"Download error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Download failed',
            'download_url': wallpaper.image_url,
            'filename': filename if 'filename' in locals() else 'wallpaper.jpg'
        })

@csrf_exempt
def toggle_like(request, id):
    """Toggle like status for a wallpaper."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    wallpaper = get_object_or_404(DesktopWallpaper, id=id)
    
    # Check if user has already liked (using session)
    session_key = f'liked_{id}'
    already_liked = request.session.get(session_key, False)
    
    if already_liked:
        # Unlike - decrease count
        DesktopWallpaper.objects.filter(id=id).update(
            likes_count=F('likes_count') - 1
        )
        request.session[session_key] = False
        action = 'unliked'
    else:
        # Like - increase count
        DesktopWallpaper.objects.filter(id=id).update(
            likes_count=F('likes_count') + 1
        )
        request.session[session_key] = True
        action = 'liked'
    
    wallpaper.refresh_from_db()
    
    return JsonResponse({
        'success': True, 
        'likes_count': wallpaper.likes_count,
        'action': action,
        'is_liked': not already_liked
    })


@csrf_exempt
def toggle_favorite(request, id):
    """Toggle favorite status for a wallpaper."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    wallpaper = get_object_or_404(DesktopWallpaper, id=id)
    
    # Check if user has already favorited (using session)
    session_key = f'favorited_{id}'
    timestamp_key = f'favorited_timestamp_{id}'
    already_favorited = request.session.get(session_key, False)
    
    if already_favorited:
        # Unfavorite - decrease count
        DesktopWallpaper.objects.filter(id=id).update(
            favorites_count=F('favorites_count') - 1
        )
        request.session[session_key] = False
        # Remove timestamp when unfavoriting
        if timestamp_key in request.session:
            del request.session[timestamp_key]
        action = 'unfavorited'
    else:
        # Favorite - increase count
        DesktopWallpaper.objects.filter(id=id).update(
            favorites_count=F('favorites_count') + 1
        )
        request.session[session_key] = True
        # Store timestamp when favoriting
        from datetime import datetime
        request.session[timestamp_key] = datetime.now().isoformat()
        action = 'favorited'
    
    wallpaper.refresh_from_db()
    
    return JsonResponse({
        'success': True, 
        'favorites_count': wallpaper.favorites_count,
        'action': action,
        'is_favorited': not already_favorited,
        'timestamp': request.session.get(timestamp_key, '') if not already_favorited else ''
    })




def get_like_status(request, id):
    """Check if user has liked a wallpaper."""
    session_key = f'liked_{id}'
    is_liked = request.session.get(session_key, False)
    
    return JsonResponse({
        'is_liked': is_liked
    })

def get_favorite_status(request, id):
    """Check if user has favorited a wallpaper."""
    session_key = f'favorited_{id}'
    is_favorited = request.session.get(session_key, False)
    
    return JsonResponse({
        'is_favorited': is_favorited
    })

def api_wallpaper_list(request):
    """API endpoint for infinite scroll - DESKTOP ONLY"""
    page = int(request.GET.get('page', 1))
    per_page = 24
    
    wallpapers = DesktopWallpaper.objects.all().order_by('-created_at')
    
    # Pagination manually for API
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_wallpapers = wallpapers[start:end]
    
    # Serialize wallpapers
    wallpaper_list = []
    for wallpaper in paginated_wallpapers:
        wallpaper_list.append({
            'id': wallpaper.id,
            'title': wallpaper.title,
            'thumbnail_url': wallpaper.thumbnail_url,
            'image_url': wallpaper.image_url,
            'resolution_width': wallpaper.resolution_width,
            'resolution_height': wallpaper.resolution_height,
            'quality_label': wallpaper.quality_label,
            'likes_count': wallpaper.likes_count,
            'favorites_count': wallpaper.favorites_count,
            'downloads_count': wallpaper.downloads_count,
            'is_trending': wallpaper.is_trending,
            'created_at': wallpaper.created_at.isoformat() if wallpaper.created_at else None,
        })
    
    return JsonResponse({
        'wallpapers': wallpaper_list,
        'has_next': end < wallpapers.count(),
        'page': page
    })

def api_favorites(request):
    """API to get favorite wallpaper data from both session and localStorage"""
    # Check for localStorage IDs in request
    ids_param = request.GET.get('ids', '')
    
    # Also check Django session favorites
    session_favorites = []
    for key in request.session.keys():
        if key.startswith('favorited_'):
            try:
                wallpaper_id = int(key.split('_')[1])
                if request.session[key]:  # If True (favorited)
                    session_favorites.append(wallpaper_id)
            except (ValueError, IndexError):
                continue
    
    # Combine both sources
    all_favorite_ids = set()
    
    if ids_param:
        try:
            ids = [int(id) for id in ids_param.split(',') if id.strip().isdigit()]
            all_favorite_ids.update(ids)
        except Exception:
            pass
    
    all_favorite_ids.update(session_favorites)
    
    if not all_favorite_ids:
        return JsonResponse({'wallpapers': []})
    
    # Fetch wallpapers that exist
    wallpapers = DesktopWallpaper.objects.filter(id__in=list(all_favorite_ids))
    
    wallpaper_list = []
    for wallpaper in wallpapers:
        wallpaper_list.append({
            'id': wallpaper.id,
            'title': wallpaper.title or 'Untitled Wallpaper',
            'thumbnail_url': wallpaper.thumbnail_url or 'https://via.placeholder.com/300x200',
            'image_url': wallpaper.image_url or 'https://via.placeholder.com/1920x1080',
            'resolution_width': wallpaper.resolution_width or 1920,
            'resolution_height': wallpaper.resolution_height or 1080,
            'quality_label': wallpaper.quality_label or 'HD',
            'likes_count': wallpaper.likes_count or 0,
            'favorites_count': wallpaper.favorites_count or 0,
            'downloads_count': wallpaper.downloads_count or 0,
            'views_count': wallpaper.views_count or 0,
            'created_at': wallpaper.created_at.isoformat() if wallpaper.created_at else '2024-01-01T00:00:00Z',
            'type': 'desktop',
            'is_trending': wallpaper.is_trending or False
        })
    
    return JsonResponse({'wallpapers': wallpaper_list})

def category_list(request):
    """List all categories with counts"""
    categories = Category.objects.filter(is_active=True).annotate(
        total_wallpapers=F('desktop_wallpaper_count')
    ).order_by('display_order', 'name')
    
    # Calculate totals
    total_wallpapers = categories.aggregate(total=Sum('desktop_wallpaper_count'))['total'] or 0
    
    context = {
        'categories': categories,
        'total_wallpapers': total_wallpapers,
        'page_title': 'Browse Wallpaper Categories | WallDrafts',
        'meta_description': 'Explore our collection of HD wallpaper categories including nature, abstract, anime, space, gaming, and more. Find the perfect wallpaper for your desktop.',
        'meta_keywords': 'wallpaper categories, HD wallpapers, desktop backgrounds, nature wallpapers, abstract art, anime backgrounds, space wallpapers, gaming wallpapers'
    }
    return render(request, 'wallpapers/categories.html', context)

def category_detail(request, slug):
    """Show wallpapers in a specific category - DESKTOP ONLY"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    sort_by = request.GET.get('sort', '-created_at')
    page = request.GET.get('page', 1)
    
    wallpapers = DesktopWallpaper.objects.filter(category=category)
    
    if sort_by == '-downloads_count':
        wallpapers = wallpapers.order_by('-downloads_count')
    elif sort_by == '-likes_count':
        wallpapers = wallpapers.order_by('-likes_count')
    elif sort_by == '-views_count':
        wallpapers = wallpapers.order_by('-views_count')
    else:
        wallpapers = wallpapers.order_by(sort_by)
    
    # Calculate total downloads for this category
    total_downloads = wallpapers.aggregate(total=Sum('downloads_count'))['total'] or 0
    
    # Pagination
    paginator = Paginator(wallpapers, 20)  # Show 20 per page
    page_obj = paginator.get_page(page)
    
    # Check if it's an AJAX request for load more
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        wallpapers_data = []
        for wallpaper in page_obj:
            wallpapers_data.append({
                'id': wallpaper.id,
                'title': wallpaper.title,
                'thumbnail_url': wallpaper.thumbnail_url,
                'downloads_count': wallpaper.downloads_count,
                'is_trending': wallpaper.is_trending,
                'resolution_width': wallpaper.resolution_width,
                'resolution_height': wallpaper.resolution_height,
            })
        
        return JsonResponse({
            'wallpapers': wallpapers_data,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        })
    
    # Get categories for header
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        total_wallpapers=F('desktop_wallpaper_count')
    ).filter(
        total_wallpapers__gt=0
    ).order_by('display_order', 'name')
    
    context = {
        'category': category,
        'wallpapers': page_obj,
        'sort_by': sort_by,
        'total_downloads': total_downloads,
        'total_count': wallpapers.count(),
        'categories': categories,
        'page_title': f'{category.name} Wallpapers - HD Desktop Backgrounds | WallDrafts',
        'meta_description': f'Download free HD {category.name} wallpapers for desktop. High-quality {category.name} backgrounds in various resolutions.',
        'meta_keywords': f'{category.name} wallpapers, {category.name} backgrounds, HD {category.name} images, free {category.name} wallpapers, desktop {category.name} backgrounds'
    }
    return render(request, 'wallpapers/category_detail.html', context)

def search(request):
    """Search wallpapers by title and tags"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        context = {
            'query': '', 
            'results': [],
            'page_title': 'Search Wallpapers | WallDrafts',
            'meta_description': 'Search for HD wallpapers by title, tags, or category. Find the perfect desktop background for your device.',
            'meta_keywords': 'search wallpapers, find backgrounds, wallpaper search, desktop backgrounds search'
        }
        return render(request, 'wallpapers/search.html', context)
    
    # Search only in desktop wallpapers
    results = DesktopWallpaper.objects.filter(
        Q(title__icontains=query) | Q(tags__icontains=query)
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(results, 24)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    
    context = {
        'query': query,
        'results': page_obj,
        'total_results': results.count(),
        'page_title': f'Search Results for "{query}" | WallDrafts',
        'meta_description': f'Found {results.count()} wallpapers matching "{query}". Download free HD wallpapers for your desktop.',
        'meta_keywords': f'{query} wallpapers, search results, {query} backgrounds, HD {query} images'
    }
    return render(request, 'wallpapers/search.html', context)

def trending_wallpapers(request):
    """Show trending wallpapers - DESKTOP ONLY"""
    sort_by = request.GET.get('sort', 'trending')
    
    if sort_by == 'downloads':
        wallpapers = DesktopWallpaper.objects.filter(
            is_trending=True
        ).order_by('-downloads_count')
    elif sort_by == 'likes':
        wallpapers = DesktopWallpaper.objects.filter(
            is_trending=True
        ).order_by('-likes_count')
    elif sort_by == 'recent':
        wallpapers = DesktopWallpaper.objects.filter(
            is_trending=True
        ).order_by('-created_at')
    else:  # trending (default)
        wallpapers = DesktopWallpaper.objects.filter(
            is_trending=True
        ).order_by('-created_at')
    
    # Calculate stats
    total_downloads = wallpapers.aggregate(total_downloads=Sum('downloads_count'))['total_downloads'] or 0
    total_likes = wallpapers.aggregate(total_likes=Sum('likes_count'))['total_likes'] or 0
    
    # Pagination
    paginator = Paginator(wallpapers, 24)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    
    # Get categories for header
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        total_wallpapers=F('desktop_wallpaper_count')
    ).filter(
        total_wallpapers__gt=0
    ).order_by('display_order', 'name')
    
    context = {
        'wallpapers': page_obj,
        'sort_by': sort_by,
        'total_downloads': total_downloads,
        'total_likes': total_likes,
        'categories': categories,
        'page_title': 'Trending Wallpapers - Most Popular HD Backgrounds | WallDrafts',
        'meta_description': 'Discover the most popular trending wallpapers. Download free HD backgrounds that are currently trending worldwide.',
        'meta_keywords': 'trending wallpapers, popular backgrounds, hot wallpapers, viral wallpapers, most downloaded backgrounds'
    }
    return render(request, 'wallpapers/trending.html', context)

def random_wallpaper(request):
    """Redirect to a random wallpaper detail page"""
    wallpaper_ids = DesktopWallpaper.objects.values_list('id', flat=True)
    if wallpaper_ids:
        random_id = random.choice(wallpaper_ids)
        return redirect('wallpapers:wallpaper_detail', id=random_id)
    return redirect('wallpapers:home')


def home(request):
    """Homepage view - Desktop only"""
    
    # Hero Section: Get ONE featured desktop wallpaper
    hero_wallpaper = DesktopWallpaper.objects.filter(
        is_featured=True
    ).order_by('-created_at').first()
    
    if not hero_wallpaper:
        hero_wallpaper = DesktopWallpaper.objects.order_by('-created_at').first()
    
    # ===== UPDATED: Efficient single query to get latest from each category =====
    # Get the latest wallpaper ID for each category
    from django.db.models import Max, Subquery, OuterRef
    
    # Create a subquery to get the max created_at for each category
    latest_wallpaper_subquery = DesktopWallpaper.objects.filter(
        category_id=OuterRef('pk')
    ).order_by('-created_at').values('id')[:1]
    
    # Get categories with their latest wallpaper
    categories_with_latest = Category.objects.filter(
        is_active=True,
        desktop_wallpaper_count__gt=0
    ).annotate(
        latest_wallpaper_id=Subquery(latest_wallpaper_subquery)
    ).filter(
        latest_wallpaper_id__isnull=False
    ).order_by('display_order', 'name')[:12]  # Limit to 12 categories
    
    # Get the actual wallpaper objects
    latest_wallpaper_ids = [cat.latest_wallpaper_id for cat in categories_with_latest if cat.latest_wallpaper_id]
    
    if latest_wallpaper_ids:
        recent_wallpapers = DesktopWallpaper.objects.filter(
            id__in=latest_wallpaper_ids
        ).select_related('category')
        
        # Order them to match the category order
        id_to_wallpaper = {wp.id: wp for wp in recent_wallpapers}
        recent_wallpapers = [id_to_wallpaper[wid] for wid in latest_wallpaper_ids if wid in id_to_wallpaper]
    else:
        recent_wallpapers = []
    # ===== END UPDATE =====
    
    # Trending Now Section (12 trending desktop wallpapers)
    trending_wallpapers = DesktopWallpaper.objects.filter(
        is_trending=True
    ).order_by('-created_at')[:12]
    
    # Categories for dropdown (this remains the same)
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        total_wallpapers=F('desktop_wallpaper_count')
    ).filter(
        total_wallpapers__gt=0
    ).order_by('display_order', 'name')
    
    context = {
        'hero_wallpaper': hero_wallpaper,
        'recent_wallpapers': recent_wallpapers,
        'trending_wallpapers': trending_wallpapers,
        'categories': categories,
        'page_title': 'WallDrafts - Free HD Wallpapers for Desktop',
        'meta_description': 'Download thousands of free HD wallpapers for desktop. Curated collection of beautiful backgrounds updated daily. No registration required.',
        'meta_keywords': 'free wallpapers, HD wallpapers, desktop backgrounds, wallpaper download, 4K wallpapers, background images'
    }
    return render(request, 'wallpapers/home.html', context)





def wallpaper_list(request):
    """Desktop wallpaper list view"""
    category_slug = request.GET.get('category')
    sort_by = request.GET.get('sort', '-created_at')
    resolution = request.GET.get('resolution')
    
    wallpapers = DesktopWallpaper.objects.all()
    
    if category_slug:
        wallpapers = wallpapers.filter(category__slug=category_slug)
    
    if resolution:
        width, height = resolution.split('x')
        wallpapers = wallpapers.filter(
            resolution_width=width,
            resolution_height=height
        )
    
    if sort_by == 'popular':
        wallpapers = wallpapers.order_by('-views_count')
    elif sort_by == 'downloads':
        wallpapers = wallpapers.order_by('-downloads_count')
    elif sort_by == 'likes':
        wallpapers = wallpapers.order_by('-likes_count')
    else:
        wallpapers = wallpapers.order_by(sort_by)
    
    paginator = Paginator(wallpapers, 24)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    
    # Get categories for header
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'wallpapers': page_obj,
        'categories': categories,
        'sort_by': sort_by,
        'page_title': 'Desktop Wallpapers - HD Backgrounds Collection | WallDrafts',
        'meta_description': 'Browse our collection of HD desktop wallpapers. Free downloads in various resolutions including 4K, 2K, and Full HD.',
        'meta_keywords': 'desktop wallpapers, HD backgrounds, computer wallpapers, PC backgrounds, wallpaper collection'
    }
    return render(request, 'wallpapers/desktop_list.html', context)

def favorites_page(request):
    """Display user's favorite wallpapers from localStorage"""
    # Get categories for header (this stays the same)
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        total_wallpapers=F('desktop_wallpaper_count')
    ).filter(
        total_wallpapers__gt=0
    ).order_by('display_order', 'name')
    
    # Get session favorites in order they were added
    session_favorites = []
    session_favorite_timestamps = {}
    
    # We need to track when favorites were added in session
    # If you haven't been tracking timestamps, we'll use session keys order
    for key in request.session.keys():
        if key.startswith('favorited_'):
            try:
                wallpaper_id = int(key.split('_')[1])
                if request.session[key]:  # If True (favorited)
                    # Check if we have a timestamp for this favorite
                    timestamp_key = f'favorited_timestamp_{wallpaper_id}'
                    timestamp = request.session.get(timestamp_key)
                    
                    session_favorites.append(wallpaper_id)
                    if timestamp:
                        session_favorite_timestamps[wallpaper_id] = timestamp
            except (ValueError, IndexError):
                continue
    
    context = {
        'categories': categories,
        'session_favorites': session_favorites,
        'page_title': 'My Favorites - Saved Wallpapers | WallDrafts',
        'meta_description': 'Access your favorite wallpapers collection. All your saved HD backgrounds in one place for easy downloading.',
        'meta_keywords': 'favorite wallpapers, saved backgrounds, wallpaper collection, my favorites, bookmarked wallpapers'
    }
    return render(request, 'wallpapers/favorites.html', context)

def wallpaper_detail(request, id):
    """Wallpaper detail view - DESKTOP ONLY"""
    wallpaper = get_object_or_404(DesktopWallpaper, id=id)
    similar_wallpapers = DesktopWallpaper.objects.filter(
        category=wallpaper.category
    ).exclude(id=id).order_by('?')[:8]  # Use random ordering
    
    wallpaper.increment_views()
    
    # Format download time display
    download_time = "Just now"
    if wallpaper.downloads_count > 0:
        if wallpaper.downloads_count < 100:
            download_time = "Recently"
        elif wallpaper.downloads_count < 1000:
            download_time = "Popular"
        else:
            download_time = "Very Popular"
    
    # Get categories for header
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        total_wallpapers=F('desktop_wallpaper_count')
    ).filter(
        total_wallpapers__gt=0
    ).order_by('display_order', 'name')
    
    # Check like/favorite status
    is_liked = request.session.get(f'liked_{id}', False)
    is_favorited = request.session.get(f'favorited_{id}', False)
    
    context = {
        'wallpaper': wallpaper,
        'similar_wallpapers': similar_wallpapers,
        'download_time': download_time,
        'categories': categories,
        'is_liked': is_liked,
        'is_favorited': is_favorited,
        'page_title': f'{wallpaper.title} - HD Wallpaper Download | WallDrafts',
        'meta_description': f'Download {wallpaper.title} wallpaper in {wallpaper.resolution_width}x{wallpaper.resolution_height} resolution. Free HD background for desktop.',
        'meta_keywords': f'{wallpaper.title}, HD wallpaper, {wallpaper.resolution_width}x{wallpaper.resolution_height}, free download, desktop background'
    }
    return render(request, 'wallpapers/wallpaper_detail.html', context)

# New pages for legal documents
def terms_of_service(request):
    """Terms of Service page"""
    context = {
        'page_title': 'Terms of Service - WallDrafts',
        'meta_description': 'WallDrafts Terms of Service. Read our terms and conditions for using our wallpaper download service.',
        'meta_keywords': 'terms of service, terms and conditions, wallpaper download terms'
    }
    return render(request, 'wallpapers/terms_of_service.html', context)

def privacy_policy(request):
    """Privacy Policy page"""
    context = {
        'page_title': 'Privacy Policy - WallDrafts',
        'meta_description': 'WallDrafts Privacy Policy. Learn how we protect your privacy and handle your data.',
        'meta_keywords': 'privacy policy, data protection, privacy terms'
    }
    return render(request, 'wallpapers/privacy_policy.html', context)

def cookie_policy(request):
    """Cookie Policy page"""
    context = {
        'page_title': 'Cookie Policy - WallDrafts',
        'meta_description': 'WallDrafts Cookie Policy. Learn about how we use cookies on our website.',
        'meta_keywords': 'cookie policy, cookies, website cookies'
    }
    return render(request, 'wallpapers/cookie_policy.html', context)

def dmca(request):
    """DMCA page"""
    context = {
        'page_title': 'DMCA Policy - WallDrafts',
        'meta_description': 'WallDrafts DMCA Policy. Copyright infringement notification procedures.',
        'meta_keywords': 'DMCA, copyright, infringement, digital millennium copyright act'
    }
    return render(request, 'wallpapers/dmca.html', context)