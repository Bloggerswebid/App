document.addEventListener('DOMContentLoaded', function() {
  const tocContainer = document.getElementById('toc');
  
  if (tocContainer) {
    // Generate heading IDs if they don't exist
    const headings = document.querySelectorAll('.post-content h2, .post-content h3, .post-content h4, .post-content h5, .post-content h6');
    
    headings.forEach(heading => {
      if (!heading.id) {
        heading.id = heading.textContent.toLowerCase()
          .replace(/[^\w\s-]/g, '')
          .replace(/\s+/g, '-');
      }
    });
    
    // Make TOC sticky
    const postContent = document.querySelector('.post-content');
    
    if (postContent && window.innerWidth >= 992) {
      const tocOffset = tocContainer.offsetTop;
      
      window.addEventListener('scroll', function() {
        if (window.pageYOffset > tocOffset) {
          tocContainer.classList.add('sticky');
        } else {
          tocContainer.classList.remove('sticky');
        }
      });
    }
    
    // Highlight current section in TOC
    window.addEventListener('scroll', highlightToc);
    
    function highlightToc() {
      if (headings.length === 0) return;
      
      // Find the heading that's currently at the top of the viewport
      let current = '';
      
      headings.forEach(heading => {
        const sectionTop = heading.offsetTop - 100;
        
        if (window.scrollY >= sectionTop) {
          current = heading.id;
        }
      });
      
      // Remove 'active' class from all TOC links
      const tocLinks = document.querySelectorAll('.toc-link');
      tocLinks.forEach(link => {
        link.classList.remove('active');
      });
      
      // Add 'active' class to current section's TOC link
      if (current) {
        const activeLink = document.querySelector(`.toc-link[href="#${current}"]`);
        if (activeLink) {
          activeLink.classList.add('active');
        }
      }
    }
    
    // Smooth scroll to section when clicking on TOC links
    const tocLinks = document.querySelectorAll('.toc-link');
    
    tocLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href');
        const targetSection = document.querySelector(targetId);
        
        if (targetSection) {
          window.scrollTo({
            top: targetSection.offsetTop - 80,
            behavior: 'smooth'
          });
        }
      });
    });
  }
});
