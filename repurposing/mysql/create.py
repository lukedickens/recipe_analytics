from collections import OrderedDict
import mysql.connector
from mysql.connector import errorcode

# connection functionality
DB_NAME = 'recipe_substitution'


def get_connection(user=None, password=None, db_name=DB_NAME):
    cnx = mysql.connector.connect(
        user=user, password=password, host='localhost',
        database=db_name)
    return cnx


def create_database(cursor, db_name=DB_NAME):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        raise err

def use_database(cnx, cursor, db_name=DB_NAME):
    try:
        cursor.execute("USE {}".format(db_name))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(db_name))
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            print("Database {} created successfully.".format(db_name))
            cnx.database = db_name
        else:
            raise err

## creating tables order matters
TABLES = OrderedDict()
TABLES["recipes"] = """
    CREATE TABLE recipes(
        recipe_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        recipe_name VARCHAR(256),
        source TEXT,
        partof VARCHAR(64),
        lid VARCHAR(64)
    );"""
TABLES["ingredients"] = """
    CREATE TABLE ingredients(
        ingredient_id INTEGER NOT NULL AUTO_INCREMENT, ingredient_name VARCHAR(128),
        PRIMARY KEY(ingredient_id), UNIQUE(ingredient_name)
    );"""
TABLES["processed_ingredients"] = """
    CREATE TABLE processed_ingredients(
        ingredient_id INTEGER, recipe_id INTEGER,
        FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id),
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        PRIMARY KEY (ingredient_id, recipe_id)
    );"""

TABLES["ingredient_aliases"] = """
    CREATE TABLE ingredient_aliases(
        ingredient1 INTEGER, ingredient2 INTEGER, 
        PRIMARY KEY (ingredient1, ingredient2),
        FOREIGN KEY(ingredient1) REFERENCES ingredients(ingredient_id),
        FOREIGN KEY(ingredient2) REFERENCES ingredients(ingredient_id)
    );"""

TABLES["equipment"] = """
    CREATE TABLE equipment(
        equipment_id INTEGER NOT NULL AUTO_INCREMENT, equipment_name VARCHAR(128),
        PRIMARY KEY(equipment_id), UNIQUE(equipment_name)
    );"""


TABLES["constituents"] = """
    CREATE TABLE constituents(
        constituent_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        recipe_id INTEGER,
        ingredient_id INTEGER, quantity_low FLOAT, 
        quantity_high FLOAT, unit VARCHAR(32),
        text TEXT,
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id)
    );"""

TABLES["required_equipment"] = """
    CREATE TABLE required_equipment(
        required_equipment_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        recipe_id INTEGER,
        equipment_id INTEGER,
        text TEXT,
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        FOREIGN KEY(equipment_id) REFERENCES equipment(equipment_id)
    );"""

# not to be used
#TABLES["constituent_nutrients"] = """
#    CREATE TABLE constituent_nutrients(
#        constituent_id INTEGER PRIMARY KEY, 
#        fat FLOAT, nrg FLOAT, pro FLOAT, sat FLOAT, sod FLOAT, sug FLOAT);"""
TABLES["instructions"] = """
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
TABLES["information_sources"] = """
    CREATE TABLE information_sources(
        short_name VARCHAR(32) PRIMARY KEY,
        text TEXT);"""


# contexts can be one of a number of types: recipe, group or constraint.
# Universal context is a constraint based type with no constraints
TABLES["contexts"] = """
    CREATE TABLE contexts(
        context_id INTEGER PRIMARY KEY AUTO_INCREMENT,
        context_type VARCHAR(32)
    );"""

TABLES["recipe_contexts"] = """
    CREATE TABLE recipe_contexts(
        context_id INTEGER,
        recipe_id INTEGER,
        PRIMARY KEY(context_id),
        UNIQUE(recipe_id),
        FOREIGN KEY(context_id) REFERENCES contexts(context_id),
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id)
    );"""
TABLES["group_contexts"] = """
    CREATE TABLE group_contexts(
        context_id INTEGER,
        recipe_id INTEGER,
        group_source VARCHAR(32),
        PRIMARY KEY(context_id),
        FOREIGN KEY(context_id) REFERENCES contexts(context_id),
        FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
        FOREIGN KEY(group_source) REFERENCES information_sources(short_name)
    );"""
TABLES["constraint_contexts"] = """
    CREATE TABLE constraint_contexts(
        context_id INTEGER,
        constraint_source VARCHAR(32),
        constraints TEXT,
        PRIMARY KEY(context_id),
        FOREIGN KEY(context_id) REFERENCES contexts(context_id),
        FOREIGN KEY(constraint_source) REFERENCES information_sources(short_name)
    );"""


TABLES["substitutions"] = """
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
TABLES["mitigations"] = """
    CREATE TABLE mitigations(
        substitution_id INTEGER PRIMARY KEY, text TEXT,
        mitigation_source VARCHAR(32),
        FOREIGN KEY(substitution_id) REFERENCES substitutions(substitution_id),
        FOREIGN KEY(mitigation_source) REFERENCES information_sources(short_name)
    );"""
TABLES["consequences"] = """
    CREATE TABLE consequences(
        substitution_id INTEGER PRIMARY KEY,
        consequence_source VARCHAR(32),
        text TEXT,
        FOREIGN KEY(substitution_id) REFERENCES substitutions(substitution_id),
        FOREIGN KEY(consequence_source) REFERENCES information_sources(short_name)
    );"""

def create_tables(
        cnx, cursor, table_names=None, exclude_table_names=None,
        tables=TABLES, fragile=False):
    """
    tables: dictionary from table name to create sql statement
        use OrderedDict to ensure insertion order is preserved.
        tables created in order they appear in dictionary.
    """
    table_names = get_table_names_list(
        table_names, exclude_table_names)
    table_names = table_names[::-1]    
    print(f"Attempting to create table names: {table_names}")
    for table_name in table_names:
        table_description = tables[table_name]
        try:
            print("Creating table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print("Error encountered: ", err.msg)
                raise err
            if fragile:
                raise err
        else:
            print("OK")
            
def create_ingredient_counts(cnx, cursor):
    command = """
    CREATE TABLE ingredient_counts AS
        SELECT
            i.ingredient_id, i.ingredient_name, COUNT(*) AS count
          FROM ingredients AS i
            LEFT JOIN constituents AS c
              ON i.ingredient_id = c.ingredient_id
          GROUP BY i.ingredient_id;
    """
    cursor.execute(command)

def get_table_names_list(table_names, exclude_table_names=None):
#    if table_names is None:
#        # use the reverse order of the created tables
#        table_names = [key for key in TABLES.keys()][::-1]
    if type(table_names) is str:
        table_names = table_names.split(',')
    if not exclude_table_names is None:
        if type(exclude_table_names) is str:
            exclude_table_names = exclude_table_names.split(',')
        for to_exclude in exclude_table_names:
            if to_exclude in table_names:
                idx = table_names.index(to_exclude)
                table_names.pop(idx)
    return table_names
    
def drop_tables(
        cnx, cursor, table_names=None, view_names=None, exclude_table_names=None,
        fragile=True, verbose=False):
    """
    tables: dictionary from table name to create sql statement
        use OrderedDict to ensure order is preserved.
        tables dropped in reverse order they appear in dictionary.
    """
    print(f"exclude_table_names = {exclude_table_names}")
    # probably now a table
    #view_names = ['ingredient_counts']
    if view_names is None:
        view_names = []
    for view_name in view_names:
        drop_table(
            cnx, cursor, view_name, fragile=fragile, verbose=verbose,
            table_or_view='VIEW')
#        try:
#            print(f"attempting to drop view: {view_name}")
#            drop_view = f"DROP VIEW IF EXISTS {view_name}"
#            cursor.execute(drop_view)
#            cnx.commit()
#        except mysql.connector.Error as err:
#            print(f"failed to drop view {view_name} ", end="")
#            print("with error {}".format(err))
#            print("ignoring...")
#        else:
#            print("OK")

    table_names = get_table_names_list(table_names, exclude_table_names)    
    for table_name in table_names:
        drop_table(cnx, cursor, table_name, fragile=fragile, verbose=verbose)


def drop_table(
        cnx, cursor, table_name, fragile=True, verbose=False,
        table_or_view='TABLE'):
    try:
        sql_drop_table = f"DROP {table_or_view} {table_name}"
        if verbose:
            print(f"Running:\n{sql_drop_table}")
        cursor.execute(sql_drop_table)
        cnx.commit()
    except mysql.connector.Error as err:
        if verbose:
            print(f"failed to drop {table_name} ", end="")
            print("with error {}".format(err))
        if fragile:
            raise err
    else:
        if verbose:
            print("OK")


def rename_table(
        cnx, cursor, table_name_from, table_name_to,
        fragile=True, verbose=False):
    try:
        sql_rename_table = f"RENAME TABLE {table_name_from} TO {table_name_to}"
        if verbose:
            print(f"Running:\n{sql_rename_table}")
        cursor.execute(sql_rename_table)
        cnx.commit()
    except mysql.connector.Error as err:
        if verbose:
            print(f"failed to drop {table_name} ", end="")
            print("with error {}".format(err))
        if fragile:
            raise err
    else:
        if verbose:
            print("OK")

