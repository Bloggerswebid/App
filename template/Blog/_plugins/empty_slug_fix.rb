module Jekyll
  class EmptySlugFix < Generator
    safe true
    priority :high

    def generate(site)
      # Fix empty slugs for categories - remove empty ones
      site.categories.keys.each do |category|
        if category.to_s.strip.empty?
          site.categories.delete(category)
        end
      end

      # Fix empty slugs for tags - remove empty ones
      site.tags.keys.each do |tag|
        if tag.to_s.strip.empty?
          site.tags.delete(tag)
        end
      end

      # Fix empty slugs in collections
      site.collections.each do |_, collection|
        collection.docs.each do |doc|
          # Skip documents that already have a permalink set
          next if doc.permalink

          # Set default slug for documents with empty slugs
          if doc.data['slug'].nil? || doc.data['slug'].to_s.strip.empty?
            # Use title as slug if available
            if doc.data['title'] && !doc.data['title'].strip.empty?
              doc.data['slug'] = Jekyll::Utils.slugify(doc.data['title'])
            else
              # Otherwise use appropriate default based on document type
              default_slug = case doc.collection.label
                             when 'posts'
                               'post-' + Time.now.strftime('%Y-%m-%d')
                             when 'pages'
                               'page-' + doc.basename_without_ext
                             else
                               'content-' + doc.basename_without_ext
                             end
              doc.data['slug'] = default_slug
            end
          end
        end
      end
    end
  end
end