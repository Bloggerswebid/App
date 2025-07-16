module Jekyll
  # Plugin to optimize performance of Jekyll
  
  # Optimize the rendering process by caching expensive operations
  class OptimizeRendering < Jekyll::Generator
    priority :high
    
    def generate(site)
      Jekyll.logger.info "Performance:", "Optimizing site rendering process"
      # Store data that will be reused frequently
      site.data["optimize_cache"] = {}
      
      # Cache common filters for better performance
      site.data["optimize_cache"]["slugs"] = {}
      site.posts.docs.each do |post|
        if post.data["title"]
          slug = post.data["title"].to_s.downcase.strip.gsub(/\s+/, '-').gsub(/[^\w-]/, '')
          site.data["optimize_cache"]["slugs"][post.data["title"]] = slug 
        end
      end
      
      # Calculate common values once
      site.data["optimize_cache"]["tag_counts"] = count_tag_usage(site)
      site.data["optimize_cache"]["category_counts"] = count_category_usage(site)
    end
    
    private
    
    def count_tag_usage(site)
      tag_counts = Hash.new(0)
      site.posts.docs.each do |post|
        Array(post.data["tags"]).each do |tag|
          tag_counts[tag] += 1 if tag
        end
      end
      tag_counts
    end
    
    def count_category_usage(site)
      category_counts = Hash.new(0)
      site.posts.docs.each do |post|
        Array(post.data["categories"]).each do |category|
          category_counts[category] += 1 if category
        end
      end
      category_counts
    end
  end
  
  # Optimize HTML output
  class HtmlOptimizer
    def self.process_output(output)
      # Only process HTML files
      return output unless output =~ /<html/i
      
      # Remove unnecessary whitespace
      output = output.gsub(/^\s+/, '')
      
      # Remove HTML comments (except IE conditionals)
      output = output.gsub(/<!--(?!\s*\[if)(?!.*?\[endif\]\s*).*?-->/m, '')
      
      # Optimize script loading
      output = output.gsub(/<script([^>]*)>(\s*)<\/script>/, '<script\1></script>')
      
      # Add importance to critical resources
      output = output.gsub(/<link([^>]*)(stylesheet)([^>]*)>/, '<link\1stylesheet\3 importance="high">')
      
      output
    end
  end
  
  # Hook into the site render process
  Jekyll::Hooks.register :site, :post_render do |site|
    # Only perform optimization in production
    if Jekyll.env == "production"
      site.pages.each do |page|
        if page.output_ext == ".html"
          page.output = HtmlOptimizer.process_output(page.output)
        end
      end
      
      site.posts.docs.each do |post|
        if post.output_ext == ".html"
          post.output = HtmlOptimizer.process_output(post.output)
        end
      end
    end
  end
end