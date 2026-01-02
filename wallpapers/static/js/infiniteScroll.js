class InfiniteScroll {
    constructor(containerSelector, loadMoreUrl) {
        this.container = document.querySelector(containerSelector);
        this.loadMoreUrl = loadMoreUrl;
        this.page = 2;
        this.loading = false;
        this.hasMore = true;
        
        this.init();
    }

    init() {
        window.addEventListener('scroll', this.handleScroll.bind(this));
    }

    handleScroll() {
        if (this.loading || !this.hasMore) return;

        const scrollTop = window.scrollY;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;

        // Load more when 80% scrolled
        if (scrollTop + windowHeight >= documentHeight * 0.8) {
            this.loadMore();
        }
    }

    async loadMore() {
        this.loading = true;
        
        // Show loading skeleton
        this.showLoadingSkeleton();

        try {
            const response = await fetch(`${this.loadMoreUrl}?page=${this.page}`);
            const data = await response.json();

            if (data.wallpapers.length === 0) {
                this.hasMore = false;
                this.showNoMoreContent();
                return;
            }

            // Append new wallpapers
            this.appendWallpapers(data.wallpapers);
            this.page++;

        } catch (error) {
            console.error('Error loading more wallpapers:', error);
        } finally {
            this.loading = false;
            this.hideLoadingSkeleton();
        }
    }

    showLoadingSkeleton() {
        const skeleton = document.createElement('div');
        skeleton.className = 'loading-skeleton';
        skeleton.innerHTML = `
            <div class="skeleton-grid">
                ${Array(12).fill('<div class="skeleton-card"></div>').join('')}
            </div>
        `;
        this.container.parentNode.insertBefore(skeleton, this.container.nextSibling);
    }

    hideLoadingSkeleton() {
        const skeleton = document.querySelector('.loading-skeleton');
        if (skeleton) skeleton.remove();
    }

    appendWallpapers(wallpapers) {
        const grid = this.container;
        wallpapers.forEach(wallpaper => {
            const card = this.createWallpaperCard(wallpaper);
            grid.appendChild(card);
        });

        // Initialize lazy loading for new images
        this.initLazyLoading();
    }

    createWallpaperCard(wallpaper) {
        const card = document.createElement('div');
        card.className = 'wallpaper-card';
        card.innerHTML = `
            <!-- Card HTML structure similar to template -->
        `;
        return card;
    }

    initLazyLoading() {
        const lazyImages = document.querySelectorAll('.wallpaper-thumbnail[loading="lazy"]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        imageObserver.unobserve(img);
                    }
                });
            });

            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }
}