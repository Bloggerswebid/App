module Jekyll
  # A Page subclass used to generate category pages
  class CategoryPage < Page
    def initialize(site, base, dir, category)
      @site = site
      @base = base
      @dir = dir
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(base, '_layouts'), 'category.html')
      self.data['category'] = category
      self.data['title'] = category
    end
  end

  # A Page subclass used to generate tag pages
  class TagPage < Page
    def initialize(site, base, dir, tag)
      @site = site
      @base = base
      @dir = dir
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(base, '_layouts'), 'tag.html')
      self.data['tag'] = tag
      self.data['title'] = tag
    end
  end

  # Generator for category and tag pages
  class CategoryPageGenerator < Generator
    safe true
    
    def generate(site)
      if site.layouts.key? 'category'
        # Track already generated categories to avoid duplicates
        generated_categories = {}
        
        site.categories.keys.each do |category|
          # Convert the category name to a URL-friendly slug
          category_slug = category.to_s.downcase.strip.gsub(' ', '-').gsub(/[^\w-]/, '')
          
          # Skip if we've already generated this category
          if generated_categories[category_slug]
            # Silenced the warning to avoid confusion
            # Jekyll.logger.warn "Skipping duplicate category:", "#{category} (slug: #{category_slug})"
            next
          end
          
          # Mark this category as generated
          generated_categories[category_slug] = true
          
          # Create the category page
          site.pages << CategoryPage.new(site, site.source, File.join('category', category_slug), category)
        end
      end
    end
  end

  class TagPageGenerator < Generator
    safe true
    
    def generate(site)
      if site.layouts.key? 'tag'
        # Track already generated tags to avoid duplicates
        generated_tags = {}
        
        site.tags.keys.each do |tag|
          # Convert the tag name to a URL-friendly slug
          tag_slug = tag.to_s.downcase.strip.gsub(' ', '-').gsub(/[^\w-]/, '')
          
          # Skip if we've already generated this tag
          if generated_tags[tag_slug]
            # Silenced the warning to avoid confusion
            # Jekyll.logger.warn "Skipping duplicate tag:", "#{tag} (slug: #{tag_slug})"
            next
          end
          
          # Mark this tag as generated
          generated_tags[tag_slug] = true
          
          # Create the tag page
          site.pages << TagPage.new(site, site.source, File.join('tag', tag_slug), tag)
        end
      end
    end
  end
end