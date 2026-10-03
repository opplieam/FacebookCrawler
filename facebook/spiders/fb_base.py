from typing import Iterable, Any

from scrapy import Spider, Request, FormRequest
from scrapy.exceptions import CloseSpider
from scrapy.http import Response


class FbBaseSpider(Spider):

    base_url = 'https://www.facebook.com/'

    allowed_domains = ["facebook.com", "localhost"]

    def __init__(self, *args, **kwargs):
        super(FbBaseSpider, self).__init__(*args, **kwargs)

        self.email: str = kwargs.get("email")
        self.password: str = kwargs.get("password")
        if not self.email or not self.password:
            raise CloseSpider("Please provide email and password.")
        page_id_arg: str = kwargs.get("page_id")

        if not page_id_arg:
            raise CloseSpider("Please provide page_id.")

        self.page_id: list = []
        if ',' in page_id_arg:
            self.page_id = page_id_arg.split(',')
        else:
            self.page_id = [page_id_arg]

        self.limit: int = kwargs.get("limit", 100)
        if self.limit != -1:
            self.custom_settings = {
                "CLOSESPIDER_ITEMCOUNT": self.limit,
            }

    def start_requests(self) -> Iterable[Request]:
        # Session cookies are kept by Scrapy's cookie middleware,
        # so the login session carries over to page requests.
        yield Request(url=self.base_url, callback=self.parse_login)

    def parse_login(self, response: Response, **kwargs: Any) -> Any:
        yield FormRequest.from_response(
            response,
            formdata={"email": self.email, "pass": self.password},
            callback=self.parse,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.xpath("//form[@id='login_form']").get():
            raise CloseSpider("Login failed, check email and password.")
        for page_id in self.page_id:
            url = self.base_url + page_id
            yield Request(
                url=url, callback=self.parse_page,
                meta={"page_id": page_id},
            )
