# Allrecipes Single Recipe Scraper
# -----------------------------------------------------------------------------
# What happens here?
#
# This module will scrape exactly one recipe from allrecipes.
# First give the function scrape_one_allrecipe a recipe-url like:
#   'https://www.allrecipes.com/recipe/262048/colombian-arepas/'
# Afterwards you shall get a dictionary with al the important recipe details.
# -----------------------------------------------------------------------------

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
    try:
        title = soup.find('h1').get_text()
    except:
        title = None

    ### Info box
    try:
        info_box = {}
        info_headers_html = \
            soup.find_all('div', class_='recipe-meta-item-header')
        info_content_html = \
            soup.find_all('div', class_='recipe-meta-item-body')

        for head, content in zip(info_headers_html, info_content_html):
            head = head.get_text().replace(':', '').strip().lower()
            content = content.get_text().strip()
            info_box[head] = content
    except:
        info_box = None

    ### Ingredients
    try:
        # Define a list that will contain dictionaries for each ingredient
        ingredients_dict_list = []
        # ingredients_dict_list = [
        #     {'amount': float, 'unit': str, 'ingredient': str},
        #     {'amount': float, 'unit': str, 'ingredient': str},
        #     {'amount': float, 'unit': str, 'ingredient': str},
        #     {...}
        # ]
        # ---------------
        # Create a first ROUGH ingredients list
        ingredients_list = []
        ingredients_html = soup.find_all('li', class_='ingredients-item')
        for i, ingr in enumerate(ingredients_html):
            ingredient = ingr.get_text()
            ingr_split = ingredient.split(' ')
            ingr_split = [x for x in ingr_split if x != '' and x != ' ']
            for j, item in enumerate(ingr_split):
                try:
                    ingr_split[j] = convert_unicode_fractions(
                        item).strip().lstrip()
                except (ValueError, TypeError):
                    ingr_split[j] = item.strip().lstrip()
            ingredient = ' '.join(ingr_split)
            ingredients_list.append(ingredient)

        # Refine the ingredients list
        for ing in ingredients_list:
            # Split each ingredient 'row' when there's a space
            spl = ing.split(' ')
            # Assign some default None's
            amount = None
            unit = None
            ingredient = None

            # Try to detect if the first item is a numeric unit ...
            try:
                amount = float(spl[0])
            except ValueError:
                # ... but if not it might be an ingredient.
                ingredient = ' '.join(spl)

            # Units typically used in recipes
            units_singular = [
                'cup', 'pound', 'lb', 'ounce', 'oz', 'pint', 'pt', 'teaspoon',
                'tsp', 'tablespoon', 'tbsp', 'cube', 'g', 'gram', 'link',
                'slice', 'liter', 'l', 'dl', 'deciliter', 'kg', 'kilogram'
            ]
            # Apppend a plural s to the singular units with 3+ characters
            units_plural = [
                f'{x}s' for x in units_singular if len(x) >= 3 and x != 'tbsp'
            ]
            units = units_singular + units_plural

            # If the second element is a cooking unit (pound, tbsp,etc) ...
            # then all elements afterwards are ingredients.
            if spl[1] in units:
                unit = spl[1]
                ingredient = ' '.join(spl[2:])

            # Sometimes there's an addition to the numerical unit ...
            # in form of a container, a can, etc.
            # If there's a requirement for half a can of a certain volume, ...
            # we can simply multiply the container size by the needed amount:
            # like 0.5*(16 ounce can) = 1*(8 ounce can).
            if '(' in spl[1] and ')' in spl[2]:
                package_size = float(spl[1].replace('(', ''))
                package_unit = spl[2].replace(')', '')
                amount *= package_size
                unit = package_unit
                ingredient = ' '.join(spl[3:])

            ing_dict = {
                'amount': amount,
                'unit': unit,
                'ingredient': ingredient
            }
            ingredients_dict_list.append(ing_dict)
    except:
        ingredients_dict_list = None

    ### Rating
    try:
        # Extract the recipe rating from the source code embedded json script
        first_json_script = soup.find('script',
                                      type='application/ld+json').contents[0]
        json_file = json.loads(first_json_script)
        df = pd.json_normalize(json_file)
        recipe_rating = df['aggregateRating.ratingValue'].dropna(
        ).values.squeeze().tolist()
    except:
        recipe_rating = None

    ### Instructions
    try:
        instructions = []
        instructions_html = soup.find_all('li',
                                          class_='instructions-section-item')
        for ins in instructions_html:
            instructions.append(
                ins.find('div', class_='paragraph').get_text().strip())
    except:
        instructions = None

    ### Optional notes
    try:
        # Sometimes recipes have some notes. Let's extract them if they're present.
        notes = []
        notes_html = soup.find('div', class_='recipe-note').children
        for note in notes_html:
            try:
                notes.append(note.find('p').get_text().lstrip().rstrip())
            except AttributeError:
                pass
    except AttributeError:
        notes = None

    ### Final output dictionary
    recipe = {
        'title': title,
        'rating': recipe_rating,
        'ingredients': ingredients_dict_list,
        'steps': instructions,
        'notes': notes
    }

    return recipe
