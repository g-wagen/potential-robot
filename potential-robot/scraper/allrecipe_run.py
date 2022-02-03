import os
import requests
from bs4 import BeautifulSoup
import random
import time
from allrecipe import scrape_one_allrecipe, save_recipe_json


def random_sleep(x=10, y=60):
    sleep_time = random.randint(x, y)
    time.sleep(sleep_time)

def allrecipe_spider(base_url):
    print(f'Base URL: {base_url}')
    response = requests.get(base_url)
    parsed_html = BeautifulSoup(response.content, 'html.parser')
    base_url_links = parsed_html.find_all('a')

    # Keep only URLs that contain recipes or recipe collections
    unique_urls = []
    for a in base_url_links:
        try:
            url = a['href']
            if url.startswith('https://www.allrecipes.com/recipe'):
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
        scraped = scrape_one_allrecipe(rec)
        save_recipe_json(scraped)

    for col in collections:
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