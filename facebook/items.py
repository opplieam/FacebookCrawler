# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Join, Identity, Compose


class FacebookPostItem(scrapy.Item):
    page_id = Field()
    page_name = Field()
    page_url = Field()
    post_id = Field()
    post_url = Field()
    post_text = Field()
    image_urls = Field()
    # video_url = Field()
    comment_count = Field()
    reaction_count = Field()
    share_count = Field()
    comments = Field()


class FacebookPostItemLoader(ItemLoader):
    default_item_class = FacebookPostItem
    default_output_processor = TakeFirst()

    post_text_out = Join()
    image_urls_out = Identity()
    comments_out = Identity()


class FacebookCommentItem(scrapy.Item):
    comment_id = Field()
    comment_text = Field()
    comment_reaction_count = Field()
    author_url = Field()
    author_name = Field()


class FacebookCommentItemLoader(ItemLoader):
    default_item_class = FacebookCommentItem
    default_output_processor = TakeFirst()

    comment_text_out = Join()
    author_name_out = Compose(TakeFirst(), lambda v: v.rstrip())

