document.addEventListener('DOMContentLoaded', function() {
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Enhanced mobile menu toggle with animations
  const menuToggleBtn = document.getElementById('menu-toggle-btn');
  const mobileMenu = document.getElementById('mobileMenu');
  const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
  const body = document.body;
  
  if (menuToggleBtn && mobileMenu) {
    // Toggle mobile menu
    menuToggleBtn.addEventListener('click', function() {
      toggleMobileMenu();
    });
    
    // Close menu on overlay click
    if (mobileMenuOverlay) {
      mobileMenuOverlay.addEventListener('click', function() {
        closeMobileMenu();
      });
    }
    
    // Close menu on escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
        closeMobileMenu();
      }
    });
    
    // Helper functions for mobile menu
    function toggleMobileMenu() {
      mobileMenu.classList.toggle('active');
      if (mobileMenuOverlay) {
        mobileMenuOverlay.classList.toggle('active');
      }
      menuToggleBtn.setAttribute('aria-expanded', mobileMenu.classList.contains('active'));
      
      // Prevent body scrolling when menu is open
      if (mobileMenu.classList.contains('active')) {
        body.style.overflow = 'hidden';
        // Change menu icon to X with animation
        const menuIcon = menuToggleBtn.querySelector('i');
        if (menuIcon) {
          menuIcon.style.transform = 'rotate(90deg)';
          menuIcon.style.opacity = '0';
          
          setTimeout(() => {
            menuIcon.setAttribute('data-feather', 'x');
            if (typeof feather !== 'undefined') {
              feather.replace();
              setTimeout(() => {
                menuIcon.style.transform = 'rotate(0deg)';
                menuIcon.style.opacity = '1';
              }, 50);
            }
          }, 200);
        }
      } else {
        body.style.overflow = '';
        // Change X icon back to menu with animation
        const menuIcon = menuToggleBtn.querySelector('i');
        if (menuIcon) {
          menuIcon.style.transform = 'rotate(-90deg)';
          menuIcon.style.opacity = '0';
          
          setTimeout(() => {
            menuIcon.setAttribute('data-feather', 'menu');
            if (typeof feather !== 'undefined') {
              feather.replace();
              setTimeout(() => {
                menuIcon.style.transform = 'rotate(0deg)';
                menuIcon.style.opacity = '1';
              }, 50);
            }
          }, 200);
        }
      }
    }
    
    function closeMobileMenu() {
      if (!mobileMenu.classList.contains('active')) return;
      
      mobileMenu.classList.remove('active');
      if (mobileMenuOverlay) {
        mobileMenuOverlay.classList.remove('active');
      }
      menuToggleBtn.setAttribute('aria-expanded', 'false');
      body.style.overflow = '';
      
      // Change X icon back to menu with animation
      const menuIcon = menuToggleBtn.querySelector('i');
      if (menuIcon) {
        menuIcon.style.transform = 'rotate(-90deg)';
        menuIcon.style.opacity = '0';
        
        setTimeout(() => {
          menuIcon.setAttribute('data-feather', 'menu');
          if (typeof feather !== 'undefined') {
            feather.replace();
            setTimeout(() => {
              menuIcon.style.transform = 'rotate(0deg)';
              menuIcon.style.opacity = '1';
            }, 50);
          }
        }, 200);
      }
    }
    
    // Close mobile menu when clicking regular links (not submenu toggles)
    const mobileMenuLinks = document.querySelectorAll('.mobile-menu .nav-menu li:not(.menu-item-has-children) > a');
    mobileMenuLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        // Allow time for the click animation
        setTimeout(() => {
          closeMobileMenu();
        }, 300);
      });
    });
    
    // Also close when clicking submenus' links
    const submenuLinks = document.querySelectorAll('.mobile-menu .sub-menu li a');
    submenuLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        // Allow time for the click animation
        setTimeout(() => {
          closeMobileMenu();
        }, 300);
      });
    });
  }
  
  // Enhanced submenu toggles for mobile with animations
  const hasChildrenItems = document.querySelectorAll('.mobile-menu .menu-item-has-children > a');
  
  hasChildrenItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      this.classList.toggle('active');
      const parent = this.parentNode;
      const submenu = parent.querySelector('.sub-menu');
      
      // Close other open submenus with animation
      const openSubmenus = parent.parentNode.querySelectorAll('.sub-menu.active');
      const openMenuLinks = parent.parentNode.querySelectorAll('.menu-item-has-children > a.active');
      
      openSubmenus.forEach(menu => {
        if (menu !== submenu) {
          // Animate closing
          menu.style.opacity = '0';
          menu.style.transform = 'translateY(-10px)';
          
          setTimeout(() => {
            menu.classList.remove('active');
            menu.style.opacity = '';
            menu.style.transform = '';
          }, 300);
        }
      });
      
      openMenuLinks.forEach(link => {
        if (link !== this) {
          link.classList.remove('active');
        }
      });
      
      if (submenu) {
        if (submenu.classList.contains('active')) {
          // Animate closing
          submenu.style.opacity = '0';
          submenu.style.transform = 'translateY(-10px)';
          
          setTimeout(() => {
            submenu.classList.remove('active');
            submenu.style.opacity = '';
            submenu.style.transform = '';
          }, 300);
        } else {
          submenu.classList.add('active');
        }
      }
    });
  });
  
  // Simple search toggle functionality
  const searchToggleBtn = document.getElementById('search-toggle-btn');
  const searchBox = document.getElementById('searchBox');
  
  if (searchToggleBtn && searchBox) {
    searchToggleBtn.addEventListener('click', function(e) {
      e.preventDefault();
      searchBox.classList.toggle('active');
      
      if (searchBox.classList.contains('active')) {
        setTimeout(() => {
          const searchInput = searchBox.querySelector('#search-input');
          if (searchInput) {
            searchInput.focus();
          }
        }, 100);
      }
    });
    
    // Close search on click outside
    document.addEventListener('click', function(e) {
      if (searchBox && searchBox.classList.contains('active')) {
        if (!searchBox.contains(e.target) && !searchToggleBtn.contains(e.target)) {
          searchBox.classList.remove('active');
        }
      }
    });
    
    // Close search on escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && searchBox && searchBox.classList.contains('active')) {
        searchBox.classList.remove('active');
      }
    });
  }
  
  // Back to top button
  const backToTopButton = document.getElementById('back-to-top-btn');
  
  if (backToTopButton) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 300) {
        backToTopButton.style.display = 'flex';
      } else {
        backToTopButton.style.display = 'none';
      }
    });
    
    backToTopButton.addEventListener('click', function(e) {
      e.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }
  
  // Enhanced lazy loading for images
  const defaultImagePath = '/assets/img/default-post-image.svg';
  
  // Create a placeholder gradient while images load
  function createPlaceholders() {
    document.querySelectorAll('.responsive-image-container').forEach(container => {
      if (!container.classList.contains('placeholder-added')) {
        const width = container.offsetWidth;
        const height = container.offsetHeight || width * 0.56; // fallback to 16:9 ratio
        
        // Add placeholder styles
        container.style.background = `linear-gradient(110deg, #ececec 8%, #f5f5f5 18%, #ececec 33%)`;
        container.style.backgroundSize = `200% 100%`;
        container.style.animation = `placeholderShimmer 1.5s linear infinite`;
        container.classList.add('placeholder-added');
      }
    });
  }
  
  // Advanced lazy loading implementation
  function initLazyLoading() {
    // Placeholder animation
    if (!document.getElementById('placeholder-animation')) {
      const style = document.createElement('style');
      style.id = 'placeholder-animation';
      style.textContent = `
        @keyframes placeholderShimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        .responsive-image-container.loaded {
          background: none;
          animation: none;
        }
        .image-fallback {
          opacity: 0.7;
          filter: grayscale(0.5);
        }
      `;
      document.head.appendChild(style);
    }
    
    createPlaceholders();
    
    if ('loading' in HTMLImageElement.prototype) {
      // Native lazy loading (modern browsers)
      document.querySelectorAll('img.responsive-image[loading="lazy"]').forEach(img => {
        if (img.dataset.src) {
          // Add load event before setting src
          img.addEventListener('load', function() {
            const container = this.closest('.responsive-image-container');
            if (container) {
              container.classList.add('loaded');
            }
            this.style.opacity = '1';
          });
          
          // Set the actual image source
          img.src = img.dataset.src;
        }
      });
    } else {
      // Fallback for browsers that don't support native lazy loading
      const lazyImageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const lazyImage = entry.target;
            if (lazyImage.dataset.src) {
              // Add load event
              lazyImage.addEventListener('load', function() {
                const container = this.closest('.responsive-image-container');
                if (container) {
                  container.classList.add('loaded');
                }
                this.style.opacity = '1';
              });
              
              // Set image source
              lazyImage.src = lazyImage.dataset.src;
            }
            lazyImageObserver.unobserve(lazyImage);
          }
        });
      }, { rootMargin: '200px' }); // Start loading images 200px before they enter viewport
      
      document.querySelectorAll('img.responsive-image[data-src]').forEach(img => {
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.3s ease';
        lazyImageObserver.observe(img);
      });
    }
  }
  
  // Fix broken image paths and undefined errors
  function fixBrokenLinks() {
    // Fix undefined links
    document.querySelectorAll('a[href="/undefined"], a[href*="/undefined"]').forEach(link => {
      const parent = link.closest('.post-card, .related-post');
      if (parent) {
        link.href = '#';
        link.setAttribute('data-original-link', 'undefined');
        link.addEventListener('click', (e) => {
          e.preventDefault();
        });
      }
    });
    
    // Set up global image fallback handler
    window.imageFallbackCallback = function(imgElement) {
      const container = imgElement.closest('.responsive-image-container');
      const originalSrc = imgElement.getAttribute('data-original-src');
      const title = container ? container.getAttribute('data-title') || imgElement.alt || 'Image' : imgElement.alt || 'Image';
      
      // Store information about broken images for SEO purposes
      if (!window.brokenImages) window.brokenImages = new Set();
      if (originalSrc) window.brokenImages.add(originalSrc);
      
      // Add structured data for SEO even if image is broken
      if (container && !container.querySelector('.image-seo-metadata')) {
        const metaDiv = document.createElement('div');
        metaDiv.className = 'image-seo-metadata';
        metaDiv.setAttribute('itemscope', '');
        metaDiv.setAttribute('itemtype', 'http://schema.org/ImageObject');
        metaDiv.style.display = 'none';
        
        const metaName = document.createElement('meta');
        metaName.setAttribute('itemprop', 'name');
        metaName.content = title;
        
        const metaURL = document.createElement('meta');
        metaURL.setAttribute('itemprop', 'contentUrl');
        metaURL.content = originalSrc || imgElement.src;
        
        metaDiv.appendChild(metaName);
        metaDiv.appendChild(metaURL);
        container.appendChild(metaDiv);
      }
      
      // Add label for broken image (development only)
      if (container && !container.querySelector('.broken-image-label')) {
        // Only for development environment
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname.includes('0.0.0.0')) {
              const label = document.createElement('span');
              label.className = 'broken-image-label';
              label.textContent = 'Missing: ' + title;
              container.appendChild(label);
            }
          }
        });
      }
    });
  }
  
  // Run the functions
  initLazyLoading();
  fixBrokenLinks();
  
  // Re-run when new content might be added (e.g. infinite scroll or AJAX)
  document.addEventListener('content-updated', function() {
    initLazyLoading();
    fixBrokenLinks();
  });
  
  // Check and fix after window load to catch any missed images
  window.addEventListener('load', function() {
    initLazyLoading();
    fixBrokenLinks();
  });
});
