"""Playwright-based browser adapter: explicit URL allowlist and visible actions."""
from urllib.parse import urlsplit

class BrowserController:
    def __init__(self, allowed_hosts, headless=False):
        self.allowed_hosts = {str(host).casefold() for host in allowed_hosts}
        self.headless = headless
        self._driver = None
        self.browser = None
        self.page = None
    def validate(self, url):
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname or parts.hostname.casefold() not in self.allowed_hosts:
            raise PermissionError("HTTPS destination not on allowlist")
        if parts.username or parts.password:raise PermissionError("Credentials in URL")
        return url
    def start(self):
        from playwright.sync_api import sync_playwright
        self._driver = sync_playwright().start()
        try:
            self.browser = self._driver.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page(accept_downloads=False)
        except Exception:
            self._driver.stop()
            self._driver = None
            raise
    def navigate(self,url):
        if self.page is None:raise RuntimeError("Browser not started")
        return self.page.goto(self.validate(url),wait_until="domcontentloaded",timeout=20000)
    def click(self, selector):
        if self.page is None:raise RuntimeError("Browser not started")
        self.page.locator(selector).first.click(timeout=10000)
    def fill(self, selector, value):
        if self.page is None:raise RuntimeError("Browser not started")
        self.page.locator(selector).first.fill(value,timeout=10000)
    def screenshot(self, path):
        if self.page is None:raise RuntimeError("Browser not started")
        self.page.screenshot(path=str(path),full_page=False)
    def close(self):
        if self.browser:self.browser.close()
        if self._driver:self._driver.stop()
        self.page=self.browser=self._driver=None
