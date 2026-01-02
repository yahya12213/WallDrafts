// CSRF Protection Helper
const CSRFToken = {
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    getToken() {
        return this.getCookie('csrftoken');
    },

    setupAjax() {
        const token = this.getToken();
        if (token) {
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", token);
                    }
                }
            });
        }
    },

    setupFetch() {
        const token = this.getToken();
        if (token) {
            const originalFetch = window.fetch;
            window.fetch = function(url, options = {}) {
                options.headers = {
                    ...options.headers,
                    'X-CSRFToken': token
                };
                return originalFetch(url, options);
            };
        }
    }
};

// Initialize CSRF protection
document.addEventListener('DOMContentLoaded', () => {
    CSRFToken.setupAjax();
    CSRFToken.setupFetch();
});