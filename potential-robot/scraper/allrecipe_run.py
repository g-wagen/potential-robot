from bs4 import BeautifulSoup
import time
import proxy
from allrecipe import save_recipe_json, scrape_one_allrecipe

# Grab the proxies
pickled_proxies = 'proxies.pickle'
proxies = proxy.pickler(pickled_proxies)

visited = []

# TODO: Try incorporating pagination!

def allrecipe_spider(base_url):
    # default_pages = [
    #     'https://www.allrecipes.com/recipes/80/main-dish/',
    #     'https://www.allrecipes.com/recipes/78/breakfast-and-brunch/'
    # ]
    print(f'Base URL: {base_url}')
    response = proxy.perform_proxy_request(base_url, proxies)
    if not response:
        # TODO: MAKE THIS RESET LOGIC SMARTER
        print('No reponse received. Reset to another page')
        allrecipe_spider('https://www.allrecipes.com/recipes/')
    else:
        print('Connected ... scraping now ... ')
        parsed_html = BeautifulSoup(response.content, 'html.parser')
        base_url_links = parsed_html.find_all('a')#, class_='card__titleLink')

        # Keep only URLs that contain recipes or recipe collections
        unique_urls = []

        for a in base_url_links:
            try:
                url = a['href']
                unique_urls.append(url)
                if url.startswith('https://www.allrecipes.com/recipe'):
                    unique_urls.append(url)
                print(url)
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
            proxy.random_wait(1, 3)
            print(r_url)
            if r_url not in visited:
                scraped = scrape_one_allrecipe(r_url)
                save_recipe_json(scraped)
                visited.append(r_url)

        for c_url in collections:
            if c_url not in visited:
                visited.append(c_url)
                allrecipe_spider(c_url)

allrecipe_spider('https://www.allrecipes.com')
