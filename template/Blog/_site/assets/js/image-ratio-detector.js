/**
 * Image Ratio Detector
 * 
 * This script automatically detects image aspect ratios and applies appropriate styling
 * based on whether images are portrait (tall), landscape (wide), or square.
 * 
 * It works with the custom CSS to ensure consistent presentation of images regardless of
 * their original dimensions.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Process all images in post content and responsive containers
  processAllImages();
  
  // Set up mutation observer to handle dynamically loaded images
  observeDynamicImages();
});

// Process all images in the document
function processAllImages() {
  // Target all responsive images in the document
  const images = document.querySelectorAll('.responsive-image, .post-content img');
  
  images.forEach(function(img) {
    // Skip images that already have been processed
    if (img.hasAttribute('data-ratio-processed')) return;
    
    // Mark as processed to avoid duplicate handling
    img.setAttribute('data-ratio-processed', 'true');
    
    // Handle image load event for accurate dimension detection
    if (img.complete) {
      determineImageRatio(img);
    } else {
      img.addEventListener('load', function() {
        determineImageRatio(img);
      });
    }
    
    // Add error handling for broken images
    img.addEventListener('error', function() {
      handleBrokenImage(img);
    });
  });
}

// Determine image ratio and apply appropriate styling
function determineImageRatio(img) {
  // Get the natural dimensions of the image
  const width = img.naturalWidth;
  const height = img.naturalHeight;
  
  if (width === 0 || height === 0) return; // Skip invalid images
  
  // Calculate aspect ratio
  const ratio = width / height;
  
  // Get container element
  const container = img.closest('.responsive-image-container') || img.parentNode;
  
  // Apply ratio classification
  let ratioClass;
  
  if (ratio < 0.85) {
    // Portrait (tall) image
    ratioClass = 'portrait';
  } else if (ratio > 1.15) {
    // Landscape (wide) image
    ratioClass = 'landscape';
  } else {
    // Square-ish image
    ratioClass = 'square';
  }
  
  // Apply the ratio attribute to the container
  container.setAttribute('data-ratio', ratioClass);
  
  // Special case for featured post images - force aspect ratio for consistency
  if (container.closest('.post-card') || container.closest('.featured-post')) {
    img.style.aspectRatio = '630/330';
    img.style.objectFit = 'cover';
  }
  
  // For post content images, apply appropriate styles based on ratio
  if (container.closest('.post-content')) {
    if (ratioClass === 'portrait') {
      img.style.maxHeight = '800px';
      img.style.width = 'auto';
      img.style.margin = '0 auto';
      img.style.display = 'block';
    } else {
      img.style.width = '100%';
      img.style.height = 'auto';
    }
  }
}

// Handle broken images
function handleBrokenImage(img) {
  // Find the default image path
  const container = img.closest('.responsive-image-container');
  const defaultImage = container ? 
    container.getAttribute('data-default-image') || '/assets/images/default-thumbnail.svg' : 
    '/assets/images/default-thumbnail.svg';
  
  // Apply fallback image if not already done
  if (!img.classList.contains('image-fallback')) {
    img.src = defaultImage;
    img.classList.add('image-fallback');
    
    // Save original source for debugging
    img.setAttribute('data-original-src', img.getAttribute('src') || '');
    
    // Set a fixed aspect ratio for broken images to maintain layout
    img.style.aspectRatio = '630/330';
  }
}

// Set up mutation observer to handle dynamically added images
function observeDynamicImages() {
  // Create mutation observer configuration
  const config = { 
    childList: true, 
    subtree: true 
  };
  
  // Create an observer instance
  const observer = new MutationObserver(function(mutations) {
    let hasNewImages = false;
    
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList' && mutation.addedNodes.length) {
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === 1) { // Element node
            if (node.matches && (node.matches('img') || node.matches('.responsive-image'))) {
              hasNewImages = true;
            } else if (node.querySelectorAll) {
              const childImages = node.querySelectorAll('img, .responsive-image');
              if (childImages.length > 0) {
                hasNewImages = true;
              }
            }
          }
        });
      }
    });
    
    if (hasNewImages) {
      processAllImages();
    }
  });
  
  // Start observing
  observer.observe(document.body, config);
}