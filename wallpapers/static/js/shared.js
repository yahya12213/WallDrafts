// Shared JavaScript utilities for WallDrafts
class LocalStorageManager {
    constructor() {
        this.favoriteKey = 'walldrafts_favorite_wallpapers';
        this.likeKey = 'walldrafts_liked_wallpapers';
        this.themeKey = 'walldrafts_theme';
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

    // Favorite methods
    toggleFavorite(wallpaperId) {
        const favorites = this.getFavoriteWallpapers();
        const index = favorites.indexOf(wallpaperId);
        if (index > -1) {
            favorites.splice(index, 1);
        } else {
            favorites.push(wallpaperId);
        }
        localStorage.setItem(this.favoriteKey, JSON.stringify(favorites));
        return index === -1; // Returns true if added, false if removed
    }

    isFavorited(wallpaperId) {
        const favorites = this.getFavoriteWallpapers();
        return favorites.includes(wallpaperId);
    }

    getFavoriteWallpapers() {
        return JSON.parse(localStorage.getItem(this.favoriteKey) || "[]");
    }

    // Like methods
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

    // Theme methods
    getTheme() {
        return localStorage.getItem(this.themeKey) || 'light';
    }

    setTheme(theme) {
        localStorage.setItem(this.themeKey, theme);
    }

    // Update button states
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

// Notification Manager
class NotificationManager {
    static show(message, type = 'success') {
        const bgColor = type === 'success' ? '#10b981' : 
                       type === 'error' ? '#ef4444' : 
                       type === 'info' ? '#139DF8' : '#FEC262';
        
        const notification = document.createElement('div');
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
            max-width: 300px;
        `;
        
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}"></i>
            ${message}
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Remove after 3 seconds
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

// Theme Manager
class ThemeManager {
    constructor() {
        this.storage = new LocalStorageManager();
        this.themeToggle = document.getElementById('themeToggle');
        this.init();
    }

    init() {
        const savedTheme = this.storage.getTheme();
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        if (this.themeToggle) {
            this.updateToggleIcon(savedTheme);
            this.themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        // Also initialize from system preference
        this.initializeSystemTheme();
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        this.storage.setTheme(newTheme);
        this.updateToggleIcon(newTheme);
        
        NotificationManager.show(`Switched to ${newTheme} mode`, 'info');
    }

    updateToggleIcon(theme) {
        if (this.themeToggle) {
            this.themeToggle.innerHTML = theme === 'light' ? 
                '<i class="fas fa-moon"></i>' : 
                '<i class="fas fa-sun"></i>';
        }
    }

    initializeSystemTheme() {
        if (this.storage.getTheme() === 'system') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme manager
    window.themeManager = new ThemeManager();
    
    // Initialize localStorage manager
    window.storageManager = new LocalStorageManager();
    
    // Initialize notification manager
    window.NotificationManager = NotificationManager;
    
    console.log('WallDrafts shared utilities initialized');
});