// storage-manager.js - Unified LocalStorage Management for WallDrafts

class StorageManager {
    constructor() {
        this.keys = {
            liked: 'walldrafts_liked_wallpapers',
            favorite: 'walldrafts_favorite_wallpapers',
            download: 'walldrafts_download_history',
            theme: 'walldrafts_theme_preference',
            cookies: 'walldrafts_cookie_consent'
        };
        this.init();
    }

    init() {
        // Initialize if not exists
        if (!this.get(this.keys.liked)) {
            this.set(this.keys.liked, []);
        }
        if (!this.get(this.keys.favorite)) {
            this.set(this.keys.favorite, []);
        }
        if (!this.get(this.keys.download)) {
            this.set(this.keys.download, []);
        }
        if (!this.get(this.keys.theme)) {
            this.set(this.keys.theme, 'dark'); // Default to dark theme
        }
        if (!this.get(this.keys.cookies)) {
            this.set(this.keys.cookies, false);
        }
    }

    // Generic getter/setter
    get(key) {
        try {
            return JSON.parse(localStorage.getItem(key));
        } catch (error) {
            console.error('StorageManager: Error parsing localStorage item', error);
            return null;
        }
    }

    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('StorageManager: Error setting localStorage item', error);
            return false;
        }
    }

    // Like management
    toggleLike(wallpaperId) {
        const liked = this.getLikedWallpapers();
        const index = liked.indexOf(wallpaperId);
        
        if (index > -1) {
            liked.splice(index, 1);
        } else {
            liked.push(wallpaperId);
        }
        
        this.set(this.keys.liked, liked);
        return index === -1; // Returns true if liked, false if unliked
    }

    isLiked(wallpaperId) {
        const liked = this.getLikedWallpapers();
        return liked.includes(wallpaperId);
    }

    getLikedWallpapers() {
        return this.get(this.keys.liked) || [];
    }

    // Favorite management
    toggleFavorite(wallpaperId) {
        const favorites = this.getFavoriteWallpapers();
        const index = favorites.indexOf(wallpaperId);
        
        if (index > -1) {
            favorites.splice(index, 1);
        } else {
            favorites.push(wallpaperId);
        }
        
        this.set(this.keys.favorite, favorites);
        
        // Update favorite count in header
        this.updateFavoriteCount();
        
        return index === -1;
    }

    isFavorited(wallpaperId) {
        const favorites = this.getFavoriteWallpapers();
        return favorites.includes(wallpaperId);
    }

    getFavoriteWallpapers() {
        return this.get(this.keys.favorite) || [];
    }

    updateFavoriteCount() {
        const favorites = this.getFavoriteWallpapers();
        const count = favorites.length;
        
        // Update header badge
        const headerBadge = document.getElementById('headerFavoriteCount');
        if (headerBadge) {
            headerBadge.textContent = count;
        }
        
        // Update mobile badge
        const mobileBadge = document.getElementById('mobileFavoriteCount');
        if (mobileBadge) {
            mobileBadge.textContent = count;
        }
        
        return count;
    }

    // Download history
    addToDownloadHistory(wallpaper) {
        const history = this.getDownloadHistory();
        history.unshift({
            ...wallpaper,
            downloadedAt: new Date().toISOString()
        });
        
        // Keep only last 50 items
        if (history.length > 50) {
            history.pop();
        }
        
        this.set(this.keys.download, history);
    }

    getDownloadHistory() {
        return this.get(this.keys.download) || [];
    }

    // Theme management
    getTheme() {
        const savedTheme = this.get(this.keys.theme);
        
        // If auto mode, detect system preference
        if (savedTheme === 'auto') {
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        
        return savedTheme || 'dark';
    }

    setTheme(theme) {
        if (!['light', 'dark', 'auto'].includes(theme)) {
            console.error('StorageManager: Invalid theme value', theme);
            return false;
        }
        
        this.set(this.keys.theme, theme);
        
        // Apply theme immediately
        document.documentElement.setAttribute('data-theme', theme === 'auto' ? 
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : theme);
        
        return true;
    }

    // Cookie consent
    getCookieConsent() {
        return this.get(this.keys.cookies) || false;
    }

    setCookieConsent(accepted) {
        this.set(this.keys.cookies, accepted);
        return true;
    }

    // Sync with Django session (for future implementation)
    async syncWithServer() {
        // This would be implemented when backend API is ready
        try {
            const favorites = this.getFavoriteWallpapers();
            const likes = this.getLikedWallpapers();
            
            // Send to server
            const response = await fetch('/api/sync/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    favorites: favorites,
                    likes: likes
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('StorageManager: Synced with server', data);
                return true;
            }
        } catch (error) {
            console.error('StorageManager: Sync error', error);
        }
        return false;
    }

    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    // Update button states
    updateFavoriteButton(wallpaperId, button) {
        if (!button) return;
        
        if (this.isFavorited(wallpaperId)) {
            button.innerHTML = '<i class="fas fa-star"></i>';
            button.classList.add('active');
            button.title = 'Remove from favorites';
        } else {
            button.innerHTML = '<i class="far fa-star"></i>';
            button.classList.remove('active');
            button.title = 'Add to favorites';
        }
    }

    updateLikeButton(wallpaperId, button) {
        if (!button) return;
        
        if (this.isLiked(wallpaperId)) {
            button.innerHTML = '<i class="fas fa-heart"></i>';
            button.classList.add('active');
            button.title = 'Unlike';
        } else {
            button.innerHTML = '<i class="far fa-heart"></i>';
            button.classList.remove('active');
            button.title = 'Like';
        }
    }

    // Clear all data (for testing/logout)
    clearAll() {
        Object.values(this.keys).forEach(key => {
            localStorage.removeItem(key);
        });
        this.init();
    }
}

// Initialize and make available globally
window.StorageManager = StorageManager;

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const storage = new StorageManager();
    
    // Update favorite count on page load
    storage.updateFavoriteCount();
    
    // Initialize button states for current page
    document.querySelectorAll('.favorite-btn').forEach(btn => {
        const wallpaperId = parseInt(btn.dataset.wallpaperId);
        if (wallpaperId) {
            storage.updateFavoriteButton(wallpaperId, btn);
        }
    });
    
    document.querySelectorAll('.like-btn').forEach(btn => {
        const wallpaperId = parseInt(btn.dataset.wallpaperId);
        if (wallpaperId) {
            storage.updateLikeButton(wallpaperId, btn);
        }
    });
});