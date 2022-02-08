from urllib import response
import requests
from bs4 import BeautifulSoup
from proxy import random_header
import sqlalchemy, psycopg2
import os
import dotenv
import pandas as pd
import allrecipe
import json
import string

dotenv.load_dotenv()

# def allrecipes_exists(url):
#     response = requests.get(url, headers=random_header())
#     return False if response.status_code > 399 else True


# print(allrecipes_exists('https://www.allrecipes.com/'))

# engine = sqlalchemy.create_engine(os.environ['BIT_CON'], isolation_level='AUTOCOMMIT')
# select_all_recipe = 'SELECT * FROM "betonk/potential-robot"."recipe";'
# select_all_ingredients = 'SELECT * FROM "betonk/potential-robot"."ingredients";'
# data = pd.read_sql(query, engine)
# print(data.id.count())


def auto_increment_bitio_column(table):
    """
    Bit.io has no auto incrementing column datatype. This is sad.
    This function tries to auto increment by counting existing rows and
    add 1 to the current count.

    table can be any table that exists."""

    # Bit.io wants us to use this particular isolation_level when connecting
    engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'),
                                      isolation_level='AUTOCOMMIT')
    bitio_repo = os.environ.get('BIT_REPO')

    # Count the rows (probably slow as hell but let's just use it for now)
    with engine.connect() as conn:
        select_all = f'SELECT * FROM "{bitio_repo}"."{table}";'
        data = pd.read_sql(select_all, conn)
        current_count = data.shape[0]

    return current_count + 1

# print(auto_increment_bitio_column('recipe'))


# with engine.connect() as conn:
#     result = conn.execute('SELECT * FROM "betonk/potential-robot"."recipe";')
#     for row in result:
#         print(row)



def recipe_add(recipe):
    bitio_repo = os.environ.get('BIT_REPO')
    title = recipe.get('title')
    url = recipe.get('url')
    rating = recipe.get('rating')
    hash = recipe.get('md5')
    recipe_table = 'recipe'
    increment = auto_increment_bitio_column('recipe')
    engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'), isolation_level='AUTOCOMMIT')
    with engine.connect() as conn:
        # recipe table
        sql_statement = f'INSERT INTO "{bitio_repo}"."{recipe_table}" (id, name, url, rating, hash) VALUES ({increment}, \'{title}\', \'{url}\', {rating}, \'{hash}\');'
        sql_statement = sqlalchemy.text(sql_statement)
        conn.execute(sql_statement)

    return increment

def recipe_exists(recipe):
    engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'), isolation_level='AUTOCOMMIT')
    bitio_repo = os.environ.get('BIT_REPO')
    url = recipe.get('url')
    url_column = 'url'
    recipe_table = 'recipe'

    with engine.connect() as conn:
        select_urls = f'SELECT "{url_column}" FROM "{bitio_repo}"."{recipe_table}" WHERE "{url_column}" LIKE \'{url}\';'
        urls = pd.read_sql(select_urls, conn)
        recipe_exists = True if urls.shape[0] > 0 else False
    return recipe_exists

def recipe_changed(recipe):
    new_hash = recipe.get('md5')
    old_hash = None

    engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'), isolation_level='AUTOCOMMIT')
    bitio_repo = os.environ.get('BIT_REPO')

    url = recipe.get('url')
    url_column = 'url'
    hash_column = 'hash'
    recipe_table = 'recipe'

    with engine.connect() as conn:
        select_hash = f'SELECT "{hash_column}" FROM "{bitio_repo}"."{recipe_table}" WHERE "{url_column}" LIKE \'{url}\';'
        old_hash = pd.read_sql(select_hash, conn)
        old_hash = old_hash.values[0]

    return new_hash != old_hash




def truncate(connection):
    """Function clears all tables you give it.
    USE JUST FOR TESTING OR RISK WIPING EVERYTHING!"""
    for t in ['notes', 'recipe', 'steps', 'nutrition', 'recipe_info', 'nutrition']:
        sql_statement = f'TRUNCATE TABLE "betonk/potential-robot"."{t}";'
        connection.execute(sqlalchemy.text(sql_statement))

def auto_increment(connection, table):
    """Bit.io has no auto incrementing column datatype. This is sad.
    This function tries to auto increment by counting existing rows and
    add 1 to the current count.
    table can be any table that exists."""
    select_all = f'SELECT * FROM {table};'
    data = pd.read_sql(select_all, connection)
    cur_cnt = data.shape[0]
    increment = cur_cnt + 1
    return increment

def add_recipe(recipe):
    engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'), isolation_level='AUTOCOMMIT')
    bitio_repo = os.environ.get('BIT_REPO')

    tables = {'recipe': 'recipe',
           'steps': 'steps',
           'notes': 'notes',
           'info': 'recipe_info',
           'nutri': 'nutrition'}

    with engine.connect() as conn:
        # TODO: This function is getting a bit too big.
        # TODO: Separate all these code blocks into functions.
        ##### Clear tables
        truncate(conn)

        ##### Tables
        recipe_table = f'"{bitio_repo}"."{tables.get("recipe")}"' # Recipes
        recipe_info_table = f'"{bitio_repo}"."{tables.get("info")}"' # Recipe Info
        steps_table = f'"{bitio_repo}"."{tables.get("steps")}"' # Steps
        notes_table = f'"{bitio_repo}"."{tables.get("notes")}"' # Notes
        nutrition_table = f'"{bitio_repo}"."{tables.get("nutri")}"' # Nutrition

        # ---------------------------------------------------------------------
        ##### Recipe table
        title = recipe.get('title')
        url = recipe.get('url')
        rating = recipe.get('rating')
        hash = recipe.get('md5')
        recipe_id = auto_increment(conn, recipe_table) # Recipe ID
        recipe_cols = ['id', 'name', 'url', 'rating', 'hash']
        recipe_old_vals = [recipe_id, title, url, rating, hash]

        # Build recipe SQL
        rcp_vals = [x if type(x) == type(1) or type(x) == type(1.1) else f"'{x}'" for x in recipe_old_vals]
        recipe_cols = f"{', '.join([str(x) for x in recipe_cols])}"
        rcp_vals = f"{', '.join([str(x) for x in rcp_vals])}"
        recipe_row_sql_str = f'INSERT INTO {recipe_table} ({recipe_cols}) VALUES ({rcp_vals});'

        # EXECUTE recipe SQL
        recipe_sql = sqlalchemy.text(recipe_row_sql_str)
        conn.execute(recipe_sql)

        # ---------------------------------------------------------------------
        ##### Steps table
        steps = recipe.get('steps')
        step_cols = ['recipe_id', 'step_num', 'step']

        # Build steps SQL
        step_vals = []
        for s, step in enumerate(steps, 1):
            old_row = [recipe_id, s, step]
            row = [x if type(x) == type(1) or type(x) == type(1.1) else f"'{x}'" for x in old_row]
            row = f"({', '.join([str(x) for x in row])})"
            step_vals.append(row)
        step_cols = f"{', '.join([str(x) for x in step_cols])}"
        step_vals = f"{', '.join([str(x) for x in step_vals])}"
        if step_vals:
            notes_sql_str = f'INSERT INTO {steps_table} ({step_cols}) VALUES {step_vals};'

            # EXECUTE steps SQL
            notes_sql = sqlalchemy.text(notes_sql_str)
            conn.execute(notes_sql)

        # ---------------------------------------------------------------------
        ##### Notes table
        notes_data = recipe.get('notes')
        notes_table_cols = ['recipe_id', 'note_num', 'note']

        # Build notes SQL
        notes_values = []
        for n, note in enumerate(notes_data, 1):
            old_row = [recipe_id, n, note]
            row = [x if type(x) == type(1) or type(x) == type(1.1) else f"'{x}'" for x in old_row]
            row = f"({', '.join([str(x) for x in row])})"
            notes_values.append(row)
        notes_table_cols = f"{', '.join([str(x) for x in notes_table_cols])}"
        notes_values = f"{', '.join([str(x) for x in notes_values])}"
        if notes_values:
            notes_sql_str = f'INSERT INTO {notes_table} ({notes_table_cols}) VALUES {notes_values};'
            # EXECUTE notes SQL
            notes_sql = sqlalchemy.text(notes_sql_str)
            conn.execute(notes_sql)

        # ---------------------------------------------------------------------
        ##### Recipe Info table
        info_data = recipe.get('info')
        info_table_cols = ['"recipe_id"'] + [f'"{x}"' for x in list(info_data.keys())]
        info_table_values = [recipe_id] + [f"'{x}'" for x in list(info_data.values())]
        info_table_cols = f"{', '.join([str(x) for x in info_table_cols])}"
        info_table_values = f"{', '.join([str(x) for x in info_table_values])}"
        if info_table_values:
            recipe_info_sql_str = f'INSERT INTO {recipe_info_table} ({info_table_cols}) VALUES ({info_table_values});'
            recipe_info_sql = sqlalchemy.text(recipe_info_sql_str)
            conn.execute(recipe_info_sql)

        # ---------------------------------------------------------------------
        ##### Nutrition table
        nutrition_data = recipe.get('nutrition')[0].lower()
        nutrition_table_cols = ['recipe_id']
        nutrition_table_values = [recipe_id]

        # TODO: I feel like this type of processing should happen at the scraper level...
        # Split the macro nutrient groups at ';'
        components = [x.lstrip().rstrip() for x in nutrition_data.split(';')]
        for comp in components:
            col = None
            val = None
            # Split the nutrient unit from the amount
            parts = comp.split(' ')
            # Check which part of the split is the nutrient unit
            for par in parts:
                checkr = []
                for p in par:
                    # A purely lowercase string will be out nutrient
                    if p in string.ascii_lowercase:
                        checkr.append(True)
                    # A mixed string will be our amount
                    else:
                        checkr.append(False)
                # Check if all list items are True...
                if all(checkr):
                    # ... and add to our columns
                    col = par
                # When some items are False we got our value.
                else:
                    # In case there's a weird dot at the end
                    if par[-1] in string.punctuation:
                        par = par[:-1]
                    val = par
            nutrition_table_cols.append(col)
            nutrition_table_values.append(val)

        nutrition_table_cols = ', '.join([f'"{x}"' for x in nutrition_table_cols])
        nutrition_table_values = ', '.join([f"'{x}'" for x in nutrition_table_values])
        if nutrition_table_values:
            nutrition_sql_str = f'INSERT INTO {nutrition_table} ({nutrition_table_cols}) VALUES ({nutrition_table_values});'
            nutrition_sql = sqlalchemy.text(nutrition_sql_str)
            conn.execute(nutrition_sql)





# ALTER TABLE "betonk/potential-robot"."nutrition"
# ALTER COLUMN "calories" TYPE VARCHAR(16),
# ALTER COLUMN "protein" TYPE VARCHAR(16),
# ALTER COLUMN "carbohydrates" TYPE VARCHAR(16),
# ALTER COLUMN "fat" TYPE VARCHAR(16),
# ALTER COLUMN "cholesterol" TYPE VARCHAR(16),
# ALTER COLUMN "sodium" TYPE VARCHAR(16);


# TRUNCATE TABLE "betonk/potential-robot"."notes";
# TRUNCATE TABLE "betonk/potential-robot"."recipe";
# TRUNCATE TABLE "betonk/potential-robot"."steps";


# def truncate_tables():



# def recipe_update(recipe):
#     engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'),
#                                       isolation_level='AUTOCOMMIT')
#     bitio_repo = os.environ.get('BIT_REPO')

#     with engine.connect() as conn:
#         select_hash = f'UPDATE "{bitio_repo}"."{recipe_table}" SET ... = ... WHERE ... = ... ;'

url = 'https://www.allrecipes.com/recipe/26661/stuffed-cabbage-rolls/'
# url = 'https://www.allrecipes.com/recipe/132833/guluptsie-cabbage-rolls/'
# url = 'https://www.allrecipes.com/recipe/216878/koulibiaka/'
recipe = allrecipe.scrape_one_allrecipe(url)

# if not recipe_exists(recipe):# or (recipe_exists(recipe) and recipe_changed(recipe)):
    # recipe_id = recipe_add(recipe)
    # steps_add(recipe, recipe_id)
add_recipe(recipe)
    # notes_add(recipe, recipe_id)
# elif :
    # recipe_add(recipe)
# recipe_add(recipe)
# if recipe_exists(recipe):
#     print('exists')
# if recipe_changed(recipe):
#     print('changed')
# print('recipe added?')
# current_ingredients = SELECT * FROM

# for ing in recipe.get('ingredients'):
#     name = ing.get('ingredient')


# increment_ids =

### Tables
# 'title': grab_title(soup),
# 'url': url,
# 'rating': grab_rating(soup),
# 'info': grab_info_box(soup),
# 'nutrition': grab_nutrition(soup),
# 'ingredients': grab_ingredients(soup),
# 'steps': grab_instructions(soup),
# 'notes': grab_notes(soup),

# recipe: id, title, url, rating
# recipe_info: recipe_id, prep, cook, additional, total, servings, yield
# ingredients: id, name
# recipe_ingredients: recipe_id, ingredient_id, unit, amount
# steps: recipe_id, step_num, step
# notes: recipe_id, note
# nutrition: recipe_id, contents


# info_list = []

# rec_dir = r'/mnt/data_projects/potential-robot/temp'
# os.curdir = rec_dir
# jsons = os.listdir(rec_dir)

# for i, js in enumerate(jsons):
#     with open(os.path.join(rec_dir, js), 'r') as j:
#         recipe = json.load(j)
#         info = recipe.get('info')
#         try:
#             for k in info.keys():
#                 info_list.append(k)
#         except:
#             pass
#     print(i+1)

# uniques = list(set(info_list))
# print(uniques)


# nutri_list = []
# import string

# only_chars = string.ascii_lowercase

# rec_dir = r'/mnt/data_projects/potential-robot/temp'
# os.curdir = rec_dir
# jsons = os.listdir(rec_dir)

# for i, js in enumerate(jsons):
#     with open(os.path.join(rec_dir, js), 'r') as j:
#         recipe = json.load(j)
#         try:
#             info = recipe.get('nutrition')[0].lower()
#             # Split the macro nutrient groups at ';'
#             components = [x.lstrip().rstrip() for x in info.split(';')]
#             for comp in components:
#                 unit = None
#                 # Split the nutrient unit from the amount
#                 parts = comp.split(' ')
#                 # Check which part of the split is the nutrient unit
#                 for par in parts:
#                     checkr = []
#                     for p in par:
#                         if p in only_chars:
#                             checkr.append(True)
#                         else:
#                             checkr.append(False)
#                     if all(checkr):
#                         unit = par
#                 nutri_list.append(unit)



#             # for k in info.keys():
#             #     nutri_list.append(k)
#         except:
#             pass
#     print(i+1)

# uniques = list(set(nutri_list))
# print(uniques)

# for un in uniques:
#     print(un, nutri_list.count(un))
