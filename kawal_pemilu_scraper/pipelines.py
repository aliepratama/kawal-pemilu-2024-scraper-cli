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
        
        # Generate a short hash for the filename
        url_hash = hashlib.sha1(request.url.encode('utf-8')).hexdigest()
        
        # Sanitize names
        def sanitize(name):
            return "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
            
        province = sanitize(province)
        regency = sanitize(regency)
        district = sanitize(district)
        village_name = sanitize(village_name)
        
        return f"{province}/{regency}/{district}/{village_name}/{url_hash}.jpg"

