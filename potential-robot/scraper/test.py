from tkinter import INSERT
from urllib import response
from wsgiref import headers
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
import numpy as np

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


def recipe_exists(recipe):
    engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'),
                                      isolation_level='AUTOCOMMIT')
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

    engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'),
                                      isolation_level='AUTOCOMMIT')
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


def clear_tables(connection):
    """Function clears all tables you give it.
    USE JUST FOR TESTING OR RISK WIPING EVERYTHING!"""
    for t in ['notes', 'recipe', 'steps', 'nutrition', 'recipe_info',
              'ingredients', 'recipe_ingredients']:
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


def sanitize_quotes(input_str):
    return input_str.replace("'", "").replace('"', '')


def get_table_columns(connection, table):
    # ', '.join([f'"{x}"' for x in ['col1', 'col2', 'col3']])
    cols = list(
        pd.read_sql(f'SELECT * FROM {table} WHERE 1=2;', connection).columns)
    cols = ', '.join([f'"{x}"' for x in cols])
    return cols


def clear_all_tables():
    engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'),
                                      isolation_level='AUTOCOMMIT')
    # bitio_repo = os.environ.get('BIT_REPO')
    with engine.connect() as conn:
        ##### Clear tables
        clear_tables(conn)

def sql_string_type_fix(items):
    quotes_if_needed = [x if type(x) == type(1) or type(x) == type(1.1) else f"'{x}'" for x in items]
    sql_values_string = f"({', '.join([str(x) for x in quotes_if_needed])})"
    return sql_values_string

def sql_table_columns(column_names):
    return ', '.join([f'"{x}"' for x in column_names])

def recipe_to_table(connection, table, **recipe):
    recipe_id = auto_increment(connection, table)  # Recipe ID
    title = recipe.get('title')
    url = recipe.get('url')
    rating = recipe.get('rating')
    md5_hash = recipe.get('md5')

    columns = sql_table_columns(['id', 'name', 'url', 'rating', 'hash'])
    recipe_old_vals = [recipe_id, sanitize_quotes(title), url, rating, md5_hash]

    # Build recipe SQL
    recipe_vals = sql_string_type_fix(recipe_old_vals)
    if recipe_vals:
        recipe_row_sql_str = f'INSERT INTO {table} ({columns}) VALUES ({recipe_vals});'
        # EXECUTE recipe SQL
        recipe_sql = sqlalchemy.text(recipe_row_sql_str)
        connection.execute(recipe_sql)
    return recipe_id

def steps_to_table(connection, table, recipe_id, **recipe):
    steps = recipe.get('steps')

    columns = sql_table_columns(['recipe_id', 'step_num', 'step'])

    # Build steps SQL
    step_vals = []
    for s, step in enumerate(steps, 1):
        old_row = [recipe_id, s, sanitize_quotes(step)]
        step_vals.append(sql_string_type_fix(old_row))

    step_vals = f"{', '.join([str(x) for x in step_vals])}"
    if step_vals:
        notes_sql_str = f'INSERT INTO {table} ({columns}) VALUES {step_vals};'

        # EXECUTE steps SQL
        notes_sql = sqlalchemy.text(notes_sql_str)
        connection.execute(notes_sql)

def notes_to_table(connection, table, recipe_id, **recipe):
    notes_data = recipe.get('notes')
    columns = sql_table_columns(['recipe_id', 'note_num', 'note'])

    # Build notes SQL
    notes_values = []
    for n, note in enumerate(notes_data, 1):
        old_row = [recipe_id, n, sanitize_quotes(note)]
        notes_values.append(sql_string_type_fix(old_row))

    notes_values = f"{', '.join([str(x) for x in notes_values])}"
    if notes_values:
        notes_sql_str = f'INSERT INTO {table} ({columns}) VALUES {notes_values};'
        # EXECUTE notes SQL
        notes_sql = sqlalchemy.text(notes_sql_str)
        connection.execute(notes_sql)

def recipe_info_to_table(connection, table, recipe_id, **recipe):
    info_data = recipe.get('info')
    info_table_cols = ['"recipe_id"'] + [f'"{x}"' for x in
                                         list(info_data.keys())]
    info_table_values = [recipe_id] + [f"'{sanitize_quotes(x)}'" for x in
                                       list(info_data.values())]
    info_table_cols = f"{', '.join([str(x) for x in info_table_cols])}"
    info_table_values = f"{', '.join([str(x) for x in info_table_values])}"
    if info_table_values:
        recipe_info_sql_str = f'INSERT INTO {table} ({info_table_cols}) VALUES ({info_table_values});'
        recipe_info_sql = sqlalchemy.text(recipe_info_sql_str)
        connection.execute(recipe_info_sql)

def ingredients_to_table(connection, table, **recipe):
    ingredients_data = recipe.get('ingredients')
    columns = sql_table_columns(['id', 'name'])
    ingredients_list = [x['ingredient'] for x in ingredients_data]

    # Get a list of all the existing ingredients
    existing_ingredients_sql = f'SELECT "name" FROM {table};'
    existing_ingredients_df = pd.read_sql(existing_ingredients_sql, connection)
    existing_ingredients = existing_ingredients_df.name.values

    # Figure out which ingredients aren't in the table yet
    new_ingredients = np.setdiff1d(ingredients_list, existing_ingredients)

    # Construct the SQL statement to INSERT all rows into the table at once
    ingr_values = []
    ingredient_id = auto_increment(connection, table)
    for ing in new_ingredients:
        old_row = [ingredient_id, sanitize_quotes(ing)]
        ingr_values.append(sql_string_type_fix(old_row))
        ingredient_id += 1

    ingr_values = f"{', '.join([str(x) for x in ingr_values])}"

    if ingr_values:
        # Finally RUN the SQL statement
        sql_str = f'INSERT INTO {table} ({columns}) VALUES {ingr_values};'
        connection.execute(sqlalchemy.text(sql_str))

def recipe_ingredients_to_table(connection, rcp_ingr_table, ingr_table, recipe_id, **recipe):
    ingredients_data = recipe.get('ingredients')
    columns = sql_table_columns(['recipe_id', 'ingredient_id', 'unit', 'amount'])

    recipe_ingredients_df = pd.DataFrame.from_dict(ingredients_data)

    recipe_ingredients_df['amount'] = recipe_ingredients_df['amount'].apply(
        pd.to_numeric)
    recipe_ingredients_df = recipe_ingredients_df.groupby(
        ['ingredient', 'unit']).sum().reset_index()
    recipe_ingredients_df['ingredient'] = recipe_ingredients_df[
        'ingredient'].apply(sanitize_quotes)
    existing_ingredients_df = pd.read_sql(
        f'SELECT * FROM {ingr_table};', connection)

    merged_df = pd.merge(existing_ingredients_df, recipe_ingredients_df,
                         how='left', left_on='name', right_on='ingredient')

    merged_df.dropna(inplace=True)
    merged_df['recipe_id'] = recipe_id
    ingredient_ids = merged_df['id']
    ingredient_unit = merged_df['unit']
    ingredient_amount = merged_df['amount']
    recipe_ingr_values = []
    for _id, _unit, _amount in zip(ingredient_ids, ingredient_unit,
                                   ingredient_amount):
        recipe_ingr_values.append(
            f"({recipe_id}, {_id}, '{_unit}', {_amount})")
    recipe_ingr_values = ', '.join([x for x in recipe_ingr_values])
    if recipe_ingr_values:
        sql_str = f'INSERT INTO {rcp_ingr_table} ({columns}) VALUES {recipe_ingr_values};'
        connection.execute(sqlalchemy.text(sql_str))

def nutrition_to_table(connection, table, recipe_id, **recipe):
    nutrition_data = recipe.get('nutrition')
    try:
        nutrition_data = nutrition_data[0].lower()
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

        nutrition_table_cols = ', '.join(
            [f'"{x}"' for x in nutrition_table_cols])
        nutrition_table_values = ', '.join(
            [f"'{x}'" for x in nutrition_table_values])
        if nutrition_table_values:
            nutrition_sql_str = f'INSERT INTO {table} ({nutrition_table_cols}) VALUES ({nutrition_table_values});'
            nutrition_sql = sqlalchemy.text(nutrition_sql_str)
            connection.execute(nutrition_sql)
    except IndexError:
        pass

def add_recipe(recipe):
    engine = sqlalchemy.create_engine(os.environ.get('BIT_CON'),
                                      isolation_level='AUTOCOMMIT')
    bitio_repo = os.environ.get('BIT_REPO')

    tables = {'recipe': 'recipe',
              'steps': 'steps',
              'notes': 'notes',
              'info': 'recipe_info',
              'nutri': 'nutrition',
              'ingr': 'ingredients',
              'reci_ingr': 'recipe_ingredients'}

    title = recipe.get('title')
    url = recipe.get('url')
    rating = recipe.get('rating')
    md5_hash = recipe.get('md5')
    steps = recipe.get('steps')
    notes_data = recipe.get('notes')
    info_data = recipe.get('info')
    nutrition_data = recipe.get('nutrition')
    ingredients_data = recipe.get('ingredients')

    # Check if the recipe has essential data and abort if it doesn't
    if rating < 0 or not ingredients_data or not steps:
        print(f'Skipping {title}')
    else:
        print(f'Adding {title}')
        with engine.connect() as conn:
            # TODO: 1. This code is horrible. A lot of stuff repeats here.

            # Tables
            recipe_table = f'"{bitio_repo}"."{tables.get("recipe")}"'  # Recipes
            recipe_info_table = f'"{bitio_repo}"."{tables.get("info")}"'  # Recipe Info
            steps_table = f'"{bitio_repo}"."{tables.get("steps")}"'  # Steps
            notes_table = f'"{bitio_repo}"."{tables.get("notes")}"'  # Notes
            nutrition_table = f'"{bitio_repo}"."{tables.get("nutri")}"'  # Nutrition
            ingredients_table = f'"{bitio_repo}"."{tables.get("ingr")}"'  # Ingredients
            recipe_ingredients_table = f'"{bitio_repo}"."{tables.get("reci_ingr")}"'  # Recipe Ingredients

            # ---------------------------------------------------------------------
            # Recipe table
            recipe_id = recipe_to_table(conn, recipe_table, **recipe)

            # Steps table
            steps_to_table(conn, steps_table, recipe_id, **recipe)

            # Notes table
            notes_to_table(conn, notes_table, recipe_id, **recipe)

            # Recipe Info table
            recipe_info_to_table(conn, recipe_info_table, recipe_id, **recipe)

            # Nutrition table
            nutrition_to_table(conn, nutrition_table, recipe_id, **recipe)

            # Ingredients table
            ingredients_to_table(conn, ingredients_table, **recipe)

            # Recipe Ingredients table
            recipe_ingredients_to_table(conn, recipe_ingredients_table, ingredients_table, recipe_id, **recipe)


# # Add a recipe to the database
# url = 'https://www.allrecipes.com/recipe/269274/pavlova-with-winter-fruits/'
# recipe = allrecipe.scrape_one_allrecipe(url)
# clear_all_tables()

recipe_path = os.path.join('..', '..', 'temp1')
num_recipes = len(os.listdir(recipe_path))
for i, item in enumerate(os.listdir(recipe_path), 1):
    recipe_json = os.path.join(recipe_path, item)
    print(i, '/', num_recipes, '-', recipe_json)
    with open(recipe_json, 'r') as r:
        add_recipe(json.load(r))
#     print(recipe_json)


# with open('/mnt/data_projects/potential-robot/temp/3_cheese_enchiladas.json', 'r') as r:
#     add_recipe(json.load(r))
# with open('/mnt/data_projects/potential-robot/temp/3ingredient_peanut_butter_cookies.json', 'r') as r:
#     add_recipe(json.load(r))



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


# url = 'https://www.allrecipes.com/recipe/26661/stuffed-cabbage-rolls/'
# url = 'https://www.allrecipes.com/recipe/132833/guluptsie-cabbage-rolls/'
# url = 'https://www.allrecipes.com/recipe/216878/koulibiaka/'
