import mysql.connector
import json

from repurposing.mysql.create import safe_create_indices

MAX_LEN_NAME = 128

sql_insert_recipe = f"""
    INSERT INTO recipes(
        recipe_name, source, partof, lid)
        VALUES(%(recipe_name)s, %(source)s, %(partof)s, %(lid)s)"""


def insert_recipes_from(
        cnx, cursor, json_recipes, batch_size=5000, fragile=True,
        partof='dataset:Recipe1M'):
    try:
        b = 0
        for json_recipe in json_recipes:
            lid = json_recipe['id']
            this_recipe = {
                'recipe_name': json_recipe['title'],
                'source': json_recipe['url'],
                'partof': partof,
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
        if fragile:
            raise     



def insert_all_recipes(cnx, cursor, ifpaths, **kwargs):
    """
    Provide a list of json filenames for recipes
    """
    print("Inserting recipes from...")
    for ifpath in ifpaths:
        print(ifpath)
        with open(ifpath,'r') as ifile:
            json_recipes = json.load(ifile)
            insert_recipes_from(
                cnx, cursor, json_recipes, **kwargs)

    # now create indices after the fact to avoid slowing inserts
    try:
        safe_create_indices(cursor, [("recipes", "recipe_name")]
#        create_recipe_name_index = \
#            "CREATE INDEX recipe_name_idx ON recipes(recipe_name)"
#        cursor.execute(create_recipe_name_index)
#        create_recipe_lid_index = \
#            "CREATE INDEX recipe_lid_idx ON recipes(lid)"
#        cursor.execute(create_recipe_name_index)
        sql_unique_recipe_lids = \
            "ALTER TABLE recipes ADD UNIQUE unique_index(partof, lid)"
        cursor.execute(sql_unique_recipe_lids)
        cnx.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))        
        raise err
        
        
def insert_ingredients_from(
        cnx, cursor, json_recipes, batch_size=5000, fragile=True):
    #
    sql_insert_ingredient = f"""
        INSERT IGNORE INTO ingredients(ingredient_name)
            VALUES(%s)"""
    try:
        b = 0
        for json_recipe in json_recipes:
            for ingr_dict in json_recipe['ingredients']:
                ingredient_name = get_ingredient_name(
                    ingr_dict)
                cursor.execute(sql_insert_ingredient, (ingredient_name,))
                b += 1
                if 'substitutions' in ingr_dict:
                    for subs_ingr_dict in ingr_dict['substitutions']:
                        ingredient_name = get_ingredient_name(
                            subs_ingr_dict)
                        cursor.execute(sql_insert_ingredient, (ingredient_name,))
                        b += 1
                if b >= batch_size:
                    cnx.commit()
                    b = 0
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        if fragile:
            raise     

def insert_all_ingredients(cnx, cursor, ifpaths, **kwargs):
    """
    Provide a list of json filenames for recipes from which to 
    insert ingredients
    """
    print(f"inserting ingredients from...")
    for ifpath in ifpaths:
        with open(ifpath,'r') as ifile:
            print(f"\t{ifpath}")
            json_recipes = json.load(ifile)
            insert_ingredients_from(
                cnx, cursor, json_recipes, **kwargs)
    try:
        sql_create_idx = """
            CREATE INDEX ingredient_name_idx 
                ON ingredients(ingredient_name)"""
        cursor.execute(sql_create_idx)
        cnx.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))        
        raise err

# not sure if we need this (truncateslong ingredients)
def get_ingredient_name(ingr_dict, max_len_name=MAX_LEN_NAME):
    if 'name' in ingr_dict:
        name = ingr_dict['name']
    else:
        name = ingr_dict['text']
    if len(name) > max_len_name:
        name = name[:max_len_name]
    return name
    
    
## constituents

SELECT_RECIPE_ID_BY_LID =  "SELECT recipe_id FROM recipes WHERE lid = %s"
SELECT_RECIPE_IDS =  "SELECT recipe_id FROM recipes WHERE partof = 'dataset:Recipe1M'"

SELECT_INGREDIENT_BY_NAME =  "SELECT ingredient_id FROM ingredients WHERE ingredient_name = %s"

ADD_CONSTITUENT = """
    INSERT IGNORE INTO constituents(recipe_id, ingredient_id, quantity_low, quantity_high, unit, text)
        VALUES(%(recipe_id)s, %(ingredient_id)s, %(quantity_low)s, %(quantity_high)s, %(unit)s, %(text)s)
    """

def get_recipe1M_id(
        cnx, cursor, recipe1M_id,
        select_recipe_id_by_lid=SELECT_RECIPE_ID_BY_LID):
    cursor.execute(select_recipe_id_by_lid, (recipe1M_id,))
    recipe_id = cursor.fetchall()[0][0]
    return recipe_id

def get_ingredient_id_by_name(
        cnx, cursor, ingr_name,
        select_ingredient_by_name=SELECT_INGREDIENT_BY_NAME):
    cursor.execute(select_ingredient_by_name, (ingr_name,))
    ingredient_id = cursor.fetchall()[0][0]
    return ingredient_id

def insert_multiple(cnx, cursor, sql_insert, values):
    for value in values:
        cursor.execute(sql_insert, value)
    cnx.commit()


#def insert_constituent(cnx, cursor, 
#    ):

def insert_constituents_from(
        cnx, cursor, json_recipes, batch_size=5000, fragile=True,
        select_recipe_id_by_lid=SELECT_RECIPE_ID_BY_LID,
        select_ingredient_by_name=SELECT_INGREDIENT_BY_NAME,
        add_constituent=ADD_CONSTITUENT, verbose=False):
    b = 0
    print("calling ", select_recipe_id_by_lid)
    print("then calling ", select_ingredient_by_name)
    try:
        for json_recipe in json_recipes:
            recipe1M_id = json_recipe['id']
            cursor.execute(select_recipe_id_by_lid, (recipe1M_id,))
            recipe_id = cursor.fetchall()[0][0]
            for ingr_dict in json_recipe['ingredients']:
                ingr_name = get_ingredient_name(
                    ingr_dict)
                cursor.execute(select_ingredient_by_name, (ingr_name,))
                try:
                    ingredient_id = cursor.fetchall()[0][0]
                except IndexError:
                    print(f"ingr_name = {ingr_name}")
                    raise
                constituent_dict = {
                    'recipe_id': recipe_id,
                    'ingredient_id': ingredient_id,
                    'unit': ingr_dict.get('unit'),
                    'text': ingr_dict['text']            
                }
                if 'numeric' in ingr_dict:
                    numeric = ingr_dict['numeric']
                    if type(numeric) in (list, tuple):
                        constituent_dict['quantity_low'] = numeric[0]
                        constituent_dict['quantity_high'] = numeric[1]
                    else:
                        constituent_dict['quantity_low'] = numeric
                        constituent_dict['quantity_high'] = numeric
                else:
                    constituent_dict['quantity_low'] = None
                    constituent_dict['quantity_high'] = None
                if verbose:
                    print(f"constituent_dict = {constituent_dict}")
                cursor.execute(add_constituent, constituent_dict)
                b += 1
                if b >= batch_size:
                    cnx.commit()
                    b = 0
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        if fragile:
            raise

def insert_all_constituents(cnx, cursor, ifpaths, **kwargs):
    """
    Provide a list of json filenames for recipes from which to 
    insert ingredients
    """
    print(f"inserting ingredients from...")
    for ifpath in ifpaths:
        with open(ifpath,'r') as ifile:
            print(f"\t{ifpath}")
            json_recipes = json.load(ifile)
            insert_constituents_from(
                cnx, cursor, json_recipes, **kwargs)
    # now create indices after the fact to avoid slowing inserts
    try:
        create_constituent_index = """
            CREATE INDEX constituent_idx
                ON constituents(recipe_id, ingredient_id)"""
        cursor.execute(create_constituent_index)
        cnx.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))        
        raise err


