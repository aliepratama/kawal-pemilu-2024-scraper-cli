import scrapy
import json
import os
import sys

class KawalSpider(scrapy.Spider):
    name = "kawal_spider"
    allowed_domains = ["kawalpemilu.org", "googleusercontent.com", "lh3.googleusercontent.com"]
    
    def start_requests(self):
        if hasattr(self, 'village_ids_file'):
            with open(self.village_ids_file, 'r') as f:
                village_ids = f.read().split(',')
        else:
            village_ids = self.village_ids.split(',')
        
        # Load tps.json to get names
        try:
            with open('context/tps.json', 'r') as f:
                data = json.load(f)
            id2name = data.get('id2name', {})
        except Exception as e:
            self.logger.error(f"Failed to load tps.json: {e}")
            id2name = {}
        
        for vid in village_ids:
            url = f"https://kawalpemilu.org/h/{vid}"
            village_name = id2name.get(vid, vid)
            
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "village_id": vid,
                    "village_name": village_name,
                    "district_name": self.district_name,
                    "regency_name": self.regency_name,
                    "province_name": self.province_name
                },
                callback=self.parse
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        
        try:
            # Wait for the main app to load
            try:
                await page.wait_for_selector("app-root", timeout=10000)
            except:
                # If verbose is off, we might not want to see this in logs, but it's a warning.
                # However, we are suppressing logs in CLI if verbose=False.
                self.logger.warning(f"Timeout waiting for app-root on {response.url}")
            
            # Wait a bit for dynamic content
            await page.wait_for_timeout(3000)
            
            # Extract photos
            photos = await page.evaluate("Array.from(document.querySelectorAll('.foto-kpu div>a')).map(a=>a.href)")
            
            if photos:
                self.logger.info(f"Found {len(photos)} photos for {response.meta['village_name']}")
                yield {
                    "image_urls": photos,
                    "village_id": response.meta['village_id'],
                    "village_name": response.meta['village_name'],
                    "district_name": response.meta['district_name'],
                    "regency_name": response.meta['regency_name'],
                    "province_name": response.meta['province_name']
                }
            else:
                self.logger.info(f"No photos found for {response.meta['village_name']}")
            
            # Print progress marker to stdout for CLI to pick up
            print(f"[PROGRESS] {response.meta['village_name']}")
            sys.stdout.flush()
                
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {e}")
        finally:
            await page.close()

