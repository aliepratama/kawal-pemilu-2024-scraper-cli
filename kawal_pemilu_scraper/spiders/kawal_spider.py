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
            
            # Extract photos with TPS information
            # We assume the rows correspond to TPS numbers sequentially starting from 1
            # or we try to find the TPS number in the row.
            # Based on inspection, the rows seem to correspond to TPS.
            
            items = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('tr');
                    const results = [];
                    rows.forEach((row, index) => {
                        const photos = Array.from(row.querySelectorAll('.foto-kpu div>a')).map(a => a.href);
                        if (photos.length > 0) {
                            // Try to find TPS number in the first cell if it exists, otherwise use index + 1
                            let tps = (index + 1).toString();
                            
                            // Check if there is a specific element for TPS number
                            // Based on inspection, it wasn't obvious, so we default to index + 1
                            // But we should pad it to 3 digits
                            
                            results.push({
                                tps_number: tps,
                                photos: photos
                            });
                        }
                    });
                    return results;
                }
            """)
            
            if items:
                total_photos = sum(len(item['photos']) for item in items)
                self.logger.info(f"Found {total_photos} photos for {response.meta['village_name']}")
                
                for item in items:
                    yield {
                        "image_urls": item['photos'],
                        "tps_number": item['tps_number'],
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

