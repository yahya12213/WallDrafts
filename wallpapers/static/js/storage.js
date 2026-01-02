// storage.js
class StorageManager {
    constructor() {
        this.keys = {
            favorites: 'walldrafts_favorites',
            likes: 'walldrafts_likes',
            downloads: 'walldrafts_downloads',
            settings: 'walldrafts_settings'
        };
    }
    
    // Favorites
    getFavorites() {
        return JSON.parse(localStorage.getItem(this.keys.favorites) || '[]');
    }
    
    toggleFavorite(wallpaperId) {
        const favorites = this.getFavorites();
        const index = favorites.indexOf(wallpaperId);
        
        if (index > -1) {
            favorites.splice(index, 1);
            localStorage.setItem(this.keys.favorites, JSON.stringify(favorites));
            return false;
        } else {
            favorites.push(wallpaperId);
            localStorage.setItem(this.keys.favorites, JSON.stringify(favorites));
            return true;
        }
    }
    
    isFavorite(wallpaperId) {
        const favorites = this.getFavorites();
        return favorites.includes(wallpaperId);
    }
    
    // Likes
    getLikes() {
        return JSON.parse(localStorage.getItem(this.keys.likes) || '[]');
    }
    
    toggleLike(wallpaperId) {
        const likes = this.getLikes();
        const index = likes.indexOf(wallpaperId);
        
        if (index > -1) {
            likes.splice(index, 1);
            localStorage.setItem(this.keys.likes, JSON.stringify(likes));
            return false;
        } else {
            likes.push(wallpaperId);
            localStorage.setItem(this.keys.likes, JSON.stringify(likes));
            return true;
        }
    }
    
    isLiked(wallpaperId) {
        const likes = this.getLikes();
        return likes.includes(wallpaperId);
    }
    
    // Downloads
    addDownload(wallpaper) {
        const downloads = JSON.parse(localStorage.getItem(this.keys.downloads) || '[]');
        const downloadRecord = {
            id: wallpaper.id,
            title: wallpaper.title,
            timestamp: new Date().toISOString(),
            resolution: wallpaper.resolution
        };
        
        downloads.unshift(downloadRecord);
        
        // Keep only last 100 downloads
        if (downloads.length > 100) {
            downloads.pop();
        }
        
        localStorage.setItem(this.keys.downloads, JSON.stringify(downloads));
    }
    
    getDownloads() {
        return JSON.parse(localStorage.getItem(this.keys.downloads) || '[]');
    }
    
    // Settings
    getSettings() {
        return JSON.parse(localStorage.getItem(this.keys.settings) || '{}');
    }
    
    saveSetting(key, value) {
        const settings = this.getSettings();
        settings[key] = value;
        localStorage.setItem(this.keys.settings, JSON.stringify(settings));
    }
    
    getSetting(key, defaultValue = null) {
        const settings = this.getSettings();
        return settings[key] || defaultValue;
    }
    
    // Clear all data
    clear() {
        localStorage.removeItem(this.keys.favorites);
        localStorage.removeItem(this.keys.likes);
        localStorage.removeItem(this.keys.downloads);
        localStorage.removeItem(this.keys.settings);
    }
}