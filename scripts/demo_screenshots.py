#!/usr/bin/env python3
"""Simple script for capturing FastVimes screenshots with Playwright."""

import asyncio
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright


async def capture_fastvimes_screenshots():
    """Capture screenshots of FastVimes interface for documentation."""
    
    # Ensure directories exist
    screenshot_dir = Path("test-results/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Start FastVimes server
    print("Starting FastVimes server...")
    server_process = subprocess.Popen(
        ["uv", "run", "fastvimes", "serve", "--port", "8003"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to start
    time.sleep(3)
    
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
        
        # 1. Homepage screenshot
        print("Capturing homepage...")
        await page.goto("http://localhost:8003")
        await page.wait_for_timeout(2000)
        homepage_path = screenshot_dir / "homepage.png"
        await page.screenshot(path=homepage_path)
        screenshots.append(("Homepage", homepage_path))
        
        # 2. API docs screenshot
        print("Capturing API docs...")
        await page.goto("http://localhost:8003/api/docs")
        await page.wait_for_timeout(2000)
        api_docs_path = screenshot_dir / "api-docs.png"
        await page.screenshot(path=api_docs_path)
        screenshots.append(("API Documentation", api_docs_path))
        
        # 3. Table view screenshot
        print("Capturing table view...")
        await page.goto("http://localhost:8003/table/users")
        await page.wait_for_timeout(3000)
        table_path = screenshot_dir / "table-view.png"
        await page.screenshot(path=table_path)
        screenshots.append(("Users Table", table_path))
        
        # 4. Form view screenshot
        print("Capturing form view...")
        await page.goto("http://localhost:8003/form/users")
        await page.wait_for_timeout(2000)
        form_path = screenshot_dir / "form-view.png"
        await page.screenshot(path=form_path)
        screenshots.append(("Add User Form", form_path))
        
        # 5. Mobile responsive screenshot
        print("Capturing mobile view...")
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.goto("http://localhost:8003")
        await page.wait_for_timeout(2000)
        mobile_path = screenshot_dir / "mobile-view.png"
        await page.screenshot(path=mobile_path)
        screenshots.append(("Mobile View", mobile_path))
        
        # Close browser
        await browser.close()
        await playwright.stop()
        
        # Report results
        print(f"\n✓ Successfully captured {len(screenshots)} screenshots:")
        for name, path in screenshots:
            size_kb = path.stat().st_size // 1024
            print(f"  {name}: {path} ({size_kb} KB)")
        
        print(f"\nScreenshots saved to: {screenshot_dir}")
        
    except Exception as e:
        print(f"Error capturing screenshots: {e}")
        
    finally:
        # Clean up server
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()


def create_visual_test_baseline():
    """Create baseline screenshots for visual regression testing."""
    baseline_dir = Path("test-results/baselines")
    baseline_dir.mkdir(parents=True, exist_ok=True)
    
    screenshot_dir = Path("test-results/screenshots")
    if not screenshot_dir.exists():
        print("No screenshots found. Run the screenshot demo first.")
        return
    
    # Copy current screenshots as baselines
    for screenshot in screenshot_dir.glob("*.png"):
        baseline_path = baseline_dir / screenshot.name
        baseline_path.write_bytes(screenshot.read_bytes())
        print(f"✓ Created baseline: {baseline_path}")
    
    print(f"\nBaseline screenshots created in: {baseline_dir}")


async def main():
    """Main demo function."""
    print("FastVimes Screenshot Demo")
    print("=" * 50)
    
    choice = input("Choose option:\n1. Capture new screenshots\n2. Create baseline from existing\n3. Both\nEnter (1-3): ")
    
    if choice in ["1", "3"]:
        await capture_fastvimes_screenshots()
    
    if choice in ["2", "3"]:
        create_visual_test_baseline()
    
    print("\nDemo completed!")


if __name__ == "__main__":
    asyncio.run(main())
