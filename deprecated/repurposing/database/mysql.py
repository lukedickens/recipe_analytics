import mysql.connector
from mysql.connector import errorcode

def get_connection():
    cnx = mysql.connector.connect(
        user, password, host='localhost',
        database='recipe_substitution')
    return cnx


def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        raise
        
        
db_name = 'recipe_substitution'

tables = {}
tables["recipes"] = """
    CREATE TABLE recipes(
        recipe_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        recipe_name VARCHAR(256),
        source TEXT,
        partof VARCHAR(64),
        lid VARCHAR(64)
    );"""
tables["ingredients"] = """
    CREATE TABLE ingredients(
        ingredient_id INTEGER NOT NULL AUTO_INCREMENT, ingredient_name VARCHAR(128),
        PRIMARY KEY(ingredient_id), UNIQUE(ingredient_name)
    );"""
tables["processed_ingredients"] = """
    CREATE TABLE processed_ingredients(
        ingredient_id INTEGER, recipe_id INTEGER,
        FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id),
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        PRIMARY KEY (ingredient_id, recipe_id)
    );"""

tables["ingredient_aliases"] = """
    CREATE TABLE ingredient_aliases(
        ingredient1 INTEGER, ingredient2 INTEGER, 
        PRIMARY KEY (ingredient1, ingredient2),
        FOREIGN KEY(ingredient1) REFERENCES ingredients(ingredient_id),
        FOREIGN KEY(ingredient2) REFERENCES ingredients(ingredient_id)
    );"""

tables["equipment"] = """
    CREATE TABLE equipment(
        equipment_id INTEGER NOT NULL AUTO_INCREMENT, equipment_name VARCHAR(128),
        PRIMARY KEY(equipment_id), UNIQUE(equipment_name)
    );"""


tables["constituents"] = """
    CREATE TABLE constituents(
        constituent_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        recipe_id INTEGER,
        ingredient_id INTEGER, quantity_low FLOAT, 
        quantity_high FLOAT, unit VARCHAR(32),
        text TEXT,
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id)
    );"""

tables["required_equipment"] = """
    CREATE TABLE constituents(
        required_equipment_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        recipe_id INTEGER,
        equipment_id INTEGER,
        text TEXT,
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        FOREIGN KEY(equipment_id) REFERENCES equipment(equipment_id)
    );"""

# not to be used
#tables["constituent_nutrients"] = """
#    CREATE TABLE constituent_nutrients(
#        constituent_id INTEGER PRIMARY KEY, 
#        fat FLOAT, nrg FLOAT, pro FLOAT, sat FLOAT, sod FLOAT, sug FLOAT);"""
tables["instructions"] = """
    CREATE TABLE instructions(
        recipe_id INTEGER,
        step INTEGER NOT NULL,
        text TEXT,
        PRIMARY KEY (recipe_id, step),
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id));"""

# as we start to work with different information sources:
# original recipes, datasets, 3rd party inference, homegrown inference
# crowdsourced contribution, we want to keep track of where
# our information originates from.
# This table stores an id for each source, where inference is concerned
# we may need to keep track of what inference, where crowdsourcing
# contributions are concerned we may want to keep track of contributors
tables["information_sources"] = """
    CREATE TABLE information_sources(
        short_name VARCHAR(32) PRIMARY KEY,
        text TEXT);"""


# contexts can be one of a number of types: recipe, group or constraint.
# Universal context is a constraint based type with no constraints
tables["contexts"] = """
    CREATE TABLE contexts(
        context_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        context_type VARCHAR(32)
    );"""

tables["recipe_contexts"] = """
    CREATE TABLE recipe_contexts(
        context_id INTEGER,
        recipe_id INTEGER,
        PRIMARY KEY(context_id),
        UNIQUE(recipe_id),
        FOREIGN KEY(context_id) REFERENCES contexts(context_id),
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id)
    );"""
tables["group_contexts"] = """
    CREATE TABLE group_contexts(
        context_id INTEGER,
        recipe_id INTEGER,
        group_source VARCHAR(32),
        PRIMARY KEY(context_id),
        FOREIGN KEY(context_id) REFERENCES contexts(context_id),
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        FOREIGN KEY(group_source) REFERENCES information_sources(short_name)
    );"""
tables["constraint_contexts"] = """
    CREATE TABLE constraint_contexts(
        context_id INTEGER,
        constraint_source VARCHAR(32),
        constraints TEXT,
        PRIMARY KEY(context_id),
        FOREIGN KEY(context_id) REFERENCES contexts(context_id),
        FOREIGN KEY(constraint_source) REFERENCES information_sources(short_name)
    );"""


tables["substitutions"] = """
    CREATE TABLE substitutions(
        substitution_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        substitution_source VARCHAR(32),
        context_id INTEGER,
        quantity_sub_for FLOAT,
        unit_sub_for VARCHAR(32),
        ingredient_sub_for INTEGER,
        quantity_sub_with FLOAT,
        unit_sub_with VARCHAR(32),
        ingredient_sub_with INTEGER,
        UNIQUE(context_id, ingredient_sub_for, ingredient_sub_with),
        FOREIGN KEY(substitution_source) REFERENCES information_sources(short_name),
        FOREIGN KEY(context_id) REFERENCES contexts(context_id),
        FOREIGN KEY(ingredient_sub_for) REFERENCES ingredients(ingredient_id),
        FOREIGN KEY(ingredient_sub_with) REFERENCES ingredients(ingredient_id)
    );"""
tables["mitigations"] = """
    CREATE TABLE mitigations(
        substitution_id INTEGER PRIMARY KEY, text TEXT,
        mitigation_source VARCHAR(32),
        FOREIGN KEY(substitution_id) REFERENCES substitutions(substitution_id),
        FOREIGN KEY(mitigation_source) REFERENCES information_sources(short_name)
    );"""
tables["consequences"] = """
    CREATE TABLE consequences(
        substitution_id INTEGER PRIMARY KEY,
        consequence_source VARCHAR(32),
        text TEXT,
        FOREIGN KEY(substitution_id) REFERENCES substitutions(substitution_id),
        FOREIGN KEY(consequence_source) REFERENCES information_sources(short_name)
    );"""


def create_tables(tables):
    cnx = get_connection()
    cursor = cnx.cursor()  
    try:
        cursor.execute("USE {}".format(db_name))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(db_name))
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            print("Database {} created successfully.".format(db_name))
            cnx.database = DB_NAME
        else:
            print(err)
            raise
    for table_name in tables.keys():
        table_description = tables[table_name]
        try:
            print("Creating table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("OK")
            
def insert_recipes_into_db(recipe_data, batch_size=5000):
    # now insert_recipes_into_db
    cnx = get_connection()
    cursor = cnx.cursor()
    
    # TODO: attempt to delete index first

    sql_insert_recipe = f"""
        INSERT INTO recipes(
            recipe_name, source, partof, lid)
            VALUES(%(recipe_name)s, %(source)s, %(partof)s, %(lid)s)"""
    create_recipe_name_index = \
        "CREATE INDEX recipe_name_idx ON recipes(recipe_name)"
    b = 0
    try:
        for json_recipe in recipe_data:
            lid = json_recipe['id']
            #lid_to_recipe[json_recipe['id']] = json_recipe
            this_recipe = {
                'recipe_name': json_recipe['title'],
                'source': json_recipe['url'],
                'partof': 'dataset:Recipe1M',
                'lid': lid
            }
            cursor.execute(sql_insert_recipe, this_recipe)
            b += 1
            if b >= batch_size:
                # Make sure data is committed to the database
                cnx.commit()
                b = 0
        cnx.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))        

    try:
        cursor.execute(create_recipe_name_index)
        create_recipe_name_index = "CREATE INDEX recipe_lid_idx ON recipes(lid)"
        cursor.execute(create_recipe_name_index)
        #create_recipe_partof_index = "CREATE INDEX recipe_partof_idx ON recipes(partof)"
        #cursor.execute(create_recipe_partof_index)
        cnx.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))        
    cursor.close()
    cnx.close()
