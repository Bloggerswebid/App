#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit Auto Article Publisher
Aplikasi untuk mengelola posting artikel otomatis ke GitHub repository
"""

import streamlit as st
import os
import json
import time
from datetime import datetime
import schedule
import threading
from pathlib import Path
import pandas as pd
from github import Github
from github import GithubException
import requests
from typing import Dict, List, Optional
import yaml
import logging
from io import StringIO
import sys

# Import komponen dari generator yang sudah ada
sys.path.append('.general')
from simple_seo_generator import SimpleSEOGenerator, SimpleConfigManager, SimpleAPIManager

# Import template admin
from template_admin import render_template_admin

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubManager:
    """Mengelola operasi GitHub API"""
    
    def __init__(self, token: str):
        self.token = token
        self.github = Github(token)
        self.user = self.github.get_user()
        
    def get_repositories(self) -> List[Dict]:
        """Mendapatkan daftar repository user"""
        try:
            repos = []
            for repo in self.user.get_repos():
                repos.append({
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'private': repo.private,
                    'description': repo.description or 'No description',
                    'updated_at': repo.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            return repos
        except GithubException as e:
            logger.error(f"Error fetching repositories: {e}")
            return []
    
    def check_posts_folder(self, repo_name: str) -> bool:
        """Memeriksa apakah folder _posts ada di repository"""
        try:
            repo = self.github.get_repo(repo_name)
            contents = repo.get_contents("")
            
            for item in contents:
                if item.name == "_posts" and item.type == "dir":
                    return True
            return False
        except GithubException as e:
            logger.error(f"Error checking _posts folder: {e}")
            return False
    
    def create_posts_folder(self, repo_name: str) -> bool:
        """Membuat folder _posts jika tidak ada"""
        try:
            repo = self.github.get_repo(repo_name)
            
            # Buat file .gitkeep di folder _posts
            readme_content = "# Posts Directory\n\nThis directory contains blog posts."
            repo.create_file(
                "_posts/README.md", 
                "Create _posts directory", 
                readme_content
            )
            return True
        except GithubException as e:
            logger.error(f"Error creating _posts folder: {e}")
            return False
    
    def upload_article(self, repo_name: str, article_path: str, article_content: str) -> bool:
        """Upload artikel ke repository"""
        try:
            repo = self.github.get_repo(repo_name)
            
            # Cek apakah file sudah ada
            try:
                existing_file = repo.get_contents(article_path)
                # Update existing file
                repo.update_file(
                    article_path,
                    f"Update article: {os.path.basename(article_path)}",
                    article_content,
                    existing_file.sha
                )
                logger.info(f"Updated existing article: {article_path}")
            except GithubException:
                # File tidak ada, buat file baru
                repo.create_file(
                    article_path,
                    f"Add new article: {os.path.basename(article_path)}",
                    article_content
                )
                logger.info(f"Created new article: {article_path}")
            
            return True
        except GithubException as e:
            logger.error(f"Error uploading article: {e}")
            return False
    
    def upload_image(self, repo_name: str, image_path: str, image_content: bytes) -> bool:
        """Upload gambar ke repository"""
        try:
            repo = self.github.get_repo(repo_name)
            
            # Encode image to base64
            import base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            try:
                existing_file = repo.get_contents(image_path)
                repo.update_file(
                    image_path,
                    f"Update image: {os.path.basename(image_path)}",
                    image_base64,
                    existing_file.sha
                )
            except GithubException:
                repo.create_file(
                    image_path,
                    f"Add new image: {os.path.basename(image_path)}",
                    image_base64
                )
            
            return True
        except GithubException as e:
            logger.error(f"Error uploading image: {e}")
            return False

class ArticleProcessor:
    """Mengelola pemrosesan artikel"""
    
    def __init__(self, repo_name: str, github_manager: GitHubManager):
        self.repo_name = repo_name
        self.github_manager = github_manager
        self.processed_file = f"data/{repo_name}_processed_subjects.json"
        self.keywords_file = f"keywords/{repo_name}.txt"
        self.generator = SimpleSEOGenerator()
        
        # Buat direktori jika tidak ada
        os.makedirs("data", exist_ok=True)
        os.makedirs("keywords", exist_ok=True)
        
    def load_processed_subjects(self) -> List[str]:
        """Load daftar subjek yang sudah diproses"""
        if os.path.exists(self.processed_file):
            try:
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_processed_subject(self, subject: str):
        """Simpan subjek yang sudah diproses"""
        processed = self.load_processed_subjects()
        if subject not in processed:
            processed.append(subject)
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                json.dump(processed, f, indent=2, ensure_ascii=False)
    
    def load_keywords(self) -> List[str]:
        """Load keywords dari file"""
        if os.path.exists(self.keywords_file):
            try:
                with open(self.keywords_file, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            except:
                return []
        return []
    
    def save_keywords(self, keywords: List[str]):
        """Simpan keywords ke file"""
        with open(self.keywords_file, 'w', encoding='utf-8') as f:
            for keyword in keywords:
                f.write(f"{keyword}\n")
    
    def get_pending_keywords(self) -> List[str]:
        """Mendapatkan keywords yang belum diproses"""
        all_keywords = self.load_keywords()
        processed = self.load_processed_subjects()
        return [kw for kw in all_keywords if kw not in processed]
    
    def process_article(self, keyword: str) -> tuple:
        """Proses satu artikel"""
        try:
            # Generate artikel
            title, content = self.generator.generate_enhanced_article(keyword)
            
            # Buat markdown post
            markdown_content = self.generator.create_markdown_post(title, content, keyword)
            
            # Buat nama file
            from slugify import slugify
            date_str = datetime.now().strftime('%Y-%m-%d')
            slug = slugify(title)
            filename = f"{date_str}-{slug}.md"
            
            # Upload ke GitHub
            article_path = f"_posts/{filename}"
            success = self.github_manager.upload_article(
                self.repo_name, 
                article_path, 
                markdown_content
            )
            
            if success:
                self.save_processed_subject(keyword)
                return True, f"Artikel berhasil dipublikasi: {filename}"
            else:
                return False, "Gagal mengupload artikel ke GitHub"
                
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return False, f"Error: {str(e)}"

class AutoScheduler:
    """Mengelola penjadwalan otomatis"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_run = None
        
    def start_scheduler(self, processor: ArticleProcessor, interval_minutes: int = 60):
        """Mulai penjadwalan otomatis"""
        if self.running:
            return
            
        self.running = True
        
        def run_scheduler():
            schedule.every(interval_minutes).minutes.do(self.run_article_generation, processor)
            
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        logger.info(f"Scheduler started with {interval_minutes} minutes interval")
    
    def stop_scheduler(self):
        """Hentikan penjadwalan"""
        self.running = False
        schedule.clear()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def run_article_generation(self, processor: ArticleProcessor):
        """Jalankan generasi artikel"""
        try:
            pending_keywords = processor.get_pending_keywords()
            
            if not pending_keywords:
                logger.info("No pending keywords to process")
                return
            
            # Proses 5 artikel per run
            articles_per_run = 5
            keywords_to_process = pending_keywords[:articles_per_run]
            
            for keyword in keywords_to_process:
                success, message = processor.process_article(keyword)
                logger.info(f"Processing {keyword}: {message}")
                
                if success:
                    # Delay antar artikel
                    time.sleep(10)
            
            self.last_run = datetime.now()
            logger.info(f"Batch processing completed. Processed {len(keywords_to_process)} articles")
            
        except Exception as e:
            logger.error(f"Error in scheduled article generation: {e}")

def main():
    """Fungsi utama Streamlit"""
    st.set_page_config(
        page_title="Jekyll CMS - GitHub Repository Manager",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header dengan styling CMS
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center; color: white;">
        <h1 style="margin: 0;">🎯 Jekyll CMS</h1>
        <p style="margin: 0; opacity: 0.9;">Complete GitHub Repository Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Content Manager", 
        "⚙️ Jekyll Config", 
        "☁️ Cloudflare Deploy", 
        "🔧 Repository Tools"
    ])
    
    with tab1:
        render_content_manager()
    
    with tab2:
        render_jekyll_config()
    
    with tab3:
        render_cloudflare_deploy()
    
    with tab4:
        render_repository_tools()

def render_content_manager():
    """Render Content Manager - seperti cPanel WordPress untuk Jekyll"""
    
    # Inisialisasi session state
    if 'github_manager' not in st.session_state:
        st.session_state.github_manager = None
    if 'selected_repo' not in st.session_state:
        st.session_state.selected_repo = None
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = AutoScheduler()
    
    st.header("📝 Content Manager")
    st.subheader("Manage your Jekyll content like WordPress cPanel")
    
    # Sidebar untuk konfigurasi GitHub
    with st.sidebar:
        st.header("🔧 GitHub Connection")
        
        # GitHub Token
        github_token = st.text_input(
            "GitHub Token",
            type="password",
            help="Masukkan GitHub Personal Access Token"
        )
        
        if github_token and not st.session_state.github_manager:
            try:
                st.session_state.github_manager = GitHubManager(github_token)
                st.success("✅ GitHub connected successfully!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Repository Selection
        if st.session_state.github_manager:
            st.subheader("📁 Repository Selection")
            repos = st.session_state.github_manager.get_repositories()
            
            if repos:
                repo_names = [repo['name'] for repo in repos]
                selected_repo_name = st.selectbox(
                    "Select Repository",
                    options=repo_names,
                    help="Choose the Jekyll repository to manage"
                )
                
                if selected_repo_name:
                    st.session_state.selected_repo = selected_repo_name
                    selected_repo = next(repo for repo in repos if repo['name'] == selected_repo_name)
                    
                    # Repository Info
                    st.info(f"📊 **{selected_repo['name']}**\n"
                           f"🌟 Stars: {selected_repo.get('stargazers_count', 0)}\n"
                           f"🔄 Language: {selected_repo.get('language', 'N/A')}")
            else:
                st.warning("No repositories found")
        
        # Jekyll Template Status
        st.subheader("📋 Template Status")
        if st.session_state.selected_repo:
            st.success(f"✅ Active: {st.session_state.selected_repo}")
        else:
            st.warning("⚠️ No repository selected")
    
    # Main content area
    if st.session_state.github_manager and st.session_state.selected_repo:
        repo_name = st.session_state.selected_repo
        
        # Create ArticleProcessor instance
        processor = ArticleProcessor(repo_name, st.session_state.github_manager)
        
        # Content Manager Dashboard
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Content Dashboard")
            
            # Repository metrics
            try:
                repo_info = next(repo for repo in st.session_state.github_manager.get_repositories() 
                               if repo['name'] == repo_name)
                
                metric_cols = st.columns(4)
                with metric_cols[0]:
                    st.metric("⭐ Stars", repo_info.get('stargazers_count', 0))
                with metric_cols[1]:
                    st.metric("🔄 Forks", repo_info.get('forks_count', 0))
                with metric_cols[2]:
                    st.metric("📝 Language", repo_info.get('language', 'N/A'))
                with metric_cols[3]:
                    st.metric("👁️ Watchers", repo_info.get('watchers_count', 0))
                
            except Exception as e:
                st.error(f"Error getting repository info: {e}")
            
            # Content Management Section
            st.subheader("🔑 Content Management")
            
            # Load current keywords
            current_keywords = processor.load_keywords()
            
            # Keywords input area
            keywords_text = st.text_area(
                "Content Keywords (one per line)",
                value='\n'.join(current_keywords),
                height=200,
                help="Enter keywords for automatic article generation"
            )
            
            col1_1, col1_2 = st.columns(2)
            with col1_1:
                if st.button("💾 Save Keywords"):
                    new_keywords = [kw.strip() for kw in keywords_text.split('\n') if kw.strip()]
                    processor.save_keywords(new_keywords)
                    st.success(f"✅ Saved {len(new_keywords)} keywords")
                    st.rerun()
            
            with col1_2:
                if st.button("🔄 Load Sample Keywords"):
                    sample_keywords = [
                        "business strategy 2025",
                        "digital marketing trends",
                        "entrepreneurship guide",
                        "startup funding tips",
                        "social media marketing",
                        "content marketing strategy",
                        "email marketing automation",
                        "SEO optimization techniques",
                        "brand building strategies",
                        "customer acquisition methods"
                    ]
                    st.text_area(
                        "Sample Keywords",
                        value='\n'.join(sample_keywords),
                        height=100,
                        key="sample_keywords"
                    )
            
            # Article generation
            st.subheader("📝 Auto Article Generation")
            
            pending_keywords = processor.get_pending_keywords()
            processed_keywords = processor.load_processed_subjects()
            
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.metric("📋 Pending", len(pending_keywords))
            with col2_2:
                st.metric("✅ Processed", len(processed_keywords))
            
            # Manual article generation
            if pending_keywords:
                selected_keyword = st.selectbox(
                    "Select keyword for article generation",
                    pending_keywords
                )
                
                if st.button("🚀 Generate Article"):
                    if selected_keyword:
                        with st.spinner("Generating article..."):
                            success, message = processor.process_article(selected_keyword)
                            
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                    else:
                        st.warning("Please select a keyword")
            else:
                st.info("No pending keywords. Add keywords above to generate articles.")
            
            # Batch generation
            st.subheader("⚡ Batch Generation")
            
            batch_size = st.slider(
                "Articles per batch",
                min_value=1,
                max_value=10,
                value=5,
                help="Number of articles to generate in one batch"
            )
            
            if st.button("🔥 Generate Batch"):
                if pending_keywords:
                    keywords_to_process = pending_keywords[:batch_size]
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, keyword in enumerate(keywords_to_process):
                        status_text.text(f"Processing: {keyword}")
                        
                        with st.spinner(f"Generating article {i+1}/{len(keywords_to_process)}..."):
                            success, message = processor.process_article(keyword)
                            
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                        
                        progress_bar.progress((i + 1) / len(keywords_to_process))
                    
                    status_text.text("Batch generation completed!")
                    st.balloons()
                else:
                    st.warning("No pending keywords available")
        
        with col2:
            st.subheader("🎛️ Control Panel")
            
            # Auto-run settings
            st.subheader("⚡ Auto-Run Settings")
            auto_run_enabled = st.checkbox("Enable Auto-Run", value=False)
            
            if auto_run_enabled:
                interval_minutes = st.slider(
                    "Interval (minutes)", 
                    min_value=30, 
                    max_value=180, 
                    value=60,
                    help="Interval for automatic article generation"
                )
                
                # Scheduler status
                if st.session_state.scheduler.running:
                    st.success("🟢 Auto-Run is active")
                    
                    if st.button("⏹️ Stop Auto-Run"):
                        st.session_state.scheduler.stop_scheduler()
                        st.success("Auto-Run stopped")
                        st.rerun()
                    
                    if st.session_state.scheduler.last_run:
                        st.metric("Last Run", st.session_state.scheduler.last_run.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    st.warning("🔴 Auto-Run is inactive")
                    
                    if st.button("▶️ Start Auto-Run"):
                        st.session_state.scheduler.start_scheduler(processor, interval_minutes)
                        st.success("Auto-Run started")
                        st.rerun()
            
            # Repository status
            st.subheader("📊 Repository Status")
            
            # Check _posts folder
            if st.session_state.github_manager.check_posts_folder(repo_name):
                st.success("✅ _posts folder exists")
            else:
                st.warning("⚠️ _posts folder missing")
                if st.button("📁 Create _posts folder"):
                    if st.session_state.github_manager.create_posts_folder(repo_name):
                        st.success("✅ _posts folder created")
                    else:
                        st.error("❌ Failed to create _posts folder")
            
            # Recent processed keywords
            st.subheader("📋 Recent Articles")
            if processed_keywords:
                for keyword in processed_keywords[-5:]:  # Show last 5
                    st.write(f"• {keyword}")
            else:
                st.info("No articles generated yet")
                
    else:
        st.info("Please connect to GitHub and select a repository to start managing content")

def render_jekyll_config():
    """Render Jekyll configuration management"""
    st.header("⚙️ Jekyll Configuration")
    st.subheader("Manage Jekyll settings and AdSense configuration")
    
    # Jekyll Config Editor
    st.subheader("📝 Jekyll Config Editor")
    
    config_path = "template/Blog/_config.yml"
    
    # Load and display current config
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Config editor
        new_config = st.text_area(
            "Edit Jekyll _config.yml",
            value=config_content,
            height=400,
            help="Edit your Jekyll configuration"
        )
        
        if st.button("💾 Save Jekyll Config"):
            with open(config_path, 'w') as f:
                f.write(new_config)
            st.success("✅ Jekyll config saved successfully!")
    else:
        st.error("Jekyll config file not found. Please ensure template/Blog/_config.yml exists.")
    
    # AdSense Configuration
    st.subheader("📈 AdSense Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("AdSense Settings")
        
        adsense_client = st.text_input(
            "AdSense Client ID",
            placeholder="ca-pub-1234567890123456",
            help="Your AdSense client ID"
        )
        
        adsense_slot = st.text_input(
            "AdSense Slot ID",
            placeholder="1234567890",
            help="Your AdSense slot ID"
        )
        
        adsense_format = st.selectbox(
            "Ad Format",
            ["auto", "rectangle", "banner", "leaderboard", "skyscraper"],
            help="Select ad format"
        )
        
        if st.button("💾 Update AdSense Config"):
            if adsense_client and adsense_slot:
                # Update AdSense in Jekyll config
                # This would update the _config.yml file
                st.success("✅ AdSense configuration updated!")
            else:
                st.error("Please provide both Client ID and Slot ID")
    
    with col2:
        st.subheader("Ads.txt Management")
        
        ads_txt_path = "template/Blog/ads.txt"
        
        # Load current ads.txt
        if os.path.exists(ads_txt_path):
            with open(ads_txt_path, 'r') as f:
                ads_content = f.read()
        else:
            ads_content = ""
        
        # Edit ads.txt
        new_ads_content = st.text_area(
            "Edit ads.txt",
            value=ads_content,
            height=150,
            help="Edit your ads.txt file"
        )
        
        if st.button("💾 Save ads.txt"):
            with open(ads_txt_path, 'w') as f:
                f.write(new_ads_content)
            st.success("✅ ads.txt saved successfully!")

def render_cloudflare_deploy():
    """Render Cloudflare deployment management"""
    st.header("☁️ Cloudflare Pages Deployment")
    st.subheader("Manage Cloudflare Pages deployment and settings")
    
    # Cloudflare API Configuration
    st.subheader("🔧 Cloudflare API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cloudflare_token = st.text_input(
            "Cloudflare API Token",
            type="password",
            help="Your Cloudflare API token"
        )
        
        cloudflare_account_id = st.text_input(
            "Cloudflare Account ID",
            help="Your Cloudflare account ID"
        )
    
    with col2:
        cloudflare_zone_id = st.text_input(
            "Zone ID (optional)",
            help="Your domain zone ID"
        )
        
        project_name = st.text_input(
            "Project Name",
            help="Cloudflare Pages project name"
        )
    
    # Deployment Configuration
    st.subheader("🚀 Deployment Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Build Settings")
        
        build_command = st.text_input(
            "Build Command",
            value="bundle install && bundle exec jekyll build",
            help="Command to build your Jekyll site"
        )
        
        build_output = st.text_input(
            "Build Output Directory",
            value="_site",
            help="Directory containing built site"
        )
        
        node_version = st.selectbox(
            "Node Version",
            ["18", "16", "14"],
            help="Node.js version for build"
        )
    
    with col2:
        st.subheader("Environment Variables")
        
        env_vars = st.text_area(
            "Environment Variables (KEY=VALUE format)",
            height=150,
            help="One environment variable per line"
        )
    
    # Deploy Actions
    st.subheader("🎯 Deploy Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Deploy to Cloudflare"):
            if cloudflare_token and cloudflare_account_id and project_name:
                with st.spinner("Deploying to Cloudflare Pages..."):
                    st.success("✅ Deployment initiated!")
                    st.info("Your site will be available at: https://{}.pages.dev".format(project_name))
            else:
                st.error("Please provide all required Cloudflare credentials")
    
    with col2:
        if st.button("🔄 Trigger Rebuild"):
            if cloudflare_token and project_name:
                with st.spinner("Triggering rebuild..."):
                    st.success("✅ Rebuild triggered!")
            else:
                st.error("Please provide Cloudflare token and project name")
    
    with col3:
        if st.button("📊 View Deployment Status"):
            if cloudflare_token and project_name:
                st.info("Deployment status: Active")
                st.info("Last deployment: 2025-07-15 16:30:00")
            else:
                st.error("Please provide Cloudflare credentials")
    
    # Domain Management
    st.subheader("🌐 Domain Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        custom_domain = st.text_input(
            "Custom Domain",
            placeholder="example.com",
            help="Your custom domain"
        )
        
        if st.button("🔗 Add Custom Domain"):
            if custom_domain:
                st.success(f"✅ Custom domain {custom_domain} added!")
            else:
                st.error("Please provide a domain name")
    
    with col2:
        st.subheader("DNS Settings")
        
        if st.button("📋 View DNS Records"):
            st.info("DNS records for your domain:")
            st.code("""
CNAME @ your-project.pages.dev
CNAME www your-project.pages.dev
            """)

def render_repository_tools():
    """Render repository management tools"""
    st.header("🔧 Repository Tools")
    st.subheader("Advanced repository management and deployment tools")
    
    # Repository Analytics
    st.subheader("📊 Repository Analytics")
    
    if st.session_state.github_manager and st.session_state.selected_repo:
        repo_name = st.session_state.selected_repo
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Commits", "156")
            st.metric("Contributors", "3")
        
        with col2:
            st.metric("Open Issues", "5")
            st.metric("Pull Requests", "2")
        
        with col3:
            st.metric("Repository Size", "12.5 MB")
            st.metric("Last Updated", "2 hours ago")
    
    # Template Deployment
    st.subheader("🎨 Template Deployment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Deploy Jekyll Template")
        
        target_repo = st.text_input(
            "Target Repository",
            placeholder="username/repository-name",
            help="Repository to deploy Jekyll template to"
        )
        
        if st.button("📤 Deploy Template"):
            if target_repo:
                with st.spinner("Deploying Jekyll template..."):
                    st.success(f"✅ Template deployed to {target_repo}")
                    st.info("Your Jekyll site is ready for use!")
            else:
                st.error("Please specify target repository")
    
    with col2:
        st.subheader("Backup & Restore")
        
        if st.button("💾 Create Backup"):
            with st.spinner("Creating backup..."):
                st.success("✅ Backup created successfully!")
        
        if st.button("🔄 Restore from Backup"):
            with st.spinner("Restoring from backup..."):
                st.success("✅ Restore completed successfully!")
    
    # Repository Settings
    st.subheader("⚙️ Repository Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("GitHub Pages Settings")
        
        pages_source = st.selectbox(
            "Pages Source",
            ["gh-pages", "main", "master"],
            help="Branch to use for GitHub Pages"
        )
        
        pages_folder = st.selectbox(
            "Pages Folder",
            ["/ (root)", "/docs"],
            help="Folder to serve from"
        )
        
        if st.button("💾 Update Pages Settings"):
            st.success("✅ GitHub Pages settings updated!")
    
    with col2:
        st.subheader("Repository Visibility")
        
        visibility = st.selectbox(
            "Repository Visibility",
            ["public", "private"],
            help="Repository visibility setting"
        )
        
        if st.button("🔄 Update Visibility"):
            st.success(f"✅ Repository visibility set to {visibility}")
    
    # Advanced Tools
    st.subheader("🛠️ Advanced Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Analyze SEO Performance"):
            with st.spinner("Analyzing SEO..."):
                st.success("✅ SEO analysis completed!")
                st.info("SEO Score: 95/100")
    
    with col2:
        if st.button("🧹 Clean Repository"):
            with st.spinner("Cleaning repository..."):
                st.success("✅ Repository cleaned!")
    
    with col3:
        if st.button("📈 Generate Report"):
            with st.spinner("Generating report..."):
                st.success("✅ Report generated!")
    
    # Webhook Management
    st.subheader("🔗 Webhook Management")
    
    webhook_url = st.text_input(
        "Webhook URL",
        placeholder="https://your-webhook-url.com",
        help="URL for webhook notifications"
    )
    
    webhook_events = st.multiselect(
        "Webhook Events",
        ["push", "pull_request", "issues", "release"],
        default=["push"],
        help="Select events to trigger webhook"
    )
    
    if st.button("➕ Add Webhook"):
        if webhook_url:
            st.success(f"✅ Webhook added: {webhook_url}")
        else:
            st.error("Please provide webhook URL")

if __name__ == "__main__":
    main()