import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse
from config import settings

class WebScraper:

    def __init__(self, 
                 user_agent: str = settings.USER_AGENT, 
                 max_depth: int = settings.MAX_DEPTH_WEB_SCRAPER):
        """
        Initializes the WebScraper.

        Args:
            max_depth: Maximum depth of links to follow.
        """
        self.max_depth = max_depth
        self.visited_urls: set[str] = set() # used to check if we already visited a link
        self.headers = { 
            'User-Agent': user_agent
        }

    def parse_website(self, base_url: str) -> Optional[Dict]:
        """
        Parses a website, following links up to a maximum depth and
        collecting information from each page.

        Args:
            base_url: The base URL of the website to parse.

        Returns:
            A dictionary representing the website structure and content,
            or None on error.
        """
        parsed_url = urlparse(base_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            logging.error(f"Invalid URL: {base_url}")
            return None
        try:
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            return self._recursive_parse(base_url, base_url, depth=0)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error requesting website {base_url}: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

    def _recursive_parse(self, base_url: str, current_url: str, depth: int) -> Optional[Dict]:
        """
        Recursively parses a website, following links and collecting information.

        Args:
            base_url: The base URL of the website.
            current_url: The current URL being parsed.
            depth: The current depth of recursion.

        Returns:
            A dictionary representing the page's structure and content,
            or None on error.
        """

        if depth > self.max_depth or current_url in self.visited_urls:
            return None
        logging.info(f"Depth {depth} - parsing {current_url}")
        self.visited_urls.add(current_url)

        try:
            response = requests.get(current_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # 1. Extract data from the current page.
            page_data = {
                "url": current_url,
                "title": soup.title.string if soup.title else None,
                "description": self.extract_description(soup),
                "links": [],  # This will hold data from linked pages
            }

            # 2. Find all links on the current page.
            for link in soup.find_all('a', href=True)[:3]:
                absolute_url = urljoin(current_url, link['href'])  # Handles relative & absolute

                # Basic filtering. Skip external, mailto, and tel links.
                if not absolute_url.startswith(base_url) or \
                   absolute_url.startswith("mailto:") or \
                   absolute_url.startswith("tel:"):
                        continue

                # 3. Recursively parse linked pages.
                linked_page_data = self._recursive_parse(base_url, absolute_url, depth + 1)
                if linked_page_data:
                    page_data["links"].append(linked_page_data)


            return page_data

        except requests.exceptions.RequestException as e:
            logging.error(f"Error requesting URL {current_url}: {e}")
            return None
        except Exception as e:
            logging.error(f"Error parsing URL {current_url}: {e}")
            return None


    @staticmethod
    def extract_description(soup: BeautifulSoup) -> Optional[str]:
        """
        Extracts the description of the place from the HTML page.
        Extraction attempts:
        1. From the description meta tag.
        2. From the first few <p> tags.
        """
        descriptions = {}
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            descriptions.update({'meta_description': meta_description.get('content')})

        if paragraphs := soup.find_all('p')[:20]:
            descriptions.update({'paragraphs':" ".join([p.text.strip() for p in paragraphs])})

        return descriptions if descriptions else None

