#!/usr/bin/env python3
"""Capture specific screenshots for FastVimes UI walkthrough documentation."""

import asyncio
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright


async def capture_walkthrough_screenshots():
    """Capture detailed screenshots for UI walkthrough."""
    
    # Ensure directories exist
    screenshot_dir = Path("docs/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Start FastVimes server
    print("Starting FastVimes server for walkthrough screenshots...")
    server_process = subprocess.Popen(
        ["uv", "run", "fastvimes", "serve", "--port", "8004"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to start
    time.sleep(4)
    
    try:
        # Launch browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        screenshots = []
        
        # 1. Homepage/Welcome screen
        print("📸 Capturing homepage...")
        await page.goto("http://localhost:8004")
        await page.wait_for_timeout(3000)
        homepage_path = screenshot_dir / "01-homepage.png"
        await page.screenshot(path=homepage_path)
        screenshots.append(("Homepage Welcome", homepage_path))
        
        # 2. Navigation sidebar (if present)
        print("📸 Capturing navigation...")
        # Try to interact with navigation if present
        try:
            # Look for common navigation elements
            nav_elements = await page.query_selector_all("nav, .sidebar, .navigation, .drawer")
            if nav_elements:
                await page.screenshot(path=screenshot_dir / "02-navigation.png")
                screenshots.append(("Navigation Sidebar", screenshot_dir / "02-navigation.png"))
        except:
            pass
        
        # 3. Table listing page
        print("📸 Capturing table list...")
        try:
            await page.goto("http://localhost:8004/tables")
            await page.wait_for_timeout(2000)
        except:
            # Fallback to root if /tables doesn't exist
            await page.goto("http://localhost:8004")
            await page.wait_for_timeout(2000)
        
        table_list_path = screenshot_dir / "03-table-list.png"
        await page.screenshot(path=table_list_path)
        screenshots.append(("Table List", table_list_path))
        
        # 4. Users table data view
        print("📸 Capturing users table...")
        await page.goto("http://localhost:8004/table/users")
        await page.wait_for_timeout(4000)  # Wait for data to load
        users_table_path = screenshot_dir / "04-users-table.png"
        await page.screenshot(path=users_table_path)
        screenshots.append(("Users Table Data", users_table_path))
        
        # 5. Table with data grid/filtering
        print("📸 Capturing data grid features...")
        # Look for filter or sort elements
        try:
            filter_elements = await page.query_selector_all("input[type='text'], .filter, .search")
            if filter_elements:
                # Try to interact with first filter
                await filter_elements[0].click()
                await page.wait_for_timeout(1000)
                await page.screenshot(path=screenshot_dir / "05-table-filtering.png")
                screenshots.append(("Table Filtering", screenshot_dir / "05-table-filtering.png"))
        except:
            # Fallback to regular table view
            await page.screenshot(path=screenshot_dir / "05-table-features.png")
            screenshots.append(("Table Features", screenshot_dir / "05-table-features.png"))
        
        # 6. Add/Create form
        print("📸 Capturing add record form...")
        await page.goto("http://localhost:8004/form/users")
        await page.wait_for_timeout(2000)
        form_path = screenshot_dir / "06-add-form.png"
        await page.screenshot(path=form_path)
        screenshots.append(("Add Record Form", form_path))
        
        # 7. Form with sample data filled
        print("📸 Capturing filled form...")
        try:
            # Fill in some sample data
            form_fields = await page.query_selector_all("input[type='text'], input[type='email'], input:not([type='submit']):not([type='button'])")
            
            for i, field in enumerate(form_fields[:3]):  # Fill first 3 fields
                sample_data = ["John Doe", "john@example.com", "Engineering"][i] if i < 3 else "Sample"
                try:
                    await field.fill(sample_data)
                    await page.wait_for_timeout(200)
                except:
                    pass
            
            filled_form_path = screenshot_dir / "07-filled-form.png"
            await page.screenshot(path=filled_form_path)
            screenshots.append(("Filled Form", filled_form_path))
        except:
            print("Could not fill form fields")
        
        # 8. API Documentation
        print("📸 Capturing API docs...")
        await page.goto("http://localhost:8004/docs")
        await page.wait_for_timeout(3000)
        api_docs_path = screenshot_dir / "08-api-docs.png"
        await page.screenshot(path=api_docs_path)
        screenshots.append(("API Documentation", api_docs_path))
        
        # 9. API docs expanded endpoint
        print("📸 Capturing expanded API endpoint...")
        try:
            # Try to expand an endpoint
            expand_buttons = await page.query_selector_all(".opblock-summary, .operation-summary")
            if expand_buttons:
                await expand_buttons[0].click()
                await page.wait_for_timeout(1000)
                expanded_api_path = screenshot_dir / "09-api-endpoint-expanded.png"
                await page.screenshot(path=expanded_api_path)
                screenshots.append(("API Endpoint Details", expanded_api_path))
        except:
            print("Could not expand API endpoint")
        
        # 10. Mobile view
        print("📸 Capturing mobile view...")
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.goto("http://localhost:8004")
        await page.wait_for_timeout(2000)
        mobile_path = screenshot_dir / "10-mobile-view.png"
        await page.screenshot(path=mobile_path)
        screenshots.append(("Mobile View", mobile_path))
        
        # Close browser
        await browser.close()
        await playwright.stop()
        
        # Report results
        print(f"\n✅ Successfully captured {len(screenshots)} walkthrough screenshots:")
        total_size = 0
        for name, path in screenshots:
            if path.exists():
                size_kb = path.stat().st_size // 1024
                total_size += size_kb
                print(f"  📷 {name}: {path.name} ({size_kb} KB)")
            else:
                print(f"  ❌ {name}: {path.name} (failed)")
        
        print(f"\n📁 Screenshots saved to: {screenshot_dir}")
        print(f"📊 Total size: {total_size} KB")
        
        return screenshots
        
    except Exception as e:
        print(f"Error capturing screenshots: {e}")
        return []
        
    finally:
        # Clean up server
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()


if __name__ == "__main__":
    asyncio.run(capture_walkthrough_screenshots())
