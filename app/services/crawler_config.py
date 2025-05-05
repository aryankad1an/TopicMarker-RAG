"""
Custom configuration for the crawler to disable debugging.
"""

from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode
import os

def get_browser_config(headless=True, verbose=False):
    """
    Get a browser configuration with debugging disabled.

    Args:
        headless: Whether to run the browser in headless mode
        verbose: Whether to enable verbose logging

    Returns:
        BrowserConfig: A browser configuration with debugging disabled
    """
    # Set environment variable to disable Node.js debugging
    os.environ["NODE_OPTIONS"] = "--no-warnings --no-deprecation"

    # Create browser config with minimal settings - using only basic parameters
    # that are compatible with the installed version of crawl4ai
    return BrowserConfig(
        browser_type="chromium",
        headless=headless,
        verbose=verbose
    )

def get_crawler_config(cache_mode=CacheMode.BYPASS, word_count_threshold=1):
    """
    Get a crawler configuration with minimal settings.

    Args:
        cache_mode: The cache mode to use
        word_count_threshold: The minimum word count threshold

    Returns:
        CrawlerRunConfig: A crawler configuration with minimal settings
    """
    return CrawlerRunConfig(
        cache_mode=cache_mode,
        word_count_threshold=word_count_threshold,
        verbose=False,
        # Disable resource-intensive features
        screenshot=False,
        pdf=False,
        capture_mhtml=False
        # Note: memory_threshold_percent and check_interval removed as they're causing compatibility issues
    )
