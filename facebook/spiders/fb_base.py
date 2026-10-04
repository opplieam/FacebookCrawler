"""Shared spider base: session handling and page fan-out."""

from typing import Any, ClassVar

from scrapy import Request, Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import Response
from scrapy_playwright.page import PageMethod

# Saved by save_auth.py after one manual login. Holds live
# session cookies.
AUTH_FILE = "auth.json"


class FbBaseSpider(Spider):
    """Base spider holding the Playwright session."""

    base_url = 'https://www.facebook.com/'

    allowed_domains: ClassVar[list] = ["facebook.com", "localhost"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        page_id_arg = kwargs.get("page_id")

        if not page_id_arg:
            raise CloseSpider("Please provide page_id.")

        self.page_id: list = []
        if ',' in page_id_arg:
            self.page_id = page_id_arg.split(',')
        else:
            self.page_id = [page_id_arg]

    async def start(self) -> Any:
        """Open the landing page to establish the session."""
        yield Request(
            url=self.base_url, callback=self.parse,
            meta={
                "playwright": True,
                "playwright_context_kwargs": {"storage_state": AUTH_FILE},
            },
        )

    def parse_page(self, response: Response, **_kwargs: Any) -> Any:
        """Parse one timeline page. Implemented by subclasses."""
        raise NotImplementedError

    def parse(self, response: Response, **_kwargs: Any) -> Any:
        """Fan out one timeline request per page id."""
        if response.xpath("//form[@id='login_form']").get():
            raise CloseSpider("Session expired, rerun python save_auth.py.")
        for page_id in self.page_id:
            url = self.base_url + page_id
            yield Request(
                url=url, callback=self.parse_page,
                meta={
                    "page_id": page_id,
                    "playwright": True,
                    "playwright_context_kwargs": {"storage_state": AUTH_FILE},
                    "playwright_page_methods": [
                        PageMethod("wait_for_timeout", 2000),
                    ],
                },
            )
