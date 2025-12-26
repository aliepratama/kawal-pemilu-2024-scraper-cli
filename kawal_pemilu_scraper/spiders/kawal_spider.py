import scrapy
import json
import os
import sys
from urllib.parse import unquote

class KawalSpider(scrapy.Spider):
    name = "kawal_spider"
    allowed_domains = ["kawalpemilu.org", "googleusercontent.com", "lh3.googleusercontent.com", "googleapis.com", "storage.googleapis.com"]
    
    async def start(self):
        """Async start method (replaces deprecated start_requests)"""
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
            
            # Extract district ID (first 6 digits of village ID) and get district name
            # Village ID format: 10 digits (e.g., 6104212001)
            # District ID format: 6 digits (e.g., 610421)
            district_id = vid[:6] if len(vid) == 10 else ''
            district_name = id2name.get(district_id, self.district_name)
            
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "village_id": vid,
                    "village_name": village_name,
                    "district_name": district_name,
                    "regency_name": self.regency_name,
                    "province_name": self.province_name
                },
                callback=self.parse
            )


    async def parse(self, response):
        page = response.meta["playwright_page"]
        district_name = response.meta['district_name']
        village_name = response.meta['village_name']
        
        try:
            # Wait for the main app to load
            try:
                await page.wait_for_selector("app-root", timeout=10000)
            except Exception as e:
                # Log timeout but continue - page might still have loaded content
                self.logger.debug(f"app-root timeout for {district_name} > {village_name} - continuing anyway")
            
            # Wait a bit for dynamic content
            await page.wait_for_timeout(3000)
            
            # Determine download type (default to regular if not specified)
            download_type = getattr(self, 'download_type', 'regular')
            
            # Extract photos with TPS information
            # Download type decides which URLs to extract:
            # - 'regular': Full C1 images from .foto-kpu div>a links
            # - 'roi': ROI images from div id attributes (KPU photos only)
            
            if download_type == 'roi':
                # Extract ROI image URLs from div id attributes
                # All images have ROI, not just KPU-labeled ones
                items = await page.evaluate("""
                    () => {
                        const results = [];
                        
                        // Find all rows with photos
                        const rows = document.querySelectorAll('tr');
                        
                        rows.forEach((row, index) => {
                            // Find all divs with id starting with https://storage.googleapis.com
                            // These contain ROI URLs for ALL photos (not just KPU)
                            const roiDivs = Array.from(row.querySelectorAll('div[id^="https://storage.googleapis.com"]'));
                            
                            if (roiDivs.length > 0) {
                                // URLs in div id may be URL-encoded (e.g. %3D for =)
                                // Return them as-is, we'll decode in Python
                                const roiUrls = roiDivs.map(div => div.id);
                                let tps = (index + 1).toString();
                                
                                results.push({
                                    tps_number: tps,
                                    photos: roiUrls
                                });
                            }
                        });
                        
                        // Debug: log extraction results
                        console.log('[ROI DEBUG] Total rows scanned:', rows.length);
                        console.log('[ROI DEBUG] Rows with ROI images:', results.length);
                        
                        return results;
                    }
                """)
            else:
                # Extract regular C1 image URLs (current logic)
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
                district_name = response.meta['district_name']
                village_name = response.meta['village_name']
                
                # Better logging with district + village info
                mode_label = "ROI" if download_type == 'roi' else "C1"
                self.logger.info(f"Found {total_photos} {mode_label} photos for {district_name} > {village_name}")
                
                for item in items:
                    # Decode ROI URLs to prevent double-encoding by Scrapy
                    photos = item['photos']
                    if download_type == 'roi':
                        # ROI URLs contain %3D which needs to be unquoted to =
                        photos = [unquote(url) for url in photos]
                    
                    yield {
                        "image_urls": photos,
                        "tps_number": item['tps_number'],
                        "village_id": response.meta['village_id'],
                        "village_name": response.meta['village_name'],
                        "district_name": response.meta['district_name'],
                        "regency_name": response.meta['regency_name'],
                        "province_name": response.meta['province_name']
                    }
            else:
                district_name = response.meta['district_name']
                village_name = response.meta['village_name']
                mode_label = "ROI" if download_type == 'roi' else "C1"
                self.logger.info(f"No {mode_label} photos found for {district_name} > {village_name}")
            
            # ALWAYS print progress marker (even if no photos) for CLI to track
            print(f"[PROGRESS] {response.meta['district_name']} > {response.meta['village_name']}", flush=True)
            sys.stdout.flush()
                
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {e}")
        finally:
            await page.close()

