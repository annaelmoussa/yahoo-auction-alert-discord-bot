import os
import json
import requests
import hikari
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from logging import info
import re
from typing import List, Optional

processed_urls = {}
proxies = []
last_proxy_update = None
PROXY_UPDATE_INTERVAL = timedelta(hours=1)

conversion_rates = {}
conversion_rates_timestamp = None
CONVERSION_CACHE_DURATION = timedelta(hours=1)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
}

def get_proxies() -> List[str]:
    global proxies, last_proxy_update
    now = datetime.now()
    
    if os.getenv('USE_PROXIES', 'false').lower() != 'true':
        return []
        
    if not last_proxy_update or (now - last_proxy_update) > PROXY_UPDATE_INTERVAL:
        try:
            proxy_url = os.getenv('PROXY_LIST_URL')
            if not proxy_url:
                return []
                
            response = requests.get(proxy_url)
            if response.status_code == 200:
                proxies = [p.strip() for p in response.text.split('\n') if p.strip()]
                last_proxy_update = now
        except Exception as e:
            info(f"Error fetching proxies: {str(e)}")
            return []
            
    return proxies

def get_next_proxy() -> Optional[dict]:
    proxy_list = get_proxies()
    if not proxy_list:
        return None
        
    # Rotate through proxies
    if proxy_list:
        proxy = proxy_list.pop(0)
        proxy_list.append(proxy)
        return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
    return None

async def check_yahoo_fleamarket(bot, translator, alert, page=1):
    url = f'https://buyee.jp/paypayfleamarket/search?keyword={alert["name"]}&order-sort=created_time&page={page}'
    
    current_proxies = get_next_proxy()
    try:
        response = requests.get(url, headers=headers, proxies=current_proxies, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        item_listings = soup.find('ul', {'class': 'item-lists'})
        if not item_listings:
            return
        
        listings = item_listings.find_all('li', {'class': 'list'})
        date = datetime.now().date()

        for item in listings:
            try:
                item_url = 'https://buyee.jp' + item.find('a').get('href')

                if item_url in processed_urls:
                    continue

                name = item.find('h2', {'class': 'name'}).text
                price = item.find('p', {'class': 'price'}).text
                target_currency = alert.get("currency", "JPY")
                if target_currency.upper() != "JPY":
                    parsed_price = parse_price(price)
                    if parsed_price is not None:
                        converted_price = convert_price(parsed_price, target_currency)
                        if converted_price is not None:
                            price += f" (≈ {converted_price} {target_currency.upper()})"
                thumbnail_data = item.find('img', {'class': "thumbnail"}).get("data-bind")
                thumbnail_start = thumbnail_data.find('imagePath: \'') + len('imagePath: \'')
                thumbnail_end = thumbnail_data.find('\'', thumbnail_start)
                thumbnail = "https:" + thumbnail_data[thumbnail_start:thumbnail_end]

                name_en = translator.translate(name)
                
                embed = create_embed("Yahoo! Flea Market", item_url, name, name_en, thumbnail, price)
                await send_alert(bot, alert, embed)

                info(f'New flea market item found: {item_url}')
                processed_urls[item_url] = date
                
            except Exception as e:
                info(f"Error processing flea market item: {str(e)}")
    except Exception as e:
        info(f"Error checking flea market: {str(e)}")

async def check_yahoo_auction(bot, translator, alert, page=1):
    url = f'https://buyee.jp/item/search/query/{alert["name"]}?sort=end&order=d&page={page}'

    current_proxies = get_next_proxy()
    try:
        response = requests.get(url, headers=headers, proxies=current_proxies, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        auction_results = soup.find('ul', {'class': 'auctionSearchResult'})
        if not auction_results:
            return
        
        item_listings = auction_results.find_all('li', {'class': 'itemCard'})
        date = datetime.now().date()

        for item in item_listings:
            try:
                item_url = 'https://buyee.jp' + item.find('a').get('href')

                if item_url in processed_urls:
                    continue

                name = item.find('div', {'class': 'itemCard__itemName'}).find('a').text
                price = item.find('div', {'class': 'g-price__outer'}).find('span').text
                target_currency = alert.get("currency", "JPY")
                if target_currency.upper() != "JPY":
                    parsed_price = parse_price(price)
                    if parsed_price is not None:
                        converted_price = convert_price(parsed_price, target_currency)
                        if converted_price is not None:
                            price += f" (≈ {converted_price} {target_currency.upper()})"
                thumbnail = item.find('img', {'class': 'g-thumbnail__image'}).get('data-src').split(';')[0]

                name_en = translator.translate(name)
                
                embed = create_embed("Yahoo! JAPAN Auction", item_url, name, name_en, thumbnail, price)
                await send_alert(bot, alert, embed)

                info(f'New auction item found: {item_url}')
                processed_urls[item_url] = date
                
            except Exception as e:
                info(f"Error processing auction item: {str(e)}")
    except Exception as e:
        info(f"Error checking auction: {str(e)}")

def create_embed(service, url, name, name_en, thumbnail, price=None):
    desc = name
    if price is not None:
        desc += '\nPrice: ' + price
        
    embed = hikari.Embed(
        title=name_en,
        url=url,
        description=desc
    )
    embed.set_author(name=service)
    embed.set_image(thumbnail)
    return embed

async def send_alert(bot, alert, embed):
    try:
        await bot.rest.create_message(alert['channel_id'], embed=embed)
    except Exception as e:
        info(f"Error sending alert: {str(e)}")

async def check_get_auctions(bot, translator, alert):
    """Main function to check both auction types for new items"""
    current_date = datetime.now().date()
    for url in list(processed_urls.keys()):
        if current_date - processed_urls[url] > timedelta(weeks=3):
            del processed_urls[url]
            
    await check_yahoo_auction(bot, translator, alert)
    await check_yahoo_fleamarket(bot, translator, alert)

def get_conversion_rates():
    global conversion_rates, conversion_rates_timestamp
    now = datetime.now()
    if conversion_rates_timestamp is None or (now - conversion_rates_timestamp) > CONVERSION_CACHE_DURATION:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/JPY")
        if response.status_code == 200:
            data = response.json()
            conversion_rates = data.get("rates", {})
            conversion_rates_timestamp = now
        else:
            conversion_rates = {}
    return conversion_rates

def convert_price(price, target_currency):
    rates = get_conversion_rates()
    rate = rates.get(target_currency.upper())
    if rate is None:
        return None
    converted_value = price * rate
    return f"{converted_value:,.2f}"

def parse_price(price_str):
    match = re.search(r"([\d,]+(?:\.\d+)?)", price_str)
    if match:
        num_str = match.group(1).replace(",", "")
        try:
            return float(num_str)
        except:
            return None
    return None 