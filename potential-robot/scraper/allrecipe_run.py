import requests
from bs4 import BeautifulSoup

import helpers
import proxy
import allrecipe

# Grab the proxies
pickled_proxies = 'proxies.pickle'
proxies = helpers.pickler(pickled_proxies, data=proxy.test_proxies(proxy.scrape_proxies()))

visited = []

def allrecipes_page_exists(url):
    """
    Check if the url exists by reporting success
    if the returned status code x is: x < 400
    """
    response = requests.get(url, headers=proxy.random_header())
    return False if response.status_code > 399 else True

def allrecipes_main_categories():
    """Fetch the main recipe categories from allrecipes"""
    output = []
    response = requests.get('https://www.allrecipes.com/recipes/', headers=proxy.random_header())
    parsed_html = BeautifulSoup(response.content, 'html.parser')
    recipe_categories = parsed_html.find_all('a', class_='recipeCarousel__link')
    for c in recipe_categories:
        try:
            output.append(c['href'])
        except:
            pass
    return output

def reset_allrecipe_spider():
    random_base_url = helpers.random_list_choice(allrecipes_main_categories())
    print(f'Stuck! No reponse received. Using {random_base_url} as the new base url ...')
    allrecipe_spider(random_base_url)

def allrecipe_spider(base_url):
    print(f'Gathering recipes: {base_url}')
    response = proxy.perform_proxy_request(base_url, proxies, 60)
    if not response:
        reset_allrecipe_spider()
    else:
        # print('Connected ... scraping now ... ')
        parsed_html = BeautifulSoup(response.content, 'html.parser')

        base_url_links = []

        for link in parsed_html.find_all('a'):
            base_url_links.append(link)

        # Keep only URLs that contain recipes or recipe collections
        unique_urls = []

        for a in base_url_links:
            try:
                url = a['href']
                unique_urls.append(url)
                if url.startswith('https://www.allrecipes.com/recipe'):
                    unique_urls.append(url)
                # print(url)
            except:
                pass

        # Use a set to remove duplicated URLs
        unique_urls = list(set(unique_urls))

        # Separate the URLs to single and multiple recipes
        recipes = []
        collections = []

        for url in unique_urls:
            # clean = [x for x in url.split('/') if len(x) > 1]
            try:
                if 'mailto' in url \
                    or 'page=' in url \
                    or '#' in url \
                    or '/cook/' in url \
                    or 'sms:/' in url:
                    pass
                else:
                    if '/recipe/' in url:
                        recipes.append(url)
                    elif '/recipes/' in url:
                        collections.append(url)
            except:
                pass

        for r_url in recipes:
            helpers.random_wait(1, 3)
            if r_url not in visited:
                print(f'Scraping {r_url}')
                scraped = allrecipe.scrape_one_allrecipe(r_url)
                allrecipe.save_recipe_json(scraped)
                visited.append(r_url)

        for c_url in collections:
            if c_url not in visited:
                visited.append(c_url)
                allrecipe_spider(c_url)

allrecipe_spider('https://www.allrecipes.com/recipes/17562/dinner/')