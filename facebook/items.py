"""Item models for posts and comments."""

import scrapy
from itemloaders.processors import Compose, Identity, Join, TakeFirst
from scrapy import Field
from scrapy.loader import ItemLoader


class FacebookPostItem(scrapy.Item):
    """One Facebook page post with counts."""

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
    """Loader keeping single values, lists for text and comments."""

    default_item_class = FacebookPostItem
    default_output_processor = TakeFirst()

    post_text_out = Join()
    image_urls_out = Identity()
    comments_out = Identity()


class FacebookCommentItem(scrapy.Item):
    """One comment with author and reactions."""

    comment_id = Field()
    comment_text = Field()
    comment_reaction_count = Field()
    author_url = Field()
    author_name = Field()


class FacebookCommentItemLoader(ItemLoader):
    """Loader joining comment text, stripping author names."""

    default_item_class = FacebookCommentItem
    default_output_processor = TakeFirst()

    comment_text_out = Join()
    author_name_out = Compose(TakeFirst(), lambda v: v.rstrip())
