// Cookie Consent Manager
class CookieManager {
    constructor() {
        this.cookieConsent = document.getElementById('cookieConsent');
        this.acceptBtn = document.getElementById('acceptCookies');
        this.rejectBtn = document.getElementById('rejectCookies');
        this.cookieName = 'walldrafts_cookies';
        this.cookieExpiry = 365; // days
        
        this.init();
    }
    
    init() {
        // Check if user already made a choice
        if (!this.getCookie(this.cookieName)) {
            this.showConsent();
        }
        
        // Set up event listeners
        if (this.acceptBtn) {
            this.acceptBtn.addEventListener('click', () => this.acceptCookies());
        }
        
        if (this.rejectBtn) {
            this.rejectBtn.addEventListener('click', () => this.rejectCookies());
        }
    }
    
    showConsent() {
        setTimeout(() => {
            if (this.cookieConsent) {
                this.cookieConsent.classList.add('show');
            }
        }, 1000);
    }
    
    hideConsent() {
        if (this.cookieConsent) {
            this.cookieConsent.classList.remove('show');
        }
    }
    
    acceptCookies() {
        this.setCookie(this.cookieName, 'accepted', this.cookieExpiry);
        this.hideConsent();
        this.loadAnalytics();
        this.showNotification('Cookies accepted!', 'success');
    }
    
    rejectCookies() {
        this.setCookie(this.cookieName, 'rejected', this.cookieExpiry);
        this.hideConsent();
        this.showNotification('Cookies rejected!', 'info');
    }
    
    loadAnalytics() {
        // Add your analytics scripts here
        // Example: Google Analytics
        if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            // Only load analytics on production
            // (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','GTM-XXXXXX');
        }
    }
    
    setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = "expires=" + date.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/;SameSite=Lax";
    }
    
    getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') {
                c = c.substring(1, c.length);
            }
            if (c.indexOf(nameEQ) === 0) {
                return c.substring(nameEQ.length, c.length);
            }
        }
        return null;
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1';
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${bgColor};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            z-index: 10000;
            transform: translateX(120%);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.8rem;
            max-width: 400px;
        `;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}"></i>
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

// Initialize Cookie Manager on page load
document.addEventListener('DOMContentLoaded', () => {
    new CookieManager();
});