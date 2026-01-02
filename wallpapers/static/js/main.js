// main.js - WallDrafts Main JavaScript

// LocalStorage Manager
class LocalStorageManager {
    constructor() {
        this.favoriteKey = 'walldrafts_favorite_wallpapers';
        this.likeKey = 'walldrafts_liked_wallpapers';
        this.init();
    }

    init() {
        if (!this.getFavoriteWallpapers()) {
            localStorage.setItem(this.favoriteKey, JSON.stringify([]));
        }
        if (!this.getLikedWallpapers()) {
            localStorage.setItem(this.likeKey, JSON.stringify([]));
        }
    }

    toggleFavorite(wallpaperId) {
        const favorites = this.getFavoriteWallpapers();
        const index = favorites.indexOf(wallpaperId);
        if (index > -1) {
            favorites.splice(index, 1);
        } else {
            favorites.push(wallpaperId);
        }
        localStorage.setItem(this.favoriteKey, JSON.stringify(favorites));
        return index === -1;
    }

    isFavorited(wallpaperId) {
        const favorites = this.getFavoriteWallpapers();
        return favorites.includes(wallpaperId);
    }

    getFavoriteWallpapers() {
        return JSON.parse(localStorage.getItem(this.favoriteKey) || "[]");
    }

    toggleLike(wallpaperId) {
        const likes = this.getLikedWallpapers();
        const index = likes.indexOf(wallpaperId);
        if (index > -1) {
            likes.splice(index, 1);
        } else {
            likes.push(wallpaperId);
        }
        localStorage.setItem(this.likeKey, JSON.stringify(likes));
        return index === -1;
    }

    isLiked(wallpaperId) {
        const likes = this.getLikedWallpapers();
        return likes.includes(wallpaperId);
    }

    getLikedWallpapers() {
        return JSON.parse(localStorage.getItem(this.likeKey) || "[]");
    }

    updateFavoriteButton(wallpaperId, button) {
        if (this.isFavorited(wallpaperId)) {
            button.innerHTML = '<i class="fas fa-star"></i>';
            button.classList.add('active');
        } else {
            button.innerHTML = '<i class="far fa-star"></i>';
            button.classList.remove('active');
        }
    }

    updateLikeButton(wallpaperId, button) {
        if (this.isLiked(wallpaperId)) {
            button.innerHTML = '<i class="fas fa-heart"></i>';
            button.classList.add('active');
        } else {
            button.innerHTML = '<i class="far fa-heart"></i>';
            button.classList.remove('active');
        }
    }
}

class ThemeManager {
    constructor() {
        this.themeToggle = document.getElementById('themeToggle');
        this.init();
    }

    init() {
        // Set initial theme - DARK MODE IS NOW DEFAULT
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.setTheme(savedTheme);
        
        // Setup toggle event
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update toggle icon - reversed logic for dark default
        if (this.themeToggle) {
            const icon = this.themeToggle.querySelector('i');
            // When dark theme is active, show sun icon (click to go to light)
            // When light theme is active, show moon icon (click to go to dark)
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        
        // Show notification
        NotificationManager.show(`Switched to ${newTheme} theme`, 'success');
    }

    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    }
}

// Favorites Manager
class FavoritesManager {
    constructor() {
        this.storage = new LocalStorageManager();
        this.favoritesGrid = document.getElementById('favoritesGrid');
        this.emptyState = document.getElementById('emptyState');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.filterButtons = document.querySelectorAll('.filter-btn');
        this.sortSelect = document.getElementById('sortSelect');
        this.favoritesData = [];
        this.currentFilter = 'all';
        this.currentSort = 'recent';
        
        if (this.favoritesGrid) {
            this.init();
        }
    }

    async init() {
        this.setupEventListeners();
        await this.loadFavorites();
        this.renderFavorites();
    }

    async loadFavorites() {
        this.showLoading();
        
        const favoriteIds = this.storage.getFavoriteWallpapers();
        
        if (favoriteIds.length === 0) {
            this.showEmptyState();
            this.hideLoading();
            return;
        }

        try {
            // Fetch favorite wallpapers from the API
            const response = await fetch(`/api/favorites/?ids=${favoriteIds.join(',')}`);
            
            if (!response.ok) {
                throw new Error('Failed to load favorites');
            }
            
            const data = await response.json();
            this.favoritesData = data.wallpapers || [];
            
        } catch (error) {
            console.error('Error loading favorites:', error);
            this.favoritesData = [];
            this.showEmptyState();
        }
        
        this.hideLoading();
    }

    renderFavorites() {
        if (!this.favoritesGrid) return;
        
        this.favoritesGrid.innerHTML = '';
        
        if (this.favoritesData.length === 0) {
            this.showEmptyState();
            return;
        }
        
        let filteredFavorites = [...this.favoritesData];
        
        // Apply filter
        filteredFavorites = this.filterFavorites(filteredFavorites);
        
        // Apply sort
        filteredFavorites = this.sortFavorites(filteredFavorites);
        
        // Render cards
        filteredFavorites.forEach(wallpaper => {
            const card = this.createFavoriteCard(wallpaper);
            this.favoritesGrid.appendChild(card);
        });
        
        this.hideEmptyState();
    }

    filterFavorites(favorites) {
        switch(this.currentFilter) {
            case 'desktop':
                return favorites.filter(w => w.type === 'desktop');
            case 'trending':
                return favorites.filter(w => w.is_trending === true);
            default:
                return favorites;
        }
    }

    sortFavorites(favorites) {
        switch(this.currentSort) {
            case 'popular':
                return favorites.sort((a, b) => (b.views_count || 0) - (a.views_count || 0));
            case 'downloads':
                return favorites.sort((a, b) => (b.downloads_count || 0) - (a.downloads_count || 0));
            case 'resolution':
                return favorites.sort((a, b) => {
                    const aRes = (a.resolution_width || 0) * (a.resolution_height || 0);
                    const bRes = (b.resolution_width || 0) * (b.resolution_height || 0);
                    return bRes - aRes;
                });
            default: // recent
                return favorites.sort((a, b) => {
                    const dateA = a.created_at ? new Date(a.created_at) : new Date(0);
                    const dateB = b.created_at ? new Date(b.created_at) : new Date(0);
                    return dateB - dateA;
                });
        }
    }

    createFavoriteCard(wallpaper) {
        const card = document.createElement('div');
        card.className = 'favorite-card';
        card.innerHTML = `
            <a href="/wallpaper/${wallpaper.id}/">
                <img src="${wallpaper.thumbnail_url}" alt="${wallpaper.title}" class="favorite-image" loading="lazy">
            </a>
            <div class="favorite-content">
                <h3 class="favorite-title">${wallpaper.title}</h3>
                <div class="favorite-meta">
                    <span>${wallpaper.resolution_width || 0}×${wallpaper.resolution_height || 0}</span>
                    <span>${wallpaper.quality_label || 'HD'}</span>
                </div>
                <div class="favorite-stats">
                    <span><i class="fas fa-download"></i> ${wallpaper.downloads_count || 0}</span>
                    <span><i class="fas fa-heart"></i> ${wallpaper.likes_count || 0}</span>
                    <span><i class="fas fa-eye"></i> ${wallpaper.views_count || 0}</span>
                </div>
                <div class="favorite-actions">
                    <a href="/wallpaper/${wallpaper.id}/" class="action-btn view-btn">
                        <i class="fas fa-eye"></i>
                        View
                    </a>
                    <button class="action-btn download-btn" data-id="${wallpaper.id}">
                        <i class="fas fa-download"></i>
                        Download
                    </button>
                    <button class="action-btn remove-btn" data-id="${wallpaper.id}">
                        <i class="fas fa-trash"></i>
                        Remove
                    </button>
                </div>
            </div>
        `;
        
        // Add event listeners
        const downloadBtn = card.querySelector('.download-btn');
        const removeBtn = card.querySelector('.remove-btn');
        
        downloadBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.downloadWallpaper(wallpaper.id);
        });
        
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.removeFavorite(wallpaper.id);
        });
        
        return card;
    }

    async downloadWallpaper(id) {
        try {
            // Create a hidden iframe for download
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = `/download/${id}/`;
            document.body.appendChild(iframe);
            
            NotificationManager.show('Download started!', 'success');
            
            // Remove iframe after download
            setTimeout(() => {
                if (iframe.parentNode) {
                    document.body.removeChild(iframe);
                }
            }, 5000);
            
        } catch (error) {
            console.error('Download error:', error);
            NotificationManager.show('Download failed!', 'error');
        }
    }

    removeFavorite(id) {
        this.storage.toggleFavorite(id);
        this.favoritesData = this.favoritesData.filter(w => w.id !== id);
        this.renderFavorites();
        NotificationManager.show('Removed from favorites!', 'info');
    }

    setupEventListeners() {
        // Filter buttons
        if (this.filterButtons) {
            this.filterButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    this.filterButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    this.currentFilter = btn.dataset.filter;
                    this.renderFavorites();
                });
            });
        }
        
        // Sort select
        if (this.sortSelect) {
            this.sortSelect.addEventListener('change', () => {
                this.currentSort = this.sortSelect.value;
                this.renderFavorites();
            });
        }
    }

    showLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.style.display = 'block';
        }
        if (this.favoritesGrid) {
            this.favoritesGrid.style.display = 'none';
        }
    }

    hideLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.style.display = 'none';
        }
        if (this.favoritesGrid) {
            this.favoritesGrid.style.display = 'grid';
        }
    }

    showEmptyState() {
        if (this.emptyState) {
            this.emptyState.style.display = 'block';
        }
        if (this.favoritesGrid) {
            this.favoritesGrid.style.display = 'none';
        }
        if (this.loadingSpinner) {
            this.loadingSpinner.style.display = 'none';
        }
    }

    hideEmptyState() {
        if (this.emptyState) {
            this.emptyState.style.display = 'none';
        }
        if (this.favoritesGrid) {
            this.favoritesGrid.style.display = 'grid';
        }
    }
}

// Storage Manager (compatibility)
class StorageManager extends LocalStorageManager {
    constructor() {
        super();
    }
}

// Notification Manager
class NotificationManager {
    static show(message, type = 'success') {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? '#10b981' : 
                       type === 'error' ? '#ef4444' : 
                       type === 'warning' ? '#f59e0b' : '#139DF8';
        
        notification.className = 'notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${bgColor};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            z-index: 10000;
            transform: translateX(120%);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.8rem;
        `;
        
        const icon = type === 'success' ? 'check' :
                    type === 'error' ? 'exclamation' :
                    type === 'warning' ? 'exclamation-triangle' : 'info';
        
        notification.innerHTML = `
            <i class="fas fa-${icon}"></i>
            ${message}
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(120%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Make managers available globally
window.LocalStorageManager = LocalStorageManager;
window.ThemeManager = ThemeManager;
window.FavoritesManager = FavoritesManager;
window.NotificationManager = NotificationManager;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('WallDrafts initialized');
    
    // Initialize theme
    window.themeManager = new ThemeManager();
    
    // Initialize favorites manager if on favorites page
    if (document.getElementById('favoritesGrid')) {
        window.favoritesManager = new FavoritesManager();
    }
    
    // Initialize like/favorite buttons on wallpaper cards
    const storage = new LocalStorageManager();
    
    // Update like buttons
    document.querySelectorAll('.like-btn').forEach(btn => {
        const wallpaperId = btn.closest('.wallpaper-card')?.dataset.wallpaperId;
        if (wallpaperId) {
            storage.updateLikeButton(parseInt(wallpaperId), btn);
        }
    });
    
    // Update favorite buttons
    document.querySelectorAll('.favorite-btn').forEach(btn => {
        const wallpaperId = btn.closest('.wallpaper-card')?.dataset.wallpaperId;
        if (wallpaperId) {
            storage.updateFavoriteButton(parseInt(wallpaperId), btn);
        }
    });
    
    // Add hover effect to wallpaper cards
    const wallpaperCards = document.querySelectorAll('.wallpaper-card');
    wallpaperCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });
    });
    
    // Initialize search forms
    const searchForms = document.querySelectorAll('.search-form');
    searchForms.forEach(form => {
        const input = form.querySelector('.search-input');
        const wrapper = form.querySelector('.search-input-wrapper');
        
        if (input && wrapper) {
            input.addEventListener('focus', () => {
                wrapper.style.borderColor = 'var(--primary-color)';
                wrapper.style.boxShadow = '0 0 0 3px rgba(19, 157, 248, 0.1)';
            });
            
            input.addEventListener('blur', () => {
                wrapper.style.borderColor = '';
                wrapper.style.boxShadow = '';
            });
        }
    });
    
    // Add loading state to buttons
    const buttons = document.querySelectorAll('.btn, .action-btn, .cookie-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (this.classList.contains('loading') || this.disabled) {
                e.preventDefault();
                return;
            }
        });
    });
});