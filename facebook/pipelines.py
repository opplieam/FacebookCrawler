"""Item pipeline helpers."""

# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

class FacebookPipeline:  # pylint: disable=too-few-public-methods
    """Placeholder pipeline, extend for storage backends."""

    # pylint: disable-next=unused-argument

    # pylint: disable-next=unused-argument
    def process_item(self, item, spider):
        """Pass items through unchanged."""
        return item
