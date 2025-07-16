/**
 * Enhanced Image Optimizer for Better Performance and SEO
 * - Optimizes image loading
 * - Handles broken images
 * - Adds SEO metadata for all images
 * - Preloads important images
 */

(function() {
  'use strict';
  
  // Configuration
  const config = {
    defaultImage: '/assets/images/default-thumbnail.svg',
    preloadFeaturedImages: true,
    lazyLoadThreshold: 200,
    useIntersectionObserver: true,
    prioritizeAboveFold: true
  };
  
  // Utility function to check if we're in a development environment
  function isDevelopment() {
    return window.location.hostname === 'localhost' || 
           window.location.hostname === '127.0.0.1' || 
           window.location.hostname.includes('0.0.0.0');
  }
  
  // Handle broken images with advanced fallback
  function handleBrokenImage(img) {
    const container = img.closest('.responsive-image-container');
    const originalSrc = img.getAttribute('src');
    const defaultImage = container ? 
      container.getAttribute('data-default-image') || config.defaultImage : 
      config.defaultImage;
    const title = container ? 
      container.getAttribute('data-title') || img.alt || 'Image' : 
      img.alt || 'Image';
    
    // Set fallback image
    img.src = defaultImage;
    img.classList.add('image-fallback');
    img.setAttribute('data-original-src', originalSrc);
    
    // Track broken images for later analysis
    if (!window.brokenImages) window.brokenImages = new Set();
    window.brokenImages.add(originalSrc);
    
    // Add SEO metadata for the original image despite being broken
    addSEOMetadata(container || img.parentNode, title, originalSrc);
    
    // Add visual indicator in development
    if (isDevelopment() && container && !container.querySelector('.broken-image-label')) {
      const label = document.createElement('span');
      label.className = 'broken-image-label';
      label.textContent = 'Missing: ' + title;
      container.appendChild(label);
    }
  }
  
  // Add SEO-friendly structured data for images
  function addSEOMetadata(container, title, url) {
    if (!container || container.querySelector('.image-seo-metadata')) return;
    
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
    metaURL.content = url;
    
    metaDiv.appendChild(metaName);
    metaDiv.appendChild(metaURL);
    container.appendChild(metaDiv);
  }
  
  // Enable lazy loading using Intersection Observer for better performance
  function setupLazyLoading() {
    if (!('IntersectionObserver' in window) || !config.useIntersectionObserver) {
      // Fallback for browsers without Intersection Observer
      document.querySelectorAll('img.responsive-image[loading="lazy"]').forEach(img => {
        img.setAttribute('loading', 'eager');
      });
      return;
    }
    
    const lazyImageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          
          // Prioritize above-fold images
          if (config.prioritizeAboveFold && entry.boundingClientRect.top < window.innerHeight) {
            img.setAttribute('fetchpriority', 'high');
          }
          
          // Load the image if it hasn't already
          if (img.dataset.src && !img.src) {
            img.src = img.dataset.src;
            delete img.dataset.src;
          }
          
          // Stop observing this image
          observer.unobserve(img);
        }
      });
    }, {
      rootMargin: `${config.lazyLoadThreshold}px 0px ${config.lazyLoadThreshold}px 0px`,
      threshold: 0.01
    });
    
    // Observe all lazy-loaded images
    document.querySelectorAll('img.responsive-image[loading="lazy"]').forEach(img => {
      lazyImageObserver.observe(img);
    });
  }
  
  // Preload featured and important images for faster rendering
  function preloadImportantImages() {
    if (!config.preloadFeaturedImages) return;
    
    // Preload featured post images
    const featuredImages = document.querySelectorAll('.featured-post img.responsive-image');
    if (featuredImages.length > 0) {
      featuredImages.forEach(img => {
        img.setAttribute('loading', 'eager');
        img.setAttribute('fetchpriority', 'high');
      });
    }
    
    // Preload hero images
    const heroImages = document.querySelectorAll('.hero-section img.responsive-image');
    if (heroImages.length > 0) {
      heroImages.forEach(img => {
        img.setAttribute('loading', 'eager');
        img.setAttribute('fetchpriority', 'high');
      });
    }
  }
  
  // Initialize the image optimizer
  function init() {
    // Set up global callback for image error handling
    window.imageFallbackCallback = handleBrokenImage;
    
    // Handle all images on the page
    document.querySelectorAll('img.responsive-image').forEach(img => {
      // Add error handling to catch broken images
      if (!img.hasAttribute('data-error-handled')) {
        img.setAttribute('data-error-handled', 'true');
        img.addEventListener('error', function() {
          handleBrokenImage(this);
        });
      }
      
      // Add SEO metadata
      const container = img.closest('.responsive-image-container');
      const title = container ? 
        container.getAttribute('data-title') || img.alt || 'Image' : 
        img.alt || 'Image';
      addSEOMetadata(container || img.parentNode, title, img.src);
    });
    
    // Set up optimized image loading
    setupLazyLoading();
    preloadImportantImages();
  }
  
  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Re-run when new content is added
  document.addEventListener('content-updated', init);
})();