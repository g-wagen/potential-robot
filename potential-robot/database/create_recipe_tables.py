import connect
import sqlalchemy

# Connect to the recipe database
recipe_db = connect.connect_to_recipes()

# Define all the needed tables for the recipe database
recipe_table_sql = \
    """
    CREATE TABLE IF NOT EXISTS recipe
    (
        recipe_id INT,
        title VARCHAR(128),
        url VARCHAR(255),
        rating DECIMAL(2,2),
        PRIMARY KEY (recipe_id)
    )
    """

directions_table_sql = \
    """
    CREATE TABLE IF NOT EXISTS directions
    (
        id INT AUTO_INCREMENT,
        recipe_id INT,
        step_num TINYINT,
        step TEXT,
        PRIMARY KEY (id),
        FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id)
    )
    """

ingredients_table_sql = \
    """
    CREATE TABLE IF NOT EXISTS ingredients
    (
        id INT AUTO_INCREMENT,
        recipe_id INT,
        amount DECIMAL(2,2),
        unit VARCHAR(32),
        ingredient VARCHAR(128),
        PRIMARY KEY (id),
        FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id)
    )
    """

notes_table_sql = \
    """
    CREATE TABLE IF NOT EXISTS notes
    (
        id INT AUTO_INCREMENT,
        recipe_id INT,
        note TEXT,
        PRIMARY KEY (id),
        FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id)
    )
    """

recipe_tables = [
    recipe_table_sql,
    ingredients_table_sql,
    directions_table_sql,
    notes_table_sql,
]

# Create all needed recipe tables
for table in recipe_tables:
    recipe_db.execute(table)

recipe_db.close()