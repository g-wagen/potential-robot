import requests
from bs4 import BeautifulSoup
import random
import time
from allrecipe import scrape_one_allrecipe, save_recipe_json

import proxy

# Grab the proxies
proxies = proxy.test_proxies(proxy.scrape_proxies())
num_proxies = len(proxies)

visited = []

def perform_proxy_request(url):
    while True:
        # Choose a random proxy
        proxy_chooser = proxies[random.randint(0, num_proxies - 1)]
        # Try if it actually works ...
        try:
            req = requests.get(
                url, # The URL
                headers=proxy.random_header(), # Random Header
                timeout=3, # 3 second timeout because time is money
                proxies={'https': proxy_chooser}) # Use https proxy
            # Break out of the while if it worked!
            return req
            break
        except:
            # In case it doesn't work just wait a little bit and retry
            proxy.random_wait(1, 3)


def allrecipe_spider(base_url):
    print(f'Base URL: {base_url}')
    # response = requests.get(base_url, headers=proxy.random_header())
    response = perform_proxy_request(base_url)
    parsed_html = BeautifulSoup(response.content, 'html.parser')
    base_url_links = parsed_html.find_all('a')

    # Keep only URLs that contain recipes or recipe collections
    unique_urls = []
    for a in base_url_links:
        try:
            url = a['href']
            if url.startswith('https://www.allrecipes.com/recipe') \
                and 'page=' not in url and '#' not in url:
                unique_urls.append(url)
        except:
            pass

    # Use a set to remove duplicated URLs
    unique_urls = list(set(unique_urls))

    recipes = []
    collections = []

    # Separate the URLs to single and multiple recipes
    for url in unique_urls:
        clean = [x for x in url.split('/') if len(x) > 1]
        if clean[2] == 'recipe':
            recipes.append(url)
        elif clean[2] == 'recipes':
            collections.append(url)

    for rec in recipes:
        # Random sleep
        sleep_time = random.randint(2, 5)
        time.sleep(sleep_time)
        print(rec)
        if rec not in visited:
            scraped = scrape_one_allrecipe(rec)
            save_recipe_json(scraped)
            visited.append(rec)
            # allrecipe_spider(rec)

    for col in collections:
        if col not in visited:
            visited.append(col)
            allrecipe_spider(col)
            # allrecipe_spider(url)
        # print(url.split('/'))
    #     try:
    #         # print(f'Parsing {url}')
    #         if '/recipe/' in url:
    #             allrecipe_spider(url)
    #             # print(f'Scraping: {url}')
    #             # new_base_url = url
    #             # save_recipe_json(allrecipe_spider(url))
    #         #     # global counter
    #         #     # counter += 1
    #         #     # random_sleep(1, 5)
    #         #     # scrape = scrape_one_allrecipe(url)
    #         #     # print(scrape)
    #         #     # save_recipe_json(scrape)
    #         #     # random_sleep(1, 3)
    #         #     allrecipe_spider(url)
    #         # else:
    #         #     new_base_url = url
    #         # #     # random_sleep(1, 3)
    #         #     allrecipe_spider(new_base_url)
    #     except:
    #         pass


allrecipe_spider('https://www.allrecipes.com')