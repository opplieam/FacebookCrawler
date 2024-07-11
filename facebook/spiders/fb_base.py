from typing import Iterable, Any

from scrapy import Spider, Request
from scrapy.exceptions import CloseSpider
from scrapy.http import Response
from scrapy_splash import SplashRequest

script = """
function main(splash, args)
  splash.private_mode_enabled = false
  splash:init_cookies(splash.args.cookies)

  splash:on_request(
  	function(request)
      request:set_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9")
      request:set_header("Accept-Language", "en")
    end
  )
  assert(splash:go(args.url))
  assert(splash:wait(1))

  input_box = assert(splash:select("#m_login_email"))
  input_box:focus()
  input_box:send_text(splash.args.email)
  assert(splash:wait(0.5))

  input_box = assert(splash:select("#m_login_password"))
  input_box:focus()
  input_box:send_text(splash.args.password)
  assert(splash:wait(0.5))

  input_box:send_keys("<Enter>")
  assert(splash:wait(5))

  decline_button = assert(splash:select('a[href*="/save-device/cancel"]'))
  decline_button:mouse_click()
  splash:wait(5)

  splash:set_viewport_full()

  return {
    cookies = splash:get_cookies(),
    html = splash:html()
  }
end
"""


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
        yield SplashRequest(
            url=self.base_url, callback=self.parse,
            endpoint="execute",
            args={
                'lua_source': script,
                'email': self.email,
                'password': self.password,
            }
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        splash_cookies = response.data['cookies']
        for page_id in self.page_id:
            url = self.base_url + page_id
            yield Request(
                url=url, cookies=splash_cookies, callback=self.parse_page,
                meta={"page_id": page_id, "cookies": splash_cookies},
            )
