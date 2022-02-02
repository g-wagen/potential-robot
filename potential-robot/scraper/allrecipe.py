# Allrecipes Single Recipe Scraper
# -----------------------------------------------------------------------------
# What happens here?
#
# This module will scrape exactly one recipe from allrecipes.
# First give the function scrape_one_allrecipe a recipe-url like:
#   'https://www.allrecipes.com/recipe/262048/colombian-arepas/'
# Afterwards you shall get a dictionary with al the important recipe details.
# -----------------------------------------------------------------------------

import string
import unicodedata
import pandas as pd
from bs4 import BeautifulSoup
import requests
import json
from utils import convert_unicode_fractions


def scrape_one_allrecipe(url: str) -> list:
    """
    Scrape exactly one recipe from Allrecipes.

    There are try-except blocks for everything in case something won't work.

    ---
    Parameters:

    `url` (str):
    Allrecipes URL in this format https://www.allrecipes.com/recipe/[0-9+]/[a-z-]+/
    """

    try:
        # Cook a tasty soup
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
    except:
        response = None
        soup = None

    ### Title
    title = ''
    try:
        title = soup.find('h1').get_text()
    except:
        pass

    ### Info box
    info_box = {}
    try:
        info_headers_html = \
            soup.find_all('div', class_='recipe-meta-item-header')
        info_content_html = \
            soup.find_all('div', class_='recipe-meta-item-body')

        for head, content in zip(info_headers_html, info_content_html):
            head = head.get_text().replace(':', '').strip().lower()
            content = content.get_text().strip()
            info_box[head] = content
    except:
        pass

    ### Ingredients
    # Define a list that will contain dictionaries for each ingredient
    ingredients = []
    try:
        # ingredients_dict_list = [
        #     {'amount': float, 'unit': str, 'ingredient': str},
        #     {'amount': float, 'unit': str, 'ingredient': str},
        #     {'amount': float, 'unit': str, 'ingredient': str},
        #     {...}
        # ]
        # ---------------
        ingredients_html = soup.find_all('li', class_='ingredients-item')
        # Grab the useful ingredients data from the <input> tag and safe myself a big headache
        for ingr in ingredients_html:
            amount = ingr.label.input['data-init-quantity']
            unit = ingr.label.input['data-unit']
            ingredient = ingr.label.input['data-ingredient']

            ing_dict = {'amount': amount,
                        'unit': unit,
                        'ingredient': ingredient}

            ingredients.append(ing_dict)
    except:
        pass

    ### Rating
    recipe_rating = -1
    try:
        # Extract the recipe rating from the source code embedded json script
        first_json_script = soup.find('script',
                                      type='application/ld+json').contents[0]
        json_file = json.loads(first_json_script)
        df = pd.json_normalize(json_file)
        recipe_rating = df['aggregateRating.ratingValue'].dropna(
        ).values.squeeze().tolist()
    except:
        pass

    ### Instructions
    instructions = []
    try:
        instructions_html = soup.find_all('li',
                                          class_='instructions-section-item')
        for ins in instructions_html:
            instructions.append(
                ins.find('div', class_='paragraph').get_text().strip())
    except:
        pass

    ### Optional notes
    notes = []
    try:
        # Sometimes recipes have some notes. Let's extract them if they're present.
        notes_html = soup.find_all('div', class_='recipe-note')
        for note in notes_html:
            try:
                notes.append(note.div.p.get_text().lstrip().rstrip())
            except AttributeError:
                pass
    except AttributeError:
        pass

    ### Nutrition
    nutrition = []
    try:
        nutrition_html = soup.find_all('section', class_='nutrition-section')
        for nutri in nutrition_html:
            foo = nutri.find('div', class_='section-body').contents[0]
            nutrition.append(foo.lstrip().rstrip())
    except:
        pass

    ### Final output dictionary
    recipe = {
        'title': title,
        'rating': recipe_rating,
        'ingredients': ingredients,
        'steps': instructions,
        'notes': notes,
        'nutrition': nutrition
    }

    return recipe

