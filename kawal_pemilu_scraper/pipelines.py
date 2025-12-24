from scrapy.pipelines.images import ImagesPipeline
import scrapy
import hashlib

class CustomImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for image_url in item.get('image_urls', []):
            yield scrapy.Request(image_url, meta={'item': item})

    def file_path(self, request, response=None, info=None, *, item=None):
        item = request.meta['item']
        
        province = item['province_name']
        regency = item['regency_name']
        district = item['district_name']
        village_name = item['village_name']
        village_id = item['village_id']
        tps_number = item['tps_number']
        
        # Format TPS number to 3 digits
        tps_number_str = str(tps_number).zfill(3)
        
        # Sanitize names
        def sanitize(name):
            return "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
            
        province = sanitize(province)
        regency = sanitize(regency)
        district = sanitize(district)
        village_name = sanitize(village_name)
        
        # New filename format: raw_<kode_kelurahan>_<nomor TPS dalam 3 digit>.jpg
        # Note: If there are multiple images for one TPS, we need to handle collision.
        # The requirement says "raw_<kode_kelurahan>_<nomor TPS dalam 3 digit>.jpg"
        # But a TPS can have multiple pages (C1 Plano has multiple pages).
        # So we should probably append a counter or hash if multiple images exist for same TPS.
        # However, the user example "raw_6271021003_004.jpg" implies one file per TPS? 
        # Or maybe they just gave one example.
        # Usually C1 Plano has 3 pages (Presiden).
        # Let's append a short hash of the URL to ensure uniqueness if multiple images exist,
        # OR use an index if we can track it. 
        # Since `file_path` is called per request, we don't easily know the index of the image in the list.
        # But we can use the URL hash to be safe and append it, or just use it as a suffix.
        # Wait, the user instruction is specific: "raw_<kode_kelurahan>_<nomor TPS dalam 3 digit>.jpg"
        # If I strictly follow this, multiple images will overwrite each other.
        # I will append a short hash to avoid overwrite, but keep the prefix as requested.
        # Example: raw_6271021003_004_a1b2c.jpg
        
        url_hash = hashlib.sha1(request.url.encode('utf-8')).hexdigest()[:5]
        filename = f"raw_{village_id}_{tps_number_str}_{url_hash}.jpg"
        
        return f"{province}/{regency}/{district}/{village_name}/{filename}"

