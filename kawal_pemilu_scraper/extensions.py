import logging
from scrapy import signals
from tqdm import tqdm

class ProgressBarExtension:
    def __init__(self):
        self.pbar = None

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        return ext

    def spider_opened(self, spider):
        # Check if total_villages argument was passed
        if hasattr(spider, 'total_villages'):
            try:
                total = int(spider.total_villages)
                self.pbar = tqdm(total=total, unit="desa", desc="Downloading", dynamic_ncols=True)
            except ValueError:
                pass

    def response_received(self, response, request, spider):
        # Only update for village page responses, not images or other assets
        # We can check if 'village_id' is in meta, which we set in the spider
        if self.pbar and 'village_id' in response.meta:
            # We also need to ensure we don't double count if there are redirects or retries
            # But for now, let's assume 1 response per village ID
            self.pbar.update(1)

    def spider_closed(self, spider):
        if self.pbar:
            self.pbar.close()
