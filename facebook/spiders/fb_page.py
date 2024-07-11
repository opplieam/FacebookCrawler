import json
import re
from typing import Any

from itemloaders.processors import MapCompose
from scrapy import Selector, Request
from scrapy.http import Response
from scrapy.utils.response import open_in_browser

from .fb_base import FbBaseSpider
from ..items import FacebookPostItemLoader, FacebookCommentItemLoader


class FbPageSpider(FbBaseSpider):
    name = 'fb_page'

    def __extract_html_chunk(self, response: Response, xpath: str, search_term: str) -> str:
        html_chunk: str = ""
        for chunk in response.xpath(xpath).extract():
            if re.search(search_term, chunk):
                html_chunk = chunk.replace("<!--", "").replace("-->", "")
                break
        return html_chunk

    def parse_page(self, response: Response, **kwargs: Any) -> Any:
        # open_in_browser(response)
        html_chunk = self.__extract_html_chunk(
            response, "//div[@class='hidden_elem']/code", "postPlaceholder"
        )
        if not html_chunk:
            return

        page_name: list = response.meta.get("page_name", response.xpath("//title/text()").extract())

        post_sel = Selector(text=html_chunk)

        for post in post_sel.css(".feed article"):
            post_url = post.css("a[href*=story_fbid]::attr(href)").extract_first()
            post_url = response.urljoin(post_url)
            yield Request(
                url=post_url,
                callback=self.parse_post,
                cookies=response.meta.get("cookies"),
                meta={
                    "cookies": response.meta.get("cookies"),
                    "page_name": page_name,
                    "page_url": response.url,
                    "post_url": post_url
                }
            )

        placeholder_pagination_id = post_sel.xpath(
            '//div[@class="feed"]//span[@role="progressbar"]/parent::div/@id'
        ).extract_first()
        pattern = r'"{pag_id}",href:"(.*?)"'.format(pag_id=placeholder_pagination_id)
        stream_pagination_url = response.urljoin(self.__extract_stats_count(pattern, response.text))
        yield Request(
            url=stream_pagination_url,
            callback=self.parse_pagination,
            cookies=response.meta.get("cookies"),
            meta={
                "cookies": response.meta.get("cookies"),
                "page_name": page_name,
                "page_url": response.url,
            }
        )

    def parse_pagination(self, response: Response, **kwargs: Any) -> Any:
        json_response = json.loads(response.text.replace("for (;;);", ''))
        html = json_response.get("payload").get("actions")[0].get("html")
        post_sel = Selector(text=html)
        for post in post_sel.css(".storyStream>article"):
            post_url = post.css("a[href*=story_fbid]::attr(href)").extract_first()
            post_url = response.urljoin(post_url)
            yield Request(
                url=post_url,
                callback=self.parse_post,
                cookies=response.meta.get("cookies"),
                meta={
                    "cookies": response.meta.get("cookies"),
                    "page_name": response.meta.get("page_name"),
                    "page_url": response.meta.get("page_url"),
                    "post_url": post_url
                }
            )

        placeholder_pagination_id = post_sel.xpath(
            '//span[@role="progressbar"]/parent::div/@id'
        ).extract_first()
        pattern = r'{pag_id}\\",\\"href\\":(.*?)\\",'.format(pag_id=placeholder_pagination_id)
        cursor = re.search(pattern, response.text).group(1).split("?")[-1]
        next_page_url = "https://m.facebook.com/profile/timeline/stream/?{query}".format(query=cursor)

        yield Request(
            url=next_page_url,
            callback=self.parse_pagination,
            cookies=response.meta.get("cookies"),
            meta={
                "cookies": response.meta.get("cookies"),
                "page_name": response.meta.get("page_name"),
                "page_url": response.meta.get("page_url")
            }
        )

    def __extract_stats_count(self, pattern: str, text: str) -> Any:
        return re.search(pattern, text).group(1)

    def parse_post(self, response: Response, **kwargs: Any) -> Any:
        # open_in_browser(response)
        html_chunk = self.__extract_html_chunk(
            response, "//div[@class='hidden_elem']/code", "story_body_container"
        )
        html_sel = Selector(text=html_chunk)
        loader = FacebookPostItemLoader(selector=html_sel)
        loader.add_value("page_id", response.meta.get("page_id"))
        loader.add_value("page_name", response.meta.get("page_name"))
        loader.add_value("page_url", response.meta.get("page_url"))
        loader.add_value("post_url", response.meta.get("post_url"))
        loader.add_xpath("post_text", '//div[@class="story_body_container"]//p//text()')
        if not loader.get_output_value("post_text"):
            loader.add_xpath(
                "post_text",
                '//div[@class="story_body_container"]//span[@role="presentation"]//text()'
            )
        loader.add_value("image_urls", response.xpath("//meta[@property='og:image']/@content").extract())
        loader.add_value(
            "comment_count",
            int(self.__extract_stats_count(r"comment_count:(.*?),", response.text))
        )
        loader.add_value(
            "reaction_count",
            int(self.__extract_stats_count(r"reactioncount:(.*?),", response.text))
        )
        loader.add_value(
            "share_count",
            int(self.__extract_stats_count(r"share_count:(.*?),", response.text))
        )

        comment_chunk = self.__extract_html_chunk(
            response, "//div[@class='hidden_elem']/code", "m-mentions-expand"
        )
        comment_sel = Selector(text=comment_chunk)
        for comment in comment_sel.xpath('//div[@data-sigil="comment"]'):
            comment_loader = FacebookCommentItemLoader(selector=comment)
            comment_loader.add_xpath("comment_id", "./@id")
            comment_loader.add_xpath(
                "comment_text",
                './/div[@data-sigil="comment-body"]//text()'
            )
            comment_loader.add_xpath(
                "author_name",
                './/div[@data-sigil="comment-body"]/preceding-sibling::div/a/text()'
            )
            comment_loader.add_xpath(
                "author_url",
                './/div[@data-sigil="comment-body"]/preceding-sibling::div/a/@href',
                MapCompose(
                    response.urljoin,
                    lambda v: v.split("&", 1)[0] if "profile.php" in v else v.split('?')[0],
                    lambda v: v.replace('m.', "")
                )
            )
            comment_id = comment_loader.get_output_value("comment_id")
            pattern = r"ft_ent_identifier:{comment_id},.*?reactioncount:(.*?),".format(comment_id=comment_id)
            comment_loader.add_value("comment_reaction_count", self.__extract_stats_count(pattern, response.text))

            loader.add_value("comments", comment_loader.load_item())

        yield loader.load_item()
