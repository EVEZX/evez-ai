import os
import sys
from playwright.sync_api import sync_playwright


def execute_gateway_session(target_url="http://localhost:8080", headless=True):
    """
    Spawns a persistent browser instance to keep session headers alive
    and automate internal interactions within the control center.
    """
    user_data_dir = os.path.abspath("./evez_browser_state")

    with sync_playwright() as p:
        print(f">> Launching contextual browser eye. Headless: {headless}")
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )

        page = context.new_page()
        try:
            print(f">> Routing navigation loop to: {target_url}")
            page.goto(target_url, wait_until="networkidle", timeout=30000)
            print(f">> Gateway Title Resolved: {page.title()}")
            context.close()
            return True
        except Exception:
            print(f"!! Gateway navigation interrupted: {str(sys.exc_info()[1])}")
            context.close()
            return False


if __name__ == "__main__":
    execute_gateway_session(headless=True)
