#!/usr/bin/env python
"""
Visual verification script for dashboard layout fixes.
Tests the dashboard at multiple viewport widths to ensure content is not cut off.
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def verify_dashboard_layout():
    """Verify dashboard layout at multiple resolutions."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--force-device-scale-factor=1')  # 100% zoom
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Test widths as specified in the plan
        test_widths = [1920, 1366, 1024, 768]
        base_url = 'http://localhost:5000'
        
        print("=" * 80)
        print("DASHBOARD LAYOUT VERIFICATION REPORT")
        print("=" * 80)
        print(f"Testing at 100% zoom (scale factor = 1.0)")
        print(f"Server URL: {base_url}")
        print()
        
        # Login first
        driver.get(f'{base_url}/login')
        time.sleep(2)
        
        # Fill login form (admin/admin123 per README)
        username_field = driver.find_element(By.NAME, 'username')
        password_field = driver.find_element(By.NAME, 'password')
        username_field.send_keys('admin')
        password_field.send_keys('admin123')
        
        # Submit form
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        time.sleep(2)
        
        # Should be redirected to admin dashboard
        current_url = driver.current_url
        print(f"After login, current URL: {current_url}")
        
        if 'admin' not in current_url:
            print("ERROR: Not redirected to admin dashboard after login!")
            return False
        
        print(f"✓ Successfully logged in and redirected to: {current_url}")
        print()
        
        # Test at each width
        for width in test_widths:
            height = 1080  # Standard height
            driver.set_window_size(width, height)
            time.sleep(1)  # Let layout stabilize
            
            print(f"\n{'='*80}")
            print(f"Testing at {width}x{height}px (100% zoom)")
            print(f"{'='*80}")
            
            # Get body scroll dimensions
            body_scroll_width = driver.execute_script("return document.body.scrollWidth;")
            body_client_width = driver.execute_script("return document.body.clientWidth;")
            viewport_width = driver.execute_script("return window.innerWidth;")
            
            print(f"Viewport width: {viewport_width}px")
            print(f"Body client width: {body_client_width}px")
            print(f"Body scroll width: {body_scroll_width}px")
            
            # Check for horizontal scrollbar
            has_horizontal_scroll = body_scroll_width > body_client_width
            if has_horizontal_scroll:
                print(f"✗ FAIL: Horizontal scrollbar detected ({body_scroll_width}px > {body_client_width}px)")
                overflow_amount = body_scroll_width - body_client_width
                print(f"  Content overflows by: {overflow_amount}px")
            else:
                print(f"✓ PASS: No horizontal scrollbar")
            
            # Check sidebar dimensions if on desktop
            if width > 768:
                try:
                    sidebar = driver.find_element(By.ID, 'sidebar')
                    sidebar_width = sidebar.size['width']
                    sidebar_left = driver.execute_script("return arguments[0].getBoundingClientRect().left;", sidebar)
                    print(f"\nSidebar:")
                    print(f"  Width: {sidebar_width}px (expected: 280px)")
                    print(f"  Left position: {sidebar_left}px (expected: 0px)")
                    
                    if abs(sidebar_width - 280) > 5:  # Allow 5px tolerance
                        print(f"  ✗ FAIL: Sidebar width incorrect")
                    else:
                        print(f"  ✓ PASS: Sidebar width correct")
                except Exception as e:
                    print(f"  WARNING: Could not measure sidebar: {e}")
            
            # Check main content positioning
            try:
                main_content = driver.find_element(By.CSS_SELECTOR, '.main-content, .col-md-9, .col-lg-10')
                content_left = driver.execute_script("return arguments[0].getBoundingClientRect().left;", main_content)
                content_width = main_content.size['width']
                
                print(f"\nMain content:")
                print(f"  Left position: {content_left}px")
                
                if width > 768:
                    # On desktop, content should start after sidebar (280px) or close to it
                    expected_left = 280
                    if abs(content_left - expected_left) > 10:  # Allow 10px tolerance
                        print(f"  ✗ FAIL: Content left position incorrect (expected ~{expected_left}px)")
                    else:
                        print(f"  ✓ PASS: Content positioned after sidebar")
                else:
                    # On mobile, content should start at 0px
                    if content_left > 10:
                        print(f"  ✗ FAIL: Content should start at 0px on mobile")
                    else:
                        print(f"  ✓ PASS: Content full-width on mobile")
                
                print(f"  Width: {content_width}px")
            except Exception as e:
                print(f"  WARNING: Could not measure main content: {e}")
            
            # Check page header
            try:
                page_header = driver.find_element(By.CSS_SELECTOR, '.page-header, .page-header-modern, h1.h2')
                header_left = driver.execute_script("return arguments[0].getBoundingClientRect().left;", page_header)
                header_width = page_header.size['width']
                header_text = page_header.text[:50]  # First 50 chars
                
                print(f"\nPage header:")
                print(f"  Text: '{header_text}'")
                print(f"  Left position: {header_left}px")
                print(f"  Width: {header_width}px")
                
                # Check if header is fully visible (not cut off left)
                if header_left < 0:
                    print(f"  ✗ FAIL: Header cut off on left side ({header_left}px < 0)")
                elif width > 768 and header_left < 300:  # On desktop, should be within content area
                    print(f"  ✗ WARNING: Header may be too close to sidebar edge")
                else:
                    print(f"  ✓ PASS: Header fully visible")
            except Exception as e:
                print(f"  WARNING: Could not measure page header: {e}")
            
            # Check for stat cards
            try:
                stat_cards = driver.find_elements(By.CSS_SELECTOR, '.stat-card, .stats-grid > div, .card')
                if stat_cards:
                    first_card = stat_cards[0]
                    card_left = driver.execute_script("return arguments[0].getBoundingClientRect().left;", first_card)
                    
                    print(f"\nStat cards:")
                    print(f"  Count: {len(stat_cards)}")
                    print(f"  First card left position: {card_left}px")
                    
                    if card_left < 0:
                        print(f"  ✗ FAIL: First card cut off on left side")
                    elif width > 768 and card_left < 300:
                        print(f"  ✗ WARNING: Card may be too close to sidebar edge")
                    else:
                        print(f"  ✓ PASS: Cards positioned correctly")
            except Exception as e:
                print(f"  WARNING: Could not measure stat cards: {e}")
        
        print(f"\n{'='*80}")
        print("VERIFICATION COMPLETE")
        print(f"{'='*80}")
        
        return True
        
    except Exception as e:
        print(f"ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        driver.quit()

if __name__ == '__main__':
    success = verify_dashboard_layout()
    exit(0 if success else 1)
