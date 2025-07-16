#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit Auto Article Publisher
Entry point for deployment - redirects to main app.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run main app
from app import main

if __name__ == "__main__":
    main()