# Auto Article Publisher

## Overview

This repository contains a Streamlit-based auto article publisher that connects to GitHub repositories to automatically generate and publish SEO-optimized articles. The system features a crown-themed interface and provides continuous automated article generation with customizable scheduling.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture
- **Language**: Python 3.x
- **Frontend**: Streamlit web application with crown theme
- **Execution Model**: Continuous background processing with GitHub API integration
- **File Structure**: Repository-specific configuration and state management
- **Content Generation**: Keyword-based article generation with SEO optimization

### Key Design Decisions
- **Repository-Specific Processing**: Uses JSON files per repository for state persistence
- **Batch Processing**: Configurable articles per run with continuous automated scheduling
- **GitHub API Integration**: Direct repository access for seamless article publishing
- **Streamlit Interface**: User-friendly web dashboard with crown theme

## Key Components

### 1. Streamlit Web Application (`app.py`)
- Crown-themed user interface with professional dashboard
- GitHub repository selection and management
- Real-time article generation monitoring
- Automated scheduling with configurable intervals

### 2. GitHub Integration (`GitHubManager`)
- Personal Access Token authentication
- Repository discovery and validation
- Direct article publishing to `_posts` folder
- Image asset management and upload

### 3. Article Processing (`ArticleProcessor`)
- Repository-specific keyword management
- Per-repository processing state tracking
- Batch article generation with progress monitoring
- Automated content publishing pipeline

### 4. Auto Scheduler (`AutoScheduler`)
- Continuous background processing
- Configurable trigger intervals (5x articles per run)
- Thread-based implementation for non-blocking operation
- Comprehensive logging and monitoring

### 5. State Management (Per Repository)
- **Progress Tracking**: `data/{repo_name}_processed_subjects.json`
- **Keywords**: `keywords/{repo_name}.txt`
- **Repository-Specific Configuration**: Automatic adaptation based on repo name
- **Duplicate Prevention**: Per-repository processing state

## Data Flow

1. **GitHub Authentication**: User provides Personal Access Token via Streamlit interface
2. **Repository Selection**: User selects target repository from dashboard grid
3. **Keyword Management**: Load/edit keywords from `keywords/{repo_name}.txt`
4. **Automated Processing**: Background scheduler triggers article generation every 60 minutes
5. **Batch Generation**: Process 5 articles per run with progress tracking
6. **Content Publishing**: Direct upload to repository's `_posts` folder via GitHub API
7. **State Management**: Update `data/{repo_name}_processed_subjects.json` automatically

## External Dependencies

### Python Libraries
- `requests`: HTTP requests for API calls and image downloads
- `urllib3`: URL handling and web requests
- `python-slugify`: URL-safe slug generation
- `langdetect`: Language detection for content
- `pyyaml`: YAML processing for Jekyll front matter

### External Services
- **Google APIs**: Multiple API keys provided for image search and content services
- **Image Sources**: Web-based image search and download

## Deployment Strategy

### Streamlit Application Deployment
- **Replit Platform**: Optimized for Replit's cloud environment
- **Continuous Running**: Background scheduler for automated processing
- **Crown Theme**: Professional UI with intuitive dashboard layout
- **Port Configuration**: Serves on port 5000 for Replit compatibility

### GitHub Integration
- **Direct API Access**: Real-time repository interaction
- **Multi-Repository Support**: Manage multiple Jekyll sites from single interface
- **Automated Folder Creation**: Automatically creates `_posts` directory if missing
- **Image Asset Management**: Direct upload to repository's `assets/image/` folder

### Configuration Management
- **Repository-Specific Settings**: Automatic adaptation based on selected repository
- **Web-Based Configuration**: All settings managed through Streamlit interface
- **Scalable Processing**: Adjustable batch sizes and scheduling intervals

## Technical Considerations

### Performance Optimization
- **Repository-Specific Processing**: Only processes unprocessed keywords per repository
- **Configurable Limits**: Adjustable word counts and image limits through web interface
- **Efficient State Management**: JSON-based state tracking per repository
- **Background Processing**: Non-blocking automated article generation

### Recent Changes (July 15, 2025)
- **Complete Transformation**: Converted command-line SEO generator to Streamlit web application
- **GitHub Integration**: Added direct API integration for repository management
- **Crown Theme**: Implemented professional crown-themed interface
- **Automated Scheduler**: Added continuous background processing with 5x article generation
- **Repository-Specific Structure**: Implemented data/{repo_name}_processed_subjects.json and keywords/{repo_name}.txt pattern
- **Template Admin Panel**: Added comprehensive Jekyll template management system
- **Cloudflare Integration**: Implemented deployment pipeline to Cloudflare Pages
- **AdSense Configuration**: Added dynamic AdSense widget management
- **External Images**: Optimized for external image usage instead of local downloads
- **Categories Navigation**: Added automatic category detection and navigation integration

### SEO Features
- **Internal Linking**: Automatic internal link generation
- **Meta Optimization**: Configurable meta descriptions and SEO tags
- **Content Structure**: Optimized heading hierarchy (H2, H3)
- **Image SEO**: Alt text and proper image integration

### Extensibility
- **Plugin Architecture**: Modular design allows easy feature additions
- **Configuration Driven**: Most features controllable via configuration
- **API Integration**: Multiple API keys for service redundancy