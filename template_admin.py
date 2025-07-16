#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Template Admin Panel
Panel admin untuk mengelola template Jekyll, AdSense, dan Cloudflare deployment
"""

import streamlit as st
import os
import json
import yaml
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
from github import Github, GithubException
import zipfile
import tempfile
import shutil
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudflareManager:
    """Mengelola operasi Cloudflare API"""
    
    def __init__(self, api_token: str, account_id: str):
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_zones(self) -> List[Dict]:
        """Mendapatkan daftar domain/zones"""
        try:
            response = requests.get(f"{self.base_url}/zones", headers=self.headers)
            if response.status_code == 200:
                return response.json().get('result', [])
            return []
        except Exception as e:
            logger.error(f"Error getting zones: {e}")
            return []
    
    def get_pages_projects(self) -> List[Dict]:
        """Mendapatkan daftar Cloudflare Pages projects"""
        try:
            response = requests.get(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json().get('result', [])
            return []
        except Exception as e:
            logger.error(f"Error getting pages projects: {e}")
            return []
    
    def create_webhook_deploy(self, project_name: str, repo_name: str) -> str:
        """Membuat webhook untuk deploy otomatis"""
        try:
            webhook_data = {
                "name": f"deploy-{project_name}",
                "target": {
                    "type": "github",
                    "repository": repo_name
                },
                "build_config": {
                    "build_command": "bundle install && bundle exec jekyll build",
                    "destination_dir": "_site",
                    "root_dir": "/template/Blog"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects/{project_name}/deployments",
                headers=self.headers,
                json=webhook_data
            )
            
            if response.status_code == 200:
                return response.json().get('result', {}).get('url', '')
            return ""
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            return ""
    
    def trigger_deploy(self, project_name: str) -> bool:
        """Trigger deploy manual"""
        try:
            response = requests.post(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects/{project_name}/deployments",
                headers=self.headers,
                json={"type": "manual"}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error triggering deploy: {e}")
            return False

class JekyllConfigManager:
    """Mengelola konfigurasi Jekyll"""
    
    def __init__(self, config_path: str = "template/Blog/_config.yml"):
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load konfigurasi Jekyll"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {}
    
    def save_config(self):
        """Simpan konfigurasi Jekyll"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def update_site_settings(self, settings: Dict):
        """Update pengaturan site"""
        for key, value in settings.items():
            self.config[key] = value
        return self.save_config()
    
    def update_adsense_settings(self, adsense_config: Dict):
        """Update pengaturan AdSense"""
        self.config['adsense'] = adsense_config
        return self.save_config()
    
    def get_categories(self) -> List[str]:
        """Mendapatkan daftar kategori dari posts"""
        categories = set()
        posts_dir = Path("template/Blog/_posts")
        
        if posts_dir.exists():
            for post_file in posts_dir.glob("*.md"):
                try:
                    with open(post_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract front matter
                        if content.startswith('---'):
                            front_matter = content.split('---')[1]
                            post_data = yaml.safe_load(front_matter)
                            if 'categories' in post_data:
                                if isinstance(post_data['categories'], list):
                                    categories.update(post_data['categories'])
                                else:
                                    categories.add(post_data['categories'])
                except Exception as e:
                    logger.error(f"Error reading post {post_file}: {e}")
        
        return sorted(list(categories))

class AdSenseManager:
    """Mengelola pengaturan AdSense"""
    
    def __init__(self, ads_txt_path: str = "template/Blog/ads.txt"):
        self.ads_txt_path = ads_txt_path
    
    def update_ads_txt(self, publisher_id: str, content: str = None) -> bool:
        """Update ads.txt file"""
        try:
            if content:
                ads_content = content
            else:
                ads_content = f"""# Ads.txt file for {publisher_id}
# Google AdSense
google.com, {publisher_id}, DIRECT, f08c47fec0942fa0

# Additional ad networks can be added here
"""
            
            with open(self.ads_txt_path, 'w', encoding='utf-8') as file:
                file.write(ads_content)
            return True
        except Exception as e:
            logger.error(f"Error updating ads.txt: {e}")
            return False
    
    def create_adsense_widget(self, ad_client: str, ad_slot: str, ad_format: str = "auto") -> str:
        """Membuat kode widget AdSense"""
        return f"""<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ad_client}"
     crossorigin="anonymous"></script>
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{ad_client}"
     data-ad-slot="{ad_slot}"
     data-ad-format="{ad_format}"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({{}});
</script>"""
    
    def update_adsense_include(self, widget_code: str, include_file: str = "template/Blog/_includes/advertisement.html"):
        """Update file include AdSense"""
        try:
            with open(include_file, 'w', encoding='utf-8') as file:
                file.write(widget_code)
            return True
        except Exception as e:
            logger.error(f"Error updating AdSense include: {e}")
            return False

class TemplateDeployManager:
    """Mengelola deployment template ke GitHub"""
    
    def __init__(self, github_token: str):
        self.github = Github(github_token)
    
    def deploy_template_to_github(self, repo_name: str, commit_message: str = "Deploy Jekyll template") -> bool:
        """Deploy template/Blog ke GitHub repository"""
        try:
            repo = self.github.get_repo(repo_name)
            template_path = Path("template/Blog")
            
            # Upload semua file template
            for file_path in template_path.rglob("*"):
                if file_path.is_file() and not self._should_exclude(file_path):
                    relative_path = file_path.relative_to(template_path)
                    github_path = str(relative_path).replace("\\", "/")
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    try:
                        # Cek apakah file sudah ada
                        existing_file = repo.get_contents(github_path)
                        repo.update_file(
                            github_path,
                            f"Update {github_path}",
                            content,
                            existing_file.sha
                        )
                    except GithubException:
                        # File tidak ada, buat baru
                        repo.create_file(
                            github_path,
                            f"Add {github_path}",
                            content
                        )
            
            return True
        except Exception as e:
            logger.error(f"Error deploying template: {e}")
            return False
    
    def _should_exclude(self, file_path: Path) -> bool:
        """Cek apakah file harus dikecualikan"""
        exclude_patterns = [
            ".git", ".jekyll-cache", "_site", ".sass-cache",
            ".DS_Store", "*.tmp", "*.bak", "node_modules"
        ]
        
        for pattern in exclude_patterns:
            if pattern in str(file_path):
                return True
        return False

def render_template_admin():
    """Render admin panel template"""
    st.set_page_config(
        page_title="Template Admin Panel",
        page_icon="⚙️",
        layout="wide"
    )
    
    st.title("⚙️ Template Admin Panel")
    st.markdown("---")
    
    # Sidebar untuk navigasi
    with st.sidebar:
        st.header("🎛️ Panel Navigation")
        admin_section = st.selectbox(
            "Select Section",
            [
                "Jekyll Configuration",
                "AdSense Settings", 
                "Cloudflare Deployment",
                "Navigation & Categories",
                "Template Management"
            ]
        )
    
    # Jekyll Configuration Section
    if admin_section == "Jekyll Configuration":
        st.header("🔧 Jekyll Configuration")
        
        config_manager = JekyllConfigManager()
        
        with st.expander("📝 Site Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                site_title = st.text_input("Site Title", value=config_manager.config.get('title', ''))
                site_description = st.text_area("Site Description", value=config_manager.config.get('description', ''))
                site_url = st.text_input("Site URL", value=config_manager.config.get('url', ''))
                site_email = st.text_input("Email", value=config_manager.config.get('email', ''))
            
            with col2:
                site_author = st.text_input("Author", value=config_manager.config.get('author', ''))
                copyright_year = st.text_input("Copyright", value=config_manager.config.get('copyright_year', ''))
                google_analytics = st.text_input("Google Analytics ID", value=config_manager.config.get('google_analytics', ''))
                disqus_shortname = st.text_input("Disqus Shortname", value=config_manager.config.get('disqus', {}).get('shortname', ''))
            
            if st.button("💾 Save Site Settings"):
                settings = {
                    'title': site_title,
                    'description': site_description,
                    'url': site_url,
                    'email': site_email,
                    'author': site_author,
                    'copyright_year': copyright_year,
                    'google_analytics': google_analytics,
                    'disqus': {'shortname': disqus_shortname}
                }
                
                if config_manager.update_site_settings(settings):
                    st.success("✅ Site settings updated successfully!")
                else:
                    st.error("❌ Failed to update site settings")
    
    # AdSense Settings Section
    elif admin_section == "AdSense Settings":
        st.header("💰 AdSense Settings")
        
        adsense_manager = AdSenseManager()
        
        with st.expander("📄 Ads.txt Configuration", expanded=True):
            publisher_id = st.text_input("Publisher ID", placeholder="pub-XXXXXXXXXXXXXXXX")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Generate ads.txt"):
                    if publisher_id:
                        if adsense_manager.update_ads_txt(publisher_id):
                            st.success("✅ ads.txt updated successfully!")
                        else:
                            st.error("❌ Failed to update ads.txt")
                    else:
                        st.warning("⚠️ Please enter Publisher ID")
            
            with col2:
                # Show current ads.txt content
                try:
                    with open("template/Blog/ads.txt", 'r') as f:
                        current_ads = f.read()
                    st.code(current_ads, language="text")
                except:
                    st.info("📝 No ads.txt file found")
        
        with st.expander("🎯 AdSense Widget Configuration", expanded=True):
            ad_client = st.text_input("Ad Client", placeholder="ca-pub-XXXXXXXXXXXXXXXX")
            ad_slot = st.text_input("Ad Slot", placeholder="XXXXXXXXXX")
            ad_format = st.selectbox("Ad Format", ["auto", "rectangle", "vertical", "horizontal"])
            
            if st.button("💾 Create AdSense Widget"):
                if ad_client and ad_slot:
                    widget_code = adsense_manager.create_adsense_widget(ad_client, ad_slot, ad_format)
                    
                    if adsense_manager.update_adsense_include(widget_code):
                        st.success("✅ AdSense widget created successfully!")
                        st.code(widget_code, language="html")
                    else:
                        st.error("❌ Failed to create AdSense widget")
                else:
                    st.warning("⚠️ Please fill Ad Client and Ad Slot")
    
    # Cloudflare Deployment Section
    elif admin_section == "Cloudflare Deployment":
        st.header("☁️ Cloudflare Deployment")
        
        with st.expander("🔑 Cloudflare API Configuration", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                cf_api_token = st.text_input("Cloudflare API Token", type="password")
                cf_account_id = st.text_input("Account ID", help="Format: 29f3f7e01fc0aa833df7207741a2dd73")
            
            with col2:
                github_token = st.text_input("GitHub Token", type="password")
                target_repo = st.text_input("Target Repository", placeholder="username/repo-name")
            
            if cf_api_token and cf_account_id:
                cf_manager = CloudflareManager(cf_api_token, cf_account_id)
                
                # Show domains
                st.subheader("🌐 Available Domains")
                domains = cf_manager.get_zones()
                if domains:
                    for domain in domains:
                        st.write(f"• {domain['name']} - {domain['status']}")
                
                # Show pages projects
                st.subheader("📄 Cloudflare Pages Projects")
                projects = cf_manager.get_pages_projects()
                if projects:
                    for project in projects:
                        st.write(f"• {project['name']} - {project.get('source', {}).get('type', 'unknown')}")
                
                # Deploy section
                st.subheader("🚀 Deploy Template")
                project_name = st.text_input("Project Name", value="jekyll-blog")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📤 Deploy to GitHub"):
                        if github_token and target_repo:
                            deploy_manager = TemplateDeployManager(github_token)
                            if deploy_manager.deploy_template_to_github(target_repo):
                                st.success("✅ Template deployed to GitHub successfully!")
                            else:
                                st.error("❌ Failed to deploy template to GitHub")
                        else:
                            st.warning("⚠️ Please provide GitHub token and repository")
                
                with col2:
                    if st.button("☁️ Create Pages Project"):
                        if project_name and target_repo:
                            if cf_manager.create_pages_project(project_name, target_repo.split('/')[1]):
                                st.success("✅ Cloudflare Pages project created!")
                            else:
                                st.error("❌ Failed to create Pages project")
                        else:
                            st.warning("⚠️ Please provide project name and repository")
    
    # Navigation & Categories Section
    elif admin_section == "Navigation & Categories":
        st.header("🧭 Navigation & Categories")
        
        config_manager = JekyllConfigManager()
        
        with st.expander("📂 Categories in Navigation", expanded=True):
            st.info("💡 Categories will be automatically generated from existing posts")
            
            # Show current categories
            categories = config_manager.get_categories()
            if categories:
                st.subheader("📋 Available Categories")
                for category in categories:
                    st.write(f"• {category}")
                
                # Update navigation with categories
                if st.button("🔄 Add Categories to Navigation"):
                    # Load current navigation
                    try:
                        with open("template/Blog/_data/navigation.yml", 'r', encoding='utf-8') as f:
                            nav_data = yaml.safe_load(f)
                        
                        # Add categories to main navigation
                        categories_menu = {
                            'title': 'Categories',
                            'url': '/categories/',
                            'submenu': []
                        }
                        
                        for category in categories:
                            categories_menu['submenu'].append({
                                'title': category,
                                'url': f'/categories/{category.lower().replace(" ", "-")}/'
                            })
                        
                        # Add to navigation if not exists
                        nav_data['main'].append(categories_menu)
                        
                        # Save navigation
                        with open("template/Blog/_data/navigation.yml", 'w', encoding='utf-8') as f:
                            yaml.dump(nav_data, f, default_flow_style=False, allow_unicode=True)
                        
                        st.success("✅ Categories added to navigation!")
                    except Exception as e:
                        st.error(f"❌ Error updating navigation: {e}")
            else:
                st.warning("⚠️ No categories found in posts")
    
    # Template Management Section
    elif admin_section == "Template Management":
        st.header("📄 Template Management")
        
        with st.expander("🖼️ Image Settings", expanded=True):
            st.info("💡 Template configured to use external images (no download to assets/images)")
            
            col1, col2 = st.columns(2)
            with col1:
                default_image = st.text_input("Default Image URL", value="https://via.placeholder.com/800x400")
                enable_external_images = st.checkbox("Enable External Images", value=True)
            
            with col2:
                image_lazy_loading = st.checkbox("Enable Lazy Loading", value=True)
                image_optimization = st.checkbox("Enable Image Optimization", value=True)
            
            if st.button("💾 Save Image Settings"):
                config_manager = JekyllConfigManager()
                image_settings = {
                    'default_image': default_image,
                    'external_images': enable_external_images,
                    'performance': {
                        'lazy_loading': image_lazy_loading,
                        'image_optimization': image_optimization
                    }
                }
                
                if config_manager.update_site_settings(image_settings):
                    st.success("✅ Image settings updated successfully!")
                else:
                    st.error("❌ Failed to update image settings")
        
        with st.expander("🎨 Theme Settings", expanded=True):
            st.info("💡 Natural Jekyll template settings")
            
            col1, col2 = st.columns(2)
            with col1:
                posts_per_page = st.number_input("Posts per Page", min_value=1, max_value=50, value=12)
                show_excerpts = st.checkbox("Show Excerpts", value=True)
                enable_comments = st.checkbox("Enable Comments", value=True)
            
            with col2:
                enable_search = st.checkbox("Enable Search", value=True)
                enable_dark_mode = st.checkbox("Enable Dark Mode", value=True)
                enable_social_share = st.checkbox("Enable Social Share", value=True)
            
            if st.button("💾 Save Theme Settings"):
                config_manager = JekyllConfigManager()
                theme_settings = {
                    'paginate': posts_per_page,
                    'show_excerpts': show_excerpts,
                    'defaults': [
                        {
                            'scope': {'path': '', 'type': 'posts'},
                            'values': {
                                'layout': 'post',
                                'comments': enable_comments,
                                'share': enable_social_share
                            }
                        }
                    ]
                }
                
                if config_manager.update_site_settings(theme_settings):
                    st.success("✅ Theme settings updated successfully!")
                else:
                    st.error("❌ Failed to update theme settings")

if __name__ == "__main__":
    render_template_admin()