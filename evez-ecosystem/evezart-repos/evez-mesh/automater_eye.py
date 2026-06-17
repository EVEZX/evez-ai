from playwright.sync_api import sync_playwright
import os


def wake_browser(headless_mode=True):
    with sync_playwright() as p:
        user_data_dir = './evez_browser_state'

        browser = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=headless_mode,
            args=["--no-sandbox", "--disable-setuid-sandbox"]  # Critical for container environments
        )

        page = browser.new_page()
        page.goto("http://localhost:8080")
        print(f">> Vision Active. Headless: {headless_mode}")

        return browser


if __name__ == "__main__":
    wake_browser(headless_mode=False)
