#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import json
import random
import datetime
import urllib.request
import urllib.parse
from slugify import slugify
from langdetect import detect
import yaml

# Configuration
SUBJECTS_FILE = "KEYWORD.txt"
CONFIG_FILE = "config.txt"
OUTPUT_FOLDER = "_posts"
IMAGES_FOLDER = "assets/image"
ARTICLE_LINKS_FILE = "article_links.json"
PROCESSED_SUBJECTS_FILE = "processed_subjects.json"

class SimpleConfigManager:
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from config.txt"""
        default_config = {
            'domain': 'example.com',
            'articles_per_run': '2',
            'min_word_count': '5000',
            'max_word_count': '8000',
            'h2_min_words': '400',
            'h2_max_words': '600',
            'target_headings': '20',
            'language': 'English',
            'base_categories': 'Bisnis,Keuangan,Teknologi,Marketing',
            'author_name': 'Admin',
            'enable_auto_images': 'true',
            'images_per_article': '5',
            'min_images_per_article': '1'
        }
        
        if not os.path.exists(self.config_file):
            return default_config
        
        config = default_config.copy()
        with open(self.config_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        return config
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def get_int(self, key, default=0):
        try:
            return int(self.config.get(key, default))
        except:
            return default
    
    def get_bool(self, key, default=False):
        value = self.config.get(key, str(default)).lower()
        return value in ['true', '1', 'yes', 'on']

class SimpleAPIManager:
    def __init__(self, filename="apikey.txt"):
        self.filename = filename
        self.api_keys = self._load_api_keys()
        self.current_index = 0
        
    def _load_api_keys(self):
        """Load API keys from file"""
        if not os.path.exists(self.filename):
            return []
        
        keys = []
        with open(self.filename, "r", encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('AIza') and len(line) > 30:
                        keys.append(line)
        return keys
    
    def get_current_key(self):
        """Get current API key"""
        if not self.api_keys:
            return None
        return self.api_keys[self.current_index]
    
    def rotate_key(self):
        """Rotate to next API key"""
        if len(self.api_keys) > 1:
            self.current_index = (self.current_index + 1) % len(self.api_keys)

class SimpleImageScraper:
    """Enhanced image scraper for downloading relevant images with multiple fallback sources"""
    
    def __init__(self, images_folder="assets/image"):
        self.images_folder = images_folder
        self.ensure_images_folder()
        self.downloaded_cache = set()  # Track downloaded images to avoid duplicates
        
    def ensure_images_folder(self):
        """Create images folder if it doesn't exist"""
        os.makedirs(self.images_folder, exist_ok=True)
        
    def search_and_download_images(self, query, count=1):
        """Enhanced search and download images from multiple sources with fallbacks"""
        print(f"🔍 Mencari gambar untuk: {query}")
        
        downloaded_images = []
        max_attempts = count * 3  # Try more sources than needed
        
        # Strategy 1: Use Unsplash Source (most reliable)
        print("📸 Mencoba Unsplash Source...")
        images = self._get_unsplash_images(query, max_attempts)
        for i, image_url in enumerate(images):
            if len(downloaded_images) >= count:
                break
            downloaded_path = self._download_image(image_url, query, f"unsplash-{i}")
            if downloaded_path:
                downloaded_images.append(downloaded_path)
        
        # Strategy 2: Try Picsum Photos if we need more
        if len(downloaded_images) < count:
            print("🖼️  Mencoba Picsum Photos...")
            images = self._get_picsum_images(count - len(downloaded_images))
            for i, image_url in enumerate(images):
                if len(downloaded_images) >= count:
                    break
                downloaded_path = self._download_image(image_url, query, f"picsum-{i}")
                if downloaded_path:
                    downloaded_images.append(downloaded_path)
        
        # Strategy 3: Try high-quality business stock images
        if len(downloaded_images) < count:
            print("📊 Mencoba business stock images...")
            images = self._get_business_stock_images(count - len(downloaded_images))
            for i, image_url in enumerate(images):
                if len(downloaded_images) >= count:
                    break
                downloaded_path = self._download_image(image_url, query, f"business-{i}")
                if downloaded_path:
                    downloaded_images.append(downloaded_path)
        
        print(f"✅ Berhasil download {len(downloaded_images)} gambar dari {count} yang diminta")
        return downloaded_images
    
    def _get_unsplash_images(self, query, count=5):
        """Get images from Unsplash Source API with enhanced keyword processing"""
        try:
            images = []
            # Process keywords for better search results
            keywords = self._process_keywords(query)
            
            # Different image dimensions for variety
            dimensions = ['1200x800', '1600x900', '800x600', '1920x1080', '1024x768', '1280x720']
            
            for i in range(count):
                dim = dimensions[i % len(dimensions)]
                # Create unique URLs with different keyword combinations
                keyword_variant = self._get_keyword_variant(keywords, i)
                img_url = f"https://source.unsplash.com/{dim}/?{keyword_variant}&sig={random.randint(1, 1000)}"
                images.append(img_url)
            
            return images
            
        except Exception as e:
            print(f"❌ Unsplash gagal: {e}")
            return []
    
    def _process_keywords(self, query):
        """Process and enhance keywords for better image search"""
        # Extract key business terms and translate to English for better results
        business_terms = {
            'bisnis': 'business',
            'investasi': 'investment',
            'startup': 'startup',
            'teknologi': 'technology',
            'marketing': 'marketing',
            'digital': 'digital',
            'keuangan': 'finance',
            'saham': 'stocks',
            'produktivitas': 'productivity',
            'strategi': 'strategy'
        }
        
        keywords = query.lower()
        for indo, eng in business_terms.items():
            if indo in keywords:
                keywords = keywords.replace(indo, eng)
        
        # Clean and format keywords
        keywords = re.sub(r'[^\w\s]', '', keywords)
        keywords = ','.join(keywords.split()[:3])  # Take first 3 words
        return keywords
    
    def _get_keyword_variant(self, keywords, index):
        """Create keyword variants for diverse image results"""
        base_keywords = keywords.split(',')
        
        # Add contextual terms based on index
        context_terms = ['professional', 'modern', 'office', 'team', 'success', 'growth']
        if index < len(context_terms):
            base_keywords.append(context_terms[index])
        
        return ','.join(base_keywords[:3])
    
    def _get_picsum_images(self, count=5):
        """Get high-quality images from Picsum Photos"""
        try:
            images = []
            # Different image IDs for variety
            image_ids = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]
            dimensions = ['1200/800', '1600/900', '800/600', '1920/1080', '1024/768']
            
            for i in range(count):
                img_id = image_ids[i % len(image_ids)]
                dim = dimensions[i % len(dimensions)]
                img_url = f"https://picsum.photos/{dim}?random={img_id + i}"
                images.append(img_url)
            
            return images
            
        except Exception as e:
            print(f"❌ Picsum gagal: {e}")
            return []
    
    def _get_business_stock_images(self, count=5):
        """Get high-quality business stock images from reliable CDNs"""
        try:
            # Curated high-quality business images
            business_images = [
                "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1573164713714-d95e436ab8d6?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1553877522-43269d4ea984?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1556157382-97eda2d62296?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1552664730-d307ca884978?w=1200&h=800&fit=crop"
            ]
            
            return business_images[:count]
            
        except Exception as e:
            print(f"❌ Business stock images gagal: {e}")
            return []
    
    def _get_pixabay_images(self, query, count=5):
        """Get images from Pixabay CDN"""
        try:
            # Pre-selected high-quality business/tech images from Pixabay
            business_images = [
                "https://cdn.pixabay.com/photo/2016/11/27/21/42/stock-1863880_1280.jpg",
                "https://cdn.pixabay.com/photo/2016/11/29/06/15/plans-1867745_1280.jpg",
                "https://cdn.pixabay.com/photo/2017/07/31/11/21/people-2557396_1280.jpg",
                "https://cdn.pixabay.com/photo/2018/03/22/02/37/email-3249062_1280.jpg",
                "https://cdn.pixabay.com/photo/2015/01/08/18/24/children-593313_1280.jpg",
                "https://cdn.pixabay.com/photo/2016/01/09/18/27/startup-1130731_1280.jpg",
                "https://cdn.pixabay.com/photo/2017/08/01/08/29/woman-2563491_1280.jpg",
                "https://cdn.pixabay.com/photo/2015/07/17/22/43/student-849825_1280.jpg"
            ]
            
            return business_images[:count]
            
        except Exception as e:
            print(f"Pixabay gagal: {e}")
            return []
    
    def _download_image(self, image_url, query, index):
        """Download image from URL and save locally"""
        try:
            # Create safe filename with proper index handling
            safe_query = slugify(query)[:50]
            timestamp = int(time.time())
            index_str = str(index) if isinstance(index, str) else str(index)
            filename = f"{safe_query}-{index_str}-{timestamp}.jpg"
            filepath = os.path.join(self.images_folder, filename)
            
            # Headers for image download
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            # Create request
            req = urllib.request.Request(image_url, headers=headers)
            
            # Optimized download with reduced timeout for GitHub Actions
            with urllib.request.urlopen(req, timeout=15) as response:
                image_data = response.read()
                
                # Validate image data (minimum 1KB)
                if len(image_data) < 1024:
                    raise Exception("Image too small")
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                # Return relative path for markdown
                relative_path = f"/assets/image/{filename}"
                print(f"Downloaded: {filename}")
                return relative_path
                
        except Exception as e:
            print(f"Download gagal untuk {image_url}: {e}")
            return None

class SimpleSEOGenerator:
    def __init__(self):
        self.config = SimpleConfigManager()
        self.api_manager = SimpleAPIManager()
        self.image_scraper = SimpleImageScraper()
        
        # Ensure directories exist
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        os.makedirs(IMAGES_FOLDER, exist_ok=True)
        
        # Article links database for internal linking
        self.article_links_file = ARTICLE_LINKS_FILE
        self.load_article_links()
    
    def gemini_request(self, prompt, model="gemini-1.5-flash", max_retries=2):
        """Optimized Gemini API request for GitHub Actions"""
        for attempt in range(max_retries):
            try:
                api_key = self.api_manager.get_current_key()
                if not api_key:
                    raise Exception("No API key available")
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                
                data = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.6,
                        "topK": 30,
                        "topP": 0.9,
                        "maxOutputTokens": 5120,  # Reduced for faster processing
                    }
                }
                
                # Convert to JSON and encode
                json_data = json.dumps(data).encode('utf-8')
                
                # Create request
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'SEO-Generator/1.0'
                    }
                )
                
                # Reduced timeout for GitHub Actions efficiency
                with urllib.request.urlopen(req, timeout=40) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    if 'candidates' in result and result['candidates']:
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        return content.strip()
                
                if len(self.api_manager.api_keys) > 1:
                    self.api_manager.rotate_key()
                    
            except Exception as e:
                print(f"API request attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return f"Error generating content: {str(e)}"
                if len(self.api_manager.api_keys) > 1:
                    self.api_manager.rotate_key()
                time.sleep(1)  # Faster retry
        
        return "Failed to generate content after multiple attempts"
    
    def load_article_links(self):
        """Load existing article links for internal linking"""
        try:
            if os.path.exists(self.article_links_file):
                with open(self.article_links_file, 'r', encoding='utf-8') as file:
                    self.article_links = json.load(file)
            else:
                self.article_links = {}
        except:
            self.article_links = {}
    
    def save_article_link(self, subject, title, slug, categories):
        """Save article link for future internal linking"""
        link_data = {
            'title': title,
            'slug': slug,
            'categories': categories,
            'keywords': self._extract_keywords_from_subject(subject)
        }
        self.article_links[subject] = link_data
        
        with open(self.article_links_file, 'w', encoding='utf-8') as file:
            json.dump(self.article_links, file, ensure_ascii=False, indent=2)
    
    def _extract_keywords_from_subject(self, subject):
        """Extract keywords from subject for internal linking"""
        keywords = []
        subject_lower = subject.lower()
        
        # Common business keywords for matching
        keyword_patterns = [
            'bisnis', 'marketing', 'strategi', 'keuangan', 'investasi',
            'startup', 'teknologi', 'digital', 'online', 'e-commerce',
            'seo', 'content', 'social media', 'fintech', 'umkm'
        ]
        
        for pattern in keyword_patterns:
            if pattern in subject_lower:
                keywords.append(pattern)
        
        return keywords
    
    def find_related_articles(self, current_subject, current_categories):
        """Find related articles for internal linking"""
        related = []
        current_keywords = self._extract_keywords_from_subject(current_subject)
        
        for subject, data in self.article_links.items():
            if subject == current_subject:
                continue
                
            # Check category match
            category_match = any(cat in current_categories for cat in data['categories'])
            
            # Check keyword match
            keyword_match = any(kw in current_keywords for kw in data['keywords'])
            
            if category_match or keyword_match:
                related.append({
                    'title': data['title'],
                    'slug': data['slug'],
                    'relevance': len(set(current_keywords) & set(data['keywords']))
                })
        
        # Sort by relevance and return top 3
        related.sort(key=lambda x: x['relevance'], reverse=True)
        return related[:3]
    
    def enhance_content_with_formatting(self, content, subject):
        """Enhance content with optimized heading structure, bullet points, and professional formatting"""
        keywords = self._extract_keywords_from_subject(subject)
        main_keyword = subject.split()[0].lower() if subject else ""
        
        lines = content.split('\n')
        enhanced_lines = []
        in_h3_section = False
        bullet_count = 0
        current_h2 = ""
        
        # Professional bullet styles with ASCII symbols
        bullet_styles = [
            "• ", "◦ ", "▪ ", "▫ ", "→ ", "✓ ", "★ ", "▷ ", "‣ ", "⋄ ",
            "► ", "⚬ ", "◆ ", "◇ ", "⬥ ", "⬦ ", "⬧ ", "⬨ ", "○ ", "● "
        ]
        
        # Enhanced punctuation patterns for better readability
        punctuation_fixes = [
            (r'([a-zA-Z])\s*,\s*([a-zA-Z])', r'\1, \2'),  # Proper comma spacing
            (r'([a-zA-Z])\s*\.\s*([A-Z])', r'\1. \2'),     # Proper period spacing
            (r'([a-zA-Z])\s*:\s*([a-zA-Z])', r'\1: \2'),   # Proper colon spacing
            (r'([a-zA-Z])\s*;\s*([a-zA-Z])', r'\1; \2'),   # Proper semicolon spacing
            (r'([a-zA-Z])\s*\!\s*([A-Z])', r'\1! \2'),     # Proper exclamation spacing
            (r'([a-zA-Z])\s*\?\s*([A-Z])', r'\1? \2'),     # Proper question spacing
        ]
        
        for i, line in enumerate(lines):
            enhanced_line = line
            
            # Track heading levels for structure optimization
            if line.startswith('### '):
                in_h3_section = True
                bullet_count = 0
                enhanced_lines.append(enhanced_line)
                continue
            elif line.startswith('## '):
                in_h3_section = False
                current_h2 = line[3:].strip()
                enhanced_lines.append(enhanced_line)
                continue
            elif line.startswith('#'):
                in_h3_section = False
                enhanced_lines.append(enhanced_line)
                continue
            
            # Skip empty lines
            if not line.strip():
                enhanced_lines.append(enhanced_line)
                continue
            
            # Enhanced bullet point formatting for H3 sections
            if in_h3_section and (line.strip().startswith('* ') or line.strip().startswith('- ')):
                # Use varied bullet styles for visual appeal
                bullet_style = bullet_styles[bullet_count % len(bullet_styles)]
                enhanced_line = re.sub(r'^(\s*)[\*\-]\s+', rf'\1{bullet_style}', line)
                bullet_count += 1
                
                # Bold important terms in bullet points
                for keyword in keywords[:2]:
                    if keyword.lower() in enhanced_line.lower():
                        enhanced_line = re.sub(
                            r'\b' + re.escape(keyword) + r'\b',
                            f'**{keyword}**',
                            enhanced_line,
                            count=1,
                            flags=re.IGNORECASE
                        )
                        break
            
            # Convert simple lists to numbered format for step-by-step content
            elif in_h3_section and any(indicator in line.lower() for indicator in ['langkah', 'tahap', 'fase', 'step', 'cara']):
                if line.strip() and not line.startswith(('1.', '2.', '3.')) and len(line.strip()) > 30:
                    if not line.strip().startswith(tuple(bullet_styles)):
                        enhanced_line = f"1. {line.strip()}"
            
            # Professional content enhancement for paragraphs
            elif line.strip() and not line.startswith('#'):
                # Apply punctuation fixes
                for pattern, replacement in punctuation_fixes:
                    enhanced_line = re.sub(pattern, replacement, enhanced_line)
                
                # Bold main keywords naturally
                for keyword in keywords[:3]:
                    if keyword.lower() in enhanced_line.lower() and f"**{keyword}" not in enhanced_line:
                        enhanced_line = re.sub(
                            r'\b' + re.escape(keyword) + r'\b',
                            f'**{keyword}**',
                            enhanced_line,
                            count=1,
                            flags=re.IGNORECASE
                        )
                        break
                
                # Italic for emphasis on important phrases
                emphasis_patterns = [
                    r'\b(sangat penting|crucial|essential|kunci utama|fundamental)\b',
                    r'\b(best practice|tips terbaik|strategi efektif|solusi optimal)\b',
                    r'\b(pertumbuhan bisnis|peningkatan profit|hasil maksimal)\b',
                    r'\b(terbukti efektif|highly recommended|wajib diterapkan)\b'
                ]
                
                for pattern in emphasis_patterns:
                    enhanced_line = re.sub(
                        pattern,
                        r'*\1*',
                        enhanced_line,
                        flags=re.IGNORECASE
                    )
                
                # Ensure proper sentence endings
                if len(enhanced_line.strip()) > 50:
                    if not enhanced_line.strip().endswith(('.', '!', '?', ':', ';')):
                        if enhanced_line.strip().endswith(','):
                            enhanced_line = enhanced_line.rstrip(',') + '.'
                        else:
                            enhanced_line += '.'
                
                # Add transitional phrases for better flow (occasionally)
                if i > 0 and len(enhanced_line) > 60 and random.random() < 0.12:
                    prev_line = lines[i-1].strip() if i > 0 else ""
                    if prev_line and not prev_line.startswith('#') and not enhanced_line.startswith(('Selanjutnya', 'Lebih lanjut', 'Di samping itu')):
                        transitions = [
                            'Selanjutnya', 'Lebih lanjut', 'Di samping itu', 
                            'Berdasarkan hal tersebut', 'Dalam konteks ini',
                            'Sebagai tambahan', 'Yang perlu diperhatikan'
                        ]
                        transition = random.choice(transitions)
                        enhanced_line = f"{transition}, {enhanced_line.lower()}"
            
            enhanced_lines.append(enhanced_line)
        
        return '\n'.join(enhanced_lines)
    
    def add_internal_links(self, content, subject, categories):
        """Add internal links to related articles"""
        related_articles = self.find_related_articles(subject, categories)
        
        if not related_articles:
            return content
        
        # Find a good spot to add internal links (after first H2 section)
        lines = content.split('\n')
        insert_index = -1
        
        h2_count = 0
        for i, line in enumerate(lines):
            if line.startswith('## '):
                h2_count += 1
                if h2_count == 2:  # After first H2 section
                    insert_index = i
                    break
        
        if insert_index == -1:
            return content
        
        # Create internal links section
        links_section = [
            "",
            "### Artikel Terkait yang Mungkin Menarik",
            ""
        ]
        
        for article in related_articles:
            category = categories[0].lower() if categories else 'artikel'
            link_text = f"- [{article['title']}](/{category}/{article['slug']}/)"
            links_section.append(link_text)
        
        links_section.append("")
        
        # Insert links
        lines[insert_index:insert_index] = links_section
        
        return '\n'.join(lines)
    
    def _generate_keyword_variations(self, title):
        """Generate LSI keyword variations for better SEO targeting"""
        # Extract base keywords from title
        words = title.lower().split()
        
        # Common business and tech related LSI terms
        lsi_terms = {
            'business': ['strategy', 'growth', 'success', 'development', 'management'],
            'marketing': ['digital', 'online', 'social media', 'content', 'advertising'],
            'technology': ['innovation', 'digital transformation', 'automation', 'AI', 'software'],
            'finance': ['investment', 'financial planning', 'wealth', 'money management', 'economics'],
            'startup': ['entrepreneurship', 'venture capital', 'scaling', 'innovation', 'funding'],
            'seo': ['search optimization', 'ranking', 'organic traffic', 'keywords', 'SERP'],
            'digital': ['online', 'internet', 'web', 'cloud', 'platform'],
            'guide': ['tutorial', 'handbook', 'manual', 'instructions', 'tips'],
            'strategy': ['planning', 'approach', 'methodology', 'framework', 'tactics']
        }
        
        variations = []
        for word in words:
            if word in lsi_terms:
                variations.extend(lsi_terms[word][:3])  # Take first 3 related terms
        
        # Add some generic high-value terms
        variations.extend(['best practices', 'professional', 'comprehensive guide', 'expert tips'])
        
        return variations[:8]  # Return top 8 variations
    
    def generate_enhanced_article(self, subject):
        """Generate enhanced article with deep content structure and 20+ headings"""
        title = subject.strip()
        domain = self.config.get('domain', 'example.com')
        language = self.config.get('language', 'Indonesian') or 'Indonesian'
        target_headings = self.config.get_int('target_headings', 20)
        min_words = self.config.get_int('min_word_count', 5000)
        max_words = self.config.get_int('max_word_count', 8000)
        
        # Generate keyword variations for better SEO targeting
        keyword_variations = self._generate_keyword_variations(title) if title else []
        related_keywords = self._extract_keywords_from_subject(subject)
        
        if language.lower() == 'english':
            prompt = f"""Write a professional SEO article for: "{title}"

SPECIFICATIONS:
- Length: {min_words}-{max_words} words
- Headings: {target_headings}+ (H2, H3) structured content
- Primary keyword: {title}
- Keywords: {', '.join(keyword_variations[:3])}

STRUCTURE:
# {title}

## Understanding {title}
### Core Concepts and Fundamentals
### Key Benefits and Applications
### Industry Context

## Complete {title} Guide
### Step-by-Step Implementation
### Best Practices and Standards
### Essential Requirements

## Advanced {title} Strategies
### Professional Techniques
### Expert Methods
### Optimization Tips

## Tools and Resources
### Essential Platforms
### Recommended Solutions
### Implementation Tools

## Common Challenges
### Typical Issues and Solutions
### Problem Prevention
### Troubleshooting Guide

## Implementation Results
### Success Metrics
### Case Studies
### ROI Optimization

## Future Outlook
### Emerging Trends
### Technology Impact
### Strategic Planning

## Conclusion
[Key takeaways and action steps]

REQUIREMENTS:
- Each H2: 300-400 words with practical insights
- Each H3: 150-200 words with bullet points
- Use varied symbols (•, ◦, →, ✓) for lists
- **Bold** keywords naturally
- Professional tone with examples
- No repetitive content

Write complete article:"""
        else:
            prompt = f"""Tulis artikel SEO profesional untuk: "{title}"

SPESIFIKASI:
- Panjang: {min_words}-{max_words} kata
- Heading: {target_headings}+ (H2, H3) terstruktur
- Keyword utama: {title}
- Keywords: {', '.join(keyword_variations[:3])}

STRUKTUR:
# {title}

## Memahami {title}
### Konsep Dasar dan Fundamental
### Manfaat Utama dan Aplikasi
### Konteks Industri

## Panduan Lengkap {title}
### Implementasi Step-by-Step
### Best Practices dan Standar
### Persyaratan Penting

## Strategi Advanced {title}
### Teknik Profesional
### Metode Expert
### Tips Optimasi

## Tools dan Resources
### Platform Essential
### Solusi Terpercaya
### Tools Implementasi

## Tantangan Umum
### Masalah Tipikal dan Solusi
### Pencegahan Masalah
### Panduan Troubleshooting

## Implementasi dan Hasil
### Metrik Kesuksesan
### Studi Kasus
### Optimasi ROI

## Outlook Masa Depan
### Tren yang Muncul
### Dampak Teknologi
### Perencanaan Strategis

## Kesimpulan
[Rangkuman dan langkah tindak lanjut]

PERSYARATAN:
- Setiap H2: 300-400 kata dengan insight praktis
- Setiap H3: 150-200 kata dengan bullet points
- Gunakan simbol bervariasi (•, ◦, →, ✓) untuk list
- **Bold** keyword secara natural
- Tone profesional dengan contoh
- Tidak ada konten repetitif

Tulis artikel lengkap:"""
        
        content = self.gemini_request(prompt)
        
        if content.startswith("Error") or content.startswith("Failed"):
            return None
        
        # Enhance content with keyword formatting and natural language improvements
        content = self.enhance_content_with_formatting(content, subject)
        
        # Add strategic image placeholders
        content = self.add_strategic_images(content, subject)
        
        # Generate categories for internal linking
        categories = self.generate_categories(subject)
        
        # Add internal links to related articles
        content = self.add_internal_links(content, subject, categories)
        
        return content
    
    def add_strategic_images(self, content, subject):
        """Add external images without downloading to optimize performance"""
        if not self.config.get_bool('enable_auto_images', True):
            return content
            
        lines = content.split('\n')
        new_lines = []
        image_count = 0
        max_images = self.config.get_int('images_per_article', 2)
        
        # Use external image sources for better performance
        external_image_sources = [
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1560472355-536de3962603?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1497215728101-856f4ea42174?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1553484771-371a605b060b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1551434678-e076c223a692?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1556742393-d75f468bfcb0?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
        ]
        
        # Add images at strategic positions
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            if line.startswith('## ') and image_count < max_images:
                heading = line[3:].strip().lower()
                # Skip conclusion-type headings
                if not any(skip in heading for skip in ['conclusion', 'kesimpulan', 'action', 'outlook']):
                    # Use external image URL
                    image_url = external_image_sources[image_count % len(external_image_sources)]
                    alt_text = f"{subject} - professional guide"
                    
                    new_lines.append('')
                    new_lines.append(f'![{alt_text}]({image_url})')
                    new_lines.append('')
                    image_count += 1
                    print(f"Added external image: {image_url}")
                    
                    # Break early if we have enough images
                    if image_count >= max_images:
                        break
        
        # Add one featured image at the beginning if no images were added
        if image_count == 0:
            featured_image = external_image_sources[0]
            alt_text = f"{subject} - complete guide"
            new_lines.insert(10, '')
            new_lines.insert(11, f'![{alt_text}]({featured_image})')
            new_lines.insert(12, '')
            image_count += 1
            print(f"Added featured image: {featured_image}")
        
        print(f"Total external images added: {image_count}")
        return '\n'.join(new_lines)
    
    def create_markdown_post(self, title, content, subject):
        """Create markdown post with frontmatter"""
        date = datetime.datetime.now()
        slug = slugify(title)[:50]
        filename = f"{date.strftime('%Y-%m-%d')}-{slug}.md"
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        
        # Extract excerpt from content
        lines = content.split('\n')
        excerpt = ""
        for line in lines:
            if line.strip() and not line.startswith('#'):
                excerpt = line.strip()[:150] + "..."
                break
        
        # Generate categories
        categories = self.generate_categories(subject)
        
        # Generate tags
        tags = self.generate_tags(content)
        
        # Enhanced frontmatter
        frontmatter_data = {
            'layout': 'post',
            'title': title,
            'date': date.strftime('%Y-%m-%d %H:%M:%S +0000'),
            'categories': categories,
            'tags': tags,
            'author': self.config.get('author_name', 'Admin'),
            'meta_description': excerpt,
            'permalink': f"/{categories[0].lower()}/{slug}/",
            'toc': True,
            'seo_optimized': True
        }
        
        # Create full post with frontmatter
        post_content = f"""---
{yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)}---

{content}
"""
        
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(post_content)
        
        print(f"✅ Artikel berhasil dibuat: {filename}")
        return filename
    
    def generate_categories(self, subject):
        """Generate categories based on subject"""
        base_categories_str = self.config.get('base_categories', 'Teknologi')
        if base_categories_str:
            base_categories = [cat.strip() for cat in base_categories_str.split(',') if cat.strip()]
        else:
            base_categories = ['Teknologi']
        
        # Simple keyword matching for categories
        subject_lower = subject.lower()
        matched_categories = []
        
        for category in base_categories:
            if any(keyword in subject_lower for keyword in [category.lower()[:3]]):
                matched_categories.append(category.strip())
        
        if not matched_categories:
            matched_categories = [base_categories[0]]
        
        return matched_categories[:2]
    
    def generate_tags(self, content):
        """Generate tags from content"""
        # Simple tag extraction based on common Indonesian business terms
        common_tags = [
            'bisnis', 'teknologi', 'keuangan', 'marketing', 'strategi',
            'tips', 'panduan', 'tutorial', 'analisis', 'tren'
        ]
        
        content_lower = content.lower()
        found_tags = []
        
        for tag in common_tags:
            if tag in content_lower:
                found_tags.append(tag)
        
        return found_tags[:5]
    
    def load_subjects(self):
        """Load subjects from file"""
        if not os.path.exists(SUBJECTS_FILE):
            print(f"File {SUBJECTS_FILE} tidak ditemukan!")
            return []
        
        with open(SUBJECTS_FILE, 'r', encoding='utf-8') as file:
            subjects = [line.strip() for line in file if line.strip()]
        
        return subjects
    
    def load_processed_subjects(self):
        """Load processed subjects"""
        if not os.path.exists(PROCESSED_SUBJECTS_FILE):
            return []
        
        try:
            with open(PROCESSED_SUBJECTS_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except:
            return []
    
    def save_processed_subject(self, subject):
        """Save processed subject"""
        processed = self.load_processed_subjects()
        if subject not in processed:
            processed.append(subject)
            with open(PROCESSED_SUBJECTS_FILE, 'w', encoding='utf-8') as file:
                json.dump(processed, file, ensure_ascii=False, indent=2)
    
    def run_generation(self):
        """Run the enhanced article generation process"""
        print("🚀 Memulai Simple SEO Article Generator...")
        print(f"📝 Target artikel per run: {self.config.get_int('articles_per_run', 2)}")
        print(f"🖼️  Target gambar per artikel: {self.config.get_int('images_per_article', 5)}")
        
        subjects = self.load_subjects()
        if not subjects:
            print("❌ Tidak ada subjects untuk diproses!")
            return
        
        processed_subjects = self.load_processed_subjects()
        unprocessed_subjects = [s for s in subjects if s not in processed_subjects]
        
        if not unprocessed_subjects:
            print("✅ Semua subjects sudah diproses!")
            return
        
        articles_per_run = self.config.get_int('articles_per_run', 2)
        generated_count = 0
        
        for subject in unprocessed_subjects[:articles_per_run]:
            try:
                print(f"\n🔄 Membuat artikel untuk: {subject}")
                
                content = self.generate_enhanced_article(subject)
                if not content:
                    print(f"❌ Gagal membuat artikel untuk: {subject}")
                    continue
                
                # Extract title from content or use subject
                title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else subject
                
                # Generate categories and slug for linking
                categories = self.generate_categories(subject)
                slug = slugify(title)[:50]
                
                # Create markdown post
                filename = self.create_markdown_post(title, content, subject)
                
                # Save article link for future internal linking
                self.save_article_link(subject, title, slug, categories)
                
                # Mark as processed
                self.save_processed_subject(subject)
                
                generated_count += 1
                print(f"✅ Artikel lengkap berhasil dibuat: {filename}")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error memproses subject '{subject}': {str(e)}")
                continue
        
        print(f"\n✅ Proses selesai! Total artikel dibuat: {generated_count}")

def main():
    """Main function"""
    try:
        generator = SimpleSEOGenerator()
        generator.run_generation()
    except KeyboardInterrupt:
        print("\n⏸️  Proses dibatalkan oleh user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()