document.addEventListener('DOMContentLoaded', function() {
  const disqusContainer = document.getElementById('disqus-container');
  
  if (disqusContainer) {
    const disqusThread = document.getElementById('disqus_thread');
    const disqusShortname = disqusThread.getAttribute('data-disqus-shortname');
    
    if (!disqusShortname) {
      console.error('Disqus shortname not found');
      return;
    }
    
    // Only load Disqus when scrolled to comments section
    function loadDisqus() {
      if (disqusLoaded) return;
      
      const disqusObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            loadDisqusComments();
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1 });
      
      disqusObserver.observe(disqusContainer);
    }
    
    // Actual Disqus loading function
    let disqusLoaded = false;
    
    function loadDisqusComments() {
      if (disqusLoaded) return;
      
      const disqus_config = function() {
        this.page.url = window.location.href;
        this.page.identifier = window.location.pathname;
      };
      
      const d = document;
      const s = d.createElement('script');
      s.src = 'https://' + disqusShortname + '.disqus.com/embed.js';
      s.setAttribute('data-timestamp', +new Date());
      (d.head || d.body).appendChild(s);
      
      disqusLoaded = true;
      
      // Show loading indicator
      disqusThread.innerHTML = '<div class="disqus-loading">Loading comments...</div>';
    }
    
    // Check if IntersectionObserver is supported
    if ('IntersectionObserver' in window) {
      loadDisqus();
    } else {
      // Fallback for older browsers
      window.addEventListener('scroll', function() {
        const rect = disqusContainer.getBoundingClientRect();
        const isVisible = rect.top < window.innerHeight && rect.bottom >= 0;
        
        if (isVisible) {
          loadDisqusComments();
          window.removeEventListener('scroll', this);
        }
      });
    }
    
    // Also load if user clicks on comments heading
    const commentsHeading = disqusContainer.querySelector('h3');
    if (commentsHeading) {
      commentsHeading.addEventListener('click', loadDisqusComments);
    }
  }
});
