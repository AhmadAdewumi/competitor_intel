from typing import Dict, Any

import requests
from bs4 import BeautifulSoup
from oauthlib.oauth2.rfc6749 import parameters

from src.core.tool import BaseTool
from src.utils.logger import log


class ScrapeTool(BaseTool):
    """
    A tool that extracts content from web pages.

    Uses BeautifulSoup to parse HTML and extract:
    - Title
    - Main content (paragraphs, headings, lists)
    - Metadata

    No API key required. Works with any public website.
    """

    def __init__(self):
        super().__init__(
            name="scrape",
            description="Extracts content from a web page. Returns title, content, headings, and metadata.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL of the page to scrape"},
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return (default: 5000)",
                        "default": 5000,
                    },
                },
                "required": ["url"],
            },
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract content from a web page.

        Args:
            input_data: {
                "url": "https://example.com",
                "max_chars": 5000 (optional)
            }

        Returns:
            {
                "success": bool,
                "title": str,
                "content": str,
                "headings": [str],
                "url": str,
                "error": str (if failed)
            }
        """

        # Extract input
        url = input_data.get("url")
        max_chars = input_data.get("max_chars", 5000)

        # validate
        if not url:
            return {
                "success": False,
                "error": "URL is required",
                "title": "",
                "content": "",
                "headings": [],
                "url": "",
            }

        log.info(f"scraping url: {url}")

        try:
            # download the page
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            # remove the script and style tags
            for script in soup(["script", "style"]):
                script.decompose()

                # Extract title
                title = soup.title.string.strip() if soup.title else "No title found"

                # Extract headings
                headings = []
                for heading in soup.find_all(["h1", "h2", "h3"]):
                    text = heading.get_text().strip()
                    if text and len(text) < 200:  # Avoid excessively long "headings"
                        headings.append(text)

                # Extract content
                # Get all paragraphs, lists, and text blocks
                content_parts = []

                # Get paragraphs
                for p in soup.find_all("p"):
                    text = p.get_text().strip()
                    if text and len(text) > 20:  # Skip short paragraphs
                        content_parts.append(text)

                # Get list items
                for li in soup.find_all("li"):
                    text = li.get_text().strip()
                    if text and len(text) > 10:
                        content_parts.append(f"• {text}")

                # Get section content (for pages using sections)
                for section in soup.find_all(["section", "article", "div"]):
                    # Only take if it has a class or id suggesting content
                    if section.get("class") or section.get("id"):
                        text = section.get_text().strip()
                        if text and len(text) > 100:
                            # Don't duplicate too much
                            pass

                    # Combine content
                content = "\n".join(content_parts)

                # Limit content length
                if len(content) > max_chars:
                    content = content[:max_chars] + "... (truncated)"

                # Clean up whitespace
                content = " ".join(content.split())

                log.info(f"Scraped {len(content)} characters from {url}")

                return {
                    "success": True,
                    "title": title,
                    "content": content,
                    "headings": headings[:10],  # Limit headings
                    "url": url,
                    "char_count": len(content),
                    "error": None,
                }

        except requests.exceptions.Timeout:
            log.error(f"Scrape timeout: {url}")
            return {
                "success": False,
                "error": "Page load timed out",
                "title": "",
                "content": "",
                "headings": [],
                "url": url,
            }
        except requests.exceptions.RequestException as e:
            log.error(f"Scrape request failed: {url} - {e}")
            return {
                "success": False,
                "error": f"Failed to download page: {str(e)}",
                "title": "",
                "content": "",
                "headings": [],
                "url": url,
            }
        except Exception as e:
            log.error(f"Scrape error: {url} - {e}")
            return {
                "success": False,
                "error": f"Scraping failed: {str(e)}",
                "title": "",
                "content": "",
                "headings": [],
                "url": url,
            }
