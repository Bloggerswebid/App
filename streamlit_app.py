#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit Auto Article Publisher
Entry point for deployment
"""

import streamlit as st
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run main app
try:
    from app import main
    main()
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please check if all dependencies are installed correctly.")
except Exception as e:
    st.error(f"Application error: {e}")
    st.error("Please contact support if this issue persists.")