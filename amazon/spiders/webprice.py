import scrapy
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import re

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
        self.logger.info('Response: %s, Url: %s, Status_Code: %s', responseTitle, response.url, response.status)
        title = response.css('.sc-product-title::text')
        if title:
            title = title.get().strip()
        price = response.css('.sc-product-price::text')
        if price:
            price = price.get().strip()
            price, currency = self.float_price(price)
        else:
            price = 0
            currency = None
        imageUrl = response.css('.sc-product-link img::attr(src)')
        if imageUrl:
            imageUrl = imageUrl.get()
        asin = response.url.split('=')[-1].strip()
        
        if title:
            data, count = supabase.table('products').update({'title': title, 'price': price}).eq('asin', asin).execute()
            self.logger.info('Data: %s \nCount: %s', data, count)
        yield {
            'Asin': asin,
            'Title': title,
            'Price': price,
            'Currency': currency,
            'Image': imageUrl
        }
        
    def float_price(self, price_text):
        pattern0 = r"\d+\,\d+"
        pattern1 = r"\d+\.\d+"
        pattern2 = r"\d+"
        currency_pattern = r"[^\d,.]+"
        found0 = re.search(pattern0, price_text)
        found1 = re.search(pattern1, price_text)
        found2 = re.search(pattern2, price_text)
        currency_found = re.search(currency_pattern, price_text)
        if found0:
            price = found0.group(0).replace(',','.')
        elif found1:
            price = found1.group(0)
        elif found2:
            price = found2.group(0)
        else:
            price = 0
        try:
            price = int(price)
        except:
            price = float(price)
        if currency_found:
            currency = currency_found.group(0).strip()
        else:
            currency = ''
        return price, currency
            
