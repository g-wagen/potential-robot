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


def grab_title(parsed_html):
    title = ''
    try:
        title = parsed_html.find('h1').get_text()
    except:
        pass

    return title

def grab_info_box(parsed_html):
    info_box = {}
    try:
        info_headers_html = \
            parsed_html.find_all('div', class_='recipe-meta-item-header')
        info_content_html = \
            parsed_html.find_all('div', class_='recipe-meta-item-body')

        for head, content in zip(info_headers_html, info_content_html):
            head = head.get_text().replace(':', '').strip().lower()
            content = content.get_text().strip()
            info_box[head] = content
    except:
        pass

    return info_box

def grab_ingredients(parsed_html):
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
        ingredients_html = parsed_html.find_all('li', class_='ingredients-item')
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

    return ingredients

def grab_rating(parsed_html):
    recipe_rating = -1
    try:
        # Extract the recipe rating from the source code embedded json script
        first_json_script = parsed_html.find(
            'script', type='application/ld+json').contents[0]
        json_file = json.loads(first_json_script)
        df = pd.json_normalize(json_file)
        recipe_rating = df['aggregateRating.ratingValue'].dropna(
        ).values.squeeze().tolist()
    except:
        pass

    return recipe_rating

def grab_instructions(parsed_html):
    instructions = []
    try:
        instructions_html = parsed_html.find_all(
            'li', class_='instructions-section-item')
        for ins in instructions_html:
            instructions.append(
                ins.find('div', class_='paragraph').get_text().strip())
    except:
        pass

    return instructions

def grab_notes(parsed_html):
    notes = []
    try:
        # Sometimes recipes have some notes. Let's extract them if they're present.
        notes_html = parsed_html.find_all('div', class_='recipe-note')
        for note in notes_html:
            try:
                notes.append(note.div.p.get_text().lstrip().rstrip())
            except AttributeError:
                pass
    except AttributeError:
        pass

    return notes

def grab_nutrition(parsed_html):
    nutrition = []
    try:
        nutrition_html = parsed_html.find_all('section', class_='nutrition-section')
        for nutri in nutrition_html:
            foo = nutri.find('div', class_='section-body').contents[0]
            nutrition.append(foo.lstrip().rstrip())
    except:
        pass

    return nutrition


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
    title = grab_title(soup)

    ### Info box
    info_box = grab_info_box(soup)

    ### Ingredients
    ingredients = grab_ingredients(soup)

    ### Rating
    recipe_rating = grab_rating(soup)

    ### Instructions
    instructions = grab_instructions(soup)

    ### Optional notes
    notes = grab_notes(soup)

    ### Nutrition
    nutrition = grab_nutrition(soup)

    ### Final output dictionary
    recipe = {
        'title': title,
        'rating': recipe_rating,
        'info': info_box,
        'ingredients': ingredients,
        'steps': instructions,
        'notes': notes,
        'nutrition': nutrition
    }

    return recipe
