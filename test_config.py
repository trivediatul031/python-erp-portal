#!/usr/bin/env python3
"""Test Azure configuration"""
import os
os.environ['FLASK_ENV'] = 'development'

from app import create_app

app = create_app()
print(f"AZURE_REDIRECT_URI: {app.config.get('AZURE_REDIRECT_URI')}")
print(f"APP_URL: {app.config.get('APP_URL')}")
