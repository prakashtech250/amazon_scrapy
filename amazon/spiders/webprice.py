import scrapy
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class WebpriceSpider(scrapy.Spider):
    name = "webprice"
    allowed_domains = ["amazon.com"]
    table =  supabase.table('products').select('*').execute()
    productUrls = [f"https://www.{x['domain']}/gp/aws/cart/add.html?ASIN.1={x['asin']}" for x in list(table)[0][1]]
    # start_urls = [f"https://www.{x['domain']}/dp/{x['asin']}" for x in list(table)[0][1]]
    # start_urls = urljoin(domain_url,f'/gp/aws/cart/add.html?ASIN.1={asin}')
    
    def start_requests(self):
        return [
            scrapy.Request(url, callback=self.parse_cart) for url in self.productUrls
        ]
    
    def parse(self, response):
        responseTitle = response.css('title::text').get()
        self.logger.info('Response: %s', responseTitle)
        asin = response.css('#ASIN::attr(value)')
        if asin:
            asin = asin.get()
        title = response.css('#productTitle::text')
        if title:
            title = title.get().strip()
        yield {
            'Response': response.css('title::text').get(),
            'ASIN': asin,
            'TITLE': title,
        }
        
    def parse_cart(self, response):
        responseTitle = response.css('title::text').get().strip()
        self.logger.info('Response: %s, Url: %s', responseTitle, response.url)
        title = response.css('.sc-product-title::text')
        if title:
            title = title.get().strip()
            
        yield {
            'Title': title
        }
            
