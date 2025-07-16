#!/usr/bin/env ruby

require 'webrick'
require 'yaml'
require 'json'
require 'erb'

# Simple Jekyll-like server for development
class JekyllServer
  def initialize(port = 5000)
    @port = port
    @config = load_config
    @posts = load_posts
    @pages = load_pages
    @categories = collect_categories
  end

  def start
    server = WEBrick::HTTPServer.new(
      Port: @port,
      DocumentRoot: '_site',
      DirectoryIndex: ['index.html']
    )

    # Generate static files
    generate_site

    # Custom routes
    server.mount_proc '/categories' do |req, res|
      serve_categories(req, res)
    end

    server.mount_proc '/categories/' do |req, res|
      serve_category_page(req, res)
    end

    puts "Jekyll-like server running on http://0.0.0.0:#{@port}"
    puts "Press Ctrl+C to stop"

    trap('INT') { server.shutdown }
    server.start
  end

  private

  def load_config
    if File.exist?('_config.yml')
      YAML.load_file('_config.yml')
    else
      {}
    end
  end

  def load_posts
    posts = []
    if Dir.exist?('_posts')
      Dir.glob('_posts/*.md').each do |file|
        content = File.read(file)
        if content.start_with?('---')
          parts = content.split('---', 3)
          front_matter = YAML.safe_load(parts[1], permitted_classes: [Date, Time])
          body = parts[2]
          
          front_matter['content'] = body
          front_matter['url'] = "/#{File.basename(file, '.md')}/"
          posts << front_matter
        end
      end
    end
    posts.sort_by { |p| p['date'] || Time.now }.reverse
  end

  def load_pages
    pages = []
    Dir.glob('_pages/*.md').each do |file|
      content = File.read(file)
      if content.start_with?('---')
        parts = content.split('---', 3)
        front_matter = YAML.safe_load(parts[1], permitted_classes: [Date, Time])
        body = parts[2]
        
        front_matter['content'] = body
        pages << front_matter
      end
    end if Dir.exist?('_pages')
    pages
  end

  def collect_categories
    categories = {}
    @posts.each do |post|
      if post['categories']
        cats = post['categories'].is_a?(Array) ? post['categories'] : [post['categories']]
        cats.each do |cat|
          categories[cat] ||= []
          categories[cat] << post
        end
      end
    end
    categories
  end

  def generate_site
    # Create _site directory
    FileUtils.mkdir_p('_site')
    
    # Copy static assets
    %w[assets css js images].each do |dir|
      if Dir.exist?(dir)
        FileUtils.cp_r(dir, '_site/')
      end
    end

    # Generate index
    generate_index
    
    # Generate category pages
    generate_category_pages
    
    # Generate individual post pages
    generate_posts
  end

  def generate_index
    template = <<~HTML
      <!DOCTYPE html>
      <html>
      <head>
        <title><%= @config['title'] || 'Jekyll Blog' %></title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
          .navbar-brand { font-weight: bold; }
          .post-card { border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 1.5rem; }
          .post-meta { color: #666; font-size: 0.9rem; }
          .categories-nav { background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 2rem; }
          .category-link { display: inline-block; margin-right: 1rem; margin-bottom: 0.5rem; }
        </style>
      </head>
      <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
          <div class="container">
            <a class="navbar-brand" href="/"><%= @config['title'] || 'Jekyll Blog' %></a>
            <div class="navbar-nav ms-auto">
              <a class="nav-link" href="/">Home</a>
              <a class="nav-link" href="/categories">Categories</a>
              <a class="nav-link" href="/about">About</a>
            </div>
          </div>
        </nav>

        <div class="container mt-4">
          <div class="row">
            <div class="col-md-8">
              <h1>Latest Posts</h1>
              <% @posts.each do |post| %>
                <div class="post-card p-3">
                  <h3><a href="<%= post['url'] %>" class="text-decoration-none"><%= post['title'] %></a></h3>
                  <div class="post-meta mb-2">
                    <% if post['date'] %>
                      <span>📅 <%= post['date'] %></span>
                    <% end %>
                    <% if post['categories'] %>
                      <span class="ms-2">📂 <%= [post['categories']].flatten.join(', ') %></span>
                    <% end %>
                  </div>
                  <% if post['excerpt'] %>
                    <p><%= post['excerpt'] %></p>
                  <% end %>
                </div>
              <% end %>
            </div>
            
            <div class="col-md-4">
              <div class="categories-nav">
                <h5>📂 Categories</h5>
                <% @categories.each do |cat, posts| %>
                  <div class="category-link">
                    <a href="/categories/<%= cat.downcase.gsub(' ', '-') %>" class="btn btn-outline-primary btn-sm">
                      <%= cat %> (<%= posts.length %>)
                    </a>
                  </div>
                <% end %>
              </div>
            </div>
          </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
      </body>
      </html>
    HTML

    result = ERB.new(template).result(binding)
    File.write('_site/index.html', result)
  end

  def generate_category_pages
    FileUtils.mkdir_p('_site/categories')
    
    # Main categories page
    template = <<~HTML
      <!DOCTYPE html>
      <html>
      <head>
        <title>Categories - <%= @config['title'] || 'Jekyll Blog' %></title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
          .navbar-brand { font-weight: bold; }
          .category-card { 
            border: 1px solid #e0e0e0; 
            border-radius: 8px; 
            margin-bottom: 1.5rem; 
            padding: 1.5rem;
            transition: transform 0.2s;
          }
          .category-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        </style>
      </head>
      <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
          <div class="container">
            <a class="navbar-brand" href="/"><%= @config['title'] || 'Jekyll Blog' %></a>
            <div class="navbar-nav ms-auto">
              <a class="nav-link" href="/">Home</a>
              <a class="nav-link" href="/categories">Categories</a>
              <a class="nav-link" href="/about">About</a>
            </div>
          </div>
        </nav>

        <div class="container mt-4">
          <h1>📂 Categories</h1>
          <p class="text-muted mb-4">Explore articles by category</p>
          
          <div class="row">
            <% @categories.each do |cat, posts| %>
              <div class="col-md-6 mb-4">
                <div class="category-card">
                  <h3><a href="/categories/<%= cat.downcase.gsub(' ', '-') %>" class="text-decoration-none"><%= cat %></a></h3>
                  <p><%= posts.length %> articles</p>
                  
                  <div class="recent-posts">
                    <% posts.first(3).each do |post| %>
                      <div class="mb-2">
                        <a href="<%= post['url'] %>" class="text-decoration-none">
                          <small><%= post['title'] %></small>
                        </a>
                      </div>
                    <% end %>
                  </div>
                </div>
              </div>
            <% end %>
          </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
      </body>
      </html>
    HTML

    result = ERB.new(template).result(binding)
    File.write('_site/categories/index.html', result)
  end

  def generate_posts
    @posts.each do |post|
      # Create directory for post
      post_dir = "_site#{post['url']}"
      FileUtils.mkdir_p(post_dir)
      
      # Simple post template
      content = "<h1>#{post['title']}</h1><div>#{post['content']}</div>"
      File.write("#{post_dir}index.html", content)
    end
  end

  def serve_categories(req, res)
    res.body = File.read('_site/categories/index.html')
    res.content_type = 'text/html'
  end

  def serve_category_page(req, res)
    # Handle individual category pages
    category = req.path.split('/').last
    if @categories.key?(category)
      # Generate category page on-the-fly
      res.body = "<h1>Category: #{category}</h1>"
      res.content_type = 'text/html'
    else
      res.status = 404
      res.body = "Category not found"
    end
  end
end

# Start server
if __FILE__ == $0
  require 'fileutils'
  server = JekyllServer.new(5000)
  server.start
end