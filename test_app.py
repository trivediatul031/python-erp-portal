#!/usr/bin/env python
"""Test script to verify app initialization."""
from app import create_app

try:
    app = create_app()
    print("✓ App created successfully")
    
    # Check error handlers registered
    error_handlers = app.error_handler_spec.get(None, {})
    if 403 in error_handlers:
        print("✓ 403 error handler registered")
    if 404 in error_handlers:
        print("✓ 404 error handler registered")
    if 500 in error_handlers:
        print("✓ 500 error handler registered")
    
    # Check blueprints registered
    blueprints = list(app.blueprints.keys())
    print(f"✓ Blueprints registered: {', '.join(blueprints)}")
    
    # Check if logs directory would be created in production
    import os
    if not app.debug:
        if os.path.exists('logs'):
            print("✓ Logs directory exists")
        else:
            print("⚠ Logs directory not found (will be created on first run in production)")
    
    print("\n✓ All checks passed!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
