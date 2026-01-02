// LocalStorage Manager for WallDrafts
class LocalStorageManager {
    constructor() {
        this.likedKey = 'walldrafts_liked_wallpapers';
        this.favoriteKey = 'walldrafts_favorite_wallpapers';
        this.downloadKey = 'walldrafts_download_history';
        this.init();
    }

    init() {
        // Initialize if not exists
        if (!this.getLikedWallpapers()) {
            localStorage.setItem(this.likedKey, JSON.stringify([]));
        }
        if (!this.getFavoriteWallpapers()) {
            localStorage.setItem(this.favoriteKey, JSON.stringify([]));
        }
        if (!this.getDownloadHistory()) {
            localStorage.setItem(this.downloadKey, JSON.stringify([]));
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
        
        localStorage.setItem(this.likedKey, JSON.stringify(liked));
        return index === -1; // Returns true if liked, false if unliked
    }

    isLiked(wallpaperId) {
        const liked = this.getLikedWallpapers();
        return liked.includes(wallpaperId);
    }

    getLikedWallpapers() {
        return JSON.parse(localStorage.getItem(this.likedKey) || "[]");
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
        
        localStorage.setItem(this.downloadKey, JSON.stringify(history));
    }

    getDownloadHistory() {
        return JSON.parse(localStorage.getItem(this.downloadKey)) || [];
    }

    // Update favorite button state
    updateFavoriteButton(wallpaperId, button) {
        if (this.isFavorited(wallpaperId)) {
            button.innerHTML = '<i class="fas fa-star" style="color: #f59e0b;"></i>';
            button.classList.add('favorited');
        } else {
            button.innerHTML = '<i class="far fa-star"></i>';
            button.classList.remove('favorited');
        }
    }

    // Update like button state
    updateLikeButton(wallpaperId, button) {
        if (this.isLiked(wallpaperId)) {
            button.innerHTML = '<i class="fas fa-heart" style="color: #ef4444;"></i>';
            button.classList.add('liked');
        } else {
            button.innerHTML = '<i class="far fa-heart"></i>';
            button.classList.remove('liked');
        }
    }
}

// Initialize LocalStorage Manager
const storage = new LocalStorageManager();

// Apply saved theme on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set dark theme as default
    document.documentElement.setAttribute('data-theme', 'dark');
    
    // Check if we're on wallpaper detail page
    const likeBtn = document.querySelector('.like-btn');
    const favoriteBtn = document.querySelector('.favorite-btn');
    
    if (likeBtn) {
        const wallpaperId = parseInt(likeBtn.dataset.wallpaperId);
        if (wallpaperId) {
            storage.updateLikeButton(wallpaperId, likeBtn);
        }
    }
    
    if (favoriteBtn) {
        const wallpaperId = parseInt(favoriteBtn.dataset.wallpaperId);
        if (wallpaperId) {
            storage.updateFavoriteButton(wallpaperId, favoriteBtn);
        }
    }
});