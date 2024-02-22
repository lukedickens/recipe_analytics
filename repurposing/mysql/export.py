import mysql.connector
from mysql.connector import errorcode
import json
import numpy as np



from repurposing.mysql.filter import get_table_count
from repurposing.file_io.paths import get_jsonpath
def export_recipes_to_json(
        cnx, cursor, recipes_table, ingredients_table, constituents_table,
        include_title=True, include_id=False, include_ingredients=True,
        include_constituents=False, title_key='title',
        ingredients_key='ingredients', constituents_key='ingredients',
        batch_size=5000, verbose=False, json_fname=None,
        exportdir=None):
    fields = ['recipe_id']
    if include_title:
        fields.append('recipe_name')
        title_index = fields.index('recipe_name')
    num_recipes = get_table_count(cnx, cursor, recipes_table)
    template_select_recipe = f"""
        SELECT {','.join(fields)} FROM {recipes_table} LIMIT %d,%d"""
    template_select_ingredients = f"""
        SELECT i.ingredient_name FROM {ingredients_table} AS i
            INNER JOIN {constituents_table} AS c
                ON i.ingredient_id = c.ingredient_id WHERE c.recipe_id = %d"""
    if include_constituents:
        raise ValueError(
            'No current way to include constituents')
    to_export = []
    for starting_at in range(0,num_recipes,batch_size):
        sql_select_recipe = template_select_recipe % (starting_at, batch_size)
        if verbose:
            print(f"executing:\n{sql_select_recipe}")
        cursor.execute(sql_select_recipe)
        for row in cursor.fetchall():
            recipe_dict = {}
            recipe_id = int(row[0])
            if include_title:
                recipe_dict[title_key] = row[title_index]
            if include_ingredients:
                sql_select_ingredients = template_select_ingredients % (recipe_id,)
                if verbose:
                    print(f"executing:\n{sql_select_ingredients}")
                cursor.execute(sql_select_ingredients)
                recipe_dict[ingredients_key] = [
                    r[0] for r in cursor.fetchall() ]
            to_export.append(recipe_dict)
    # now save all to one json file
    #TODO allow function to save to multiple files            
    if json_fname is None:
        nr = get_table_count(cnx, cursor, recipes_table)
        ni = get_table_count(cnx, cursor, ingredients_table)
        nc = get_table_count(cnx, cursor, constituents_table)
        json_fname = f'recipes_r{nr}i{ni}c{nc}.json'
    json_fpath = get_jsonpath(json_fname, dir_=exportdir)
    print(f"writing recipes to:\n\t{json_fpath}")
    with open(json_fpath,'w') as json_file:
        json.dump(to_export, json_file, indent=4)

