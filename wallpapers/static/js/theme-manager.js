// theme-manager.js - Theme Switching for WallDrafts

class ThemeManager {
    constructor() {
        this.storage = new StorageManager();
        this.themeToggle = document.getElementById('themeToggle');
        this.mobileThemeOptions = document.querySelectorAll('.theme-option');
        this.systemPreference = window.matchMedia('(prefers-color-scheme: dark)');
        
        this.init();
    }

    init() {
        // Apply saved theme on page load
        this.applyTheme();
        
        // Initialize theme toggle button
        if (this.themeToggle) {
            this.themeToggle.classList.add('visible');
            this.themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        // Initialize mobile theme options
        this.mobileThemeOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                const theme = e.currentTarget.dataset.theme;
                this.setTheme(theme);
                
                // Update active state
                this.mobileThemeOptions.forEach(opt => opt.classList.remove('active'));
                e.currentTarget.classList.add('active');
            });
        });
        
        // Listen for system theme changes
        this.systemPreference.addEventListener('change', (e) => {
            const savedTheme = this.storage.getTheme();
            if (savedTheme === 'auto') {
                this.applyTheme();
            }
        });
        
        // Set initial active state for mobile theme options
        this.updateMobileThemeActiveState();
    }

    applyTheme() {
        const theme = this.storage.getTheme();
        let appliedTheme = theme;
        
        if (theme === 'auto') {
            appliedTheme = this.systemPreference.matches ? 'dark' : 'light';
        }
        
        document.documentElement.setAttribute('data-theme', appliedTheme);
        
        // Update theme toggle icon
        this.updateThemeToggleIcon(appliedTheme);
        
        // Update mobile theme active state
        this.updateMobileThemeActiveState();
    }

    setTheme(theme) {
        if (!['light', 'dark', 'auto'].includes(theme)) {
            console.error('ThemeManager: Invalid theme value', theme);
            return;
        }
        
        this.storage.setTheme(theme);
        this.applyTheme();
        
        // Show notification
        if (window.NotificationManager) {
            const themeNames = {
                light: 'Light',
                dark: 'Dark',
                auto: 'Auto (System)'
            };
            window.NotificationManager.show(`Theme changed to ${themeNames[theme]} mode`, 'success');
        }
    }

    toggleTheme() {
        const currentTheme = this.storage.getTheme();
        let newTheme;
        
        // Cycle through themes: dark -> light -> auto -> dark
        switch(currentTheme) {
            case 'dark':
                newTheme = 'light';
                break;
            case 'light':
                newTheme = 'auto';
                break;
            case 'auto':
                newTheme = 'dark';
                break;
            default:
                newTheme = 'dark';
        }
        
        this.setTheme(newTheme);
    }

    updateThemeToggleIcon(theme) {
        if (!this.themeToggle) return;
        
        const moonIcon = this.themeToggle.querySelector('.fa-moon');
        const sunIcon = this.themeToggle.querySelector('.fa-sun');
        
        if (theme === 'dark') {
            moonIcon.style.opacity = '1';
            moonIcon.style.transform = 'scale(1)';
            sunIcon.style.opacity = '0';
            sunIcon.style.transform = 'scale(0)';
            this.themeToggle.setAttribute('aria-label', 'Switch to light mode');
        } else {
            moonIcon.style.opacity = '0';
            moonIcon.style.transform = 'scale(0)';
            sunIcon.style.opacity = '1';
            sunIcon.style.transform = 'scale(1)';
            this.themeToggle.setAttribute('aria-label', 'Switch to dark mode');
        }
    }

    updateMobileThemeActiveState() {
        const currentTheme = this.storage.getTheme();
        
        this.mobileThemeOptions.forEach(option => {
            option.classList.remove('active');
            if (option.dataset.theme === currentTheme) {
                option.classList.add('active');
            }
        });
    }

    // Get current theme for other components
    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme');
    }

    // Check if current theme is dark
    isDarkMode() {
        return this.getCurrentTheme() === 'dark';
    }

    // Check if current theme is light
    isLightMode() {
        return this.getCurrentTheme() === 'light';
    }
}

// Initialize theme manager on page load
document.addEventListener('DOMContentLoaded', function() {
    window.ThemeManager = new ThemeManager();
});