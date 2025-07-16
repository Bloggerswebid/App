// Simple live search functionality for Jekyll
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('search-input');
  const liveSearchResults = document.getElementById('live-search-results');
  let searchIndex = [];
  
  if (!searchInput) return;
  
  // Load search index
  fetch('/search.json')
    .then(response => response.json())
    .then(data => {
      searchIndex = data;
      
      // Set up live search
      searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase().trim();
        
        if (query.length < 2) {
          if (liveSearchResults) {
            liveSearchResults.innerHTML = '';
            liveSearchResults.style.display = 'none';
          }
          return;
        }
        
        const results = searchIndex.filter(item => {
          const titleMatch = item.title && item.title.toLowerCase().includes(query);
          const contentMatch = item.content && item.content.toLowerCase().includes(query);
          const tagsMatch = item.tags && item.tags.some(tag => tag && tag.toLowerCase().includes(query));
          const categoryMatch = item.categories && item.categories.some(category => category && category.toLowerCase().includes(query));
          
          return titleMatch || contentMatch || tagsMatch || categoryMatch;
        }).slice(0, 5);
        
        if (liveSearchResults) {
          if (results.length === 0) {
            liveSearchResults.innerHTML = `<p>No results found for "${query}"</p>`;
          } else {
            let html = '<ul class="live-search-list">';
            
            results.forEach(result => {
              const resultUrl = result.url.startsWith('/') ? result.url : '/' + result.url;
              html += `
                <li class="live-search-item">
                  <a href="${resultUrl}">
                    <span class="live-search-title">${result.title}</span>
                    <span class="live-search-category">${result.categories && result.categories.length > 0 ? result.categories[0] : ''}</span>
                  </a>
                </li>
              `;
            });
            
            html += `
              <li class="live-search-more">
                <a href="/search/?q=${encodeURIComponent(query)}">View all results</a>
              </li>
            `;
            html += '</ul>';
            
            liveSearchResults.innerHTML = html;
          }
          
          liveSearchResults.style.display = 'block';
        }
      });
      
      // Hide live search results when clicking outside
      document.addEventListener('click', function(e) {
        if (liveSearchResults && !searchInput.contains(e.target) && !liveSearchResults.contains(e.target)) {
          liveSearchResults.style.display = 'none';
        }
      });
    })
    .catch(error => {
      console.error('Error loading search data:', error);
    });
});