import mysql.connector
from mysql.connector import errorcode
import json
import numpy as np

from repurposing.mysql.create import drop_table
from repurposing.mysql.create import rename_table


problem_strings  = []
problem_string = ' or '
problem_strings.append(problem_string)
problem_string = ' for the '
problem_strings.append(problem_string)
problem_string = ','
problem_strings.append(problem_string)
problem_string = ' and '
problem_strings.append(problem_string)
problem_string = ' not '
problem_strings.append(problem_string)
problem_string = ' with '
problem_strings.append(problem_string)
problem_string = ' in '
problem_strings.append(problem_string)
problem_string = '\\\'s'
problem_strings.append(problem_string)
problem_string = '\\\*'
problem_strings.append(problem_string)
problem_string = '('
problem_strings.append(problem_string)
problem_string = 'slices '
problem_strings.append(problem_string)
problem_string = ' cup '
problem_strings.append(problem_string)
problem_string = '&'
problem_strings.append(problem_string)
problem_string = ';'
problem_strings.append(problem_string)
problem_strings.append(problem_string)
problem_string = '. '
problem_strings.append(problem_string)
problem_string = '..'
problem_strings.append(problem_string)
problem_string = '+'
problem_strings.append(problem_string)
problem_string = 'available'
problem_strings.append(problem_string)
problem_string = 'accompaniment' #  typically indicates a recipe that goes well with it
problem_strings.append(problem_string)
problem_string = 'to taste'
problem_strings.append(problem_string)
problem_string = 'additional'
problem_strings.append(problem_string)
problem_string = ' plus '
problem_strings.append(problem_string)
problem_string = ' more '
problem_strings.append(problem_string)
problem_string = ' i like '
problem_strings.append(problem_string)
problem_string = ' you like '
problem_strings.append(problem_string)
problem_string = '/' # possible substitution indicator 
problem_strings.append(problem_string)
problem_string = ' of '
problem_strings.append(problem_string)
problem_string = ' much '
problem_strings.append(problem_string)
problem_string = ' needed '
problem_strings.append(problem_string)
# for counting nothing
#problem_strings  = []
#problem_string = ' whapoihoatopihpoiht '
#problem_strings.append(problem_string)

problem_conditions = [f"ingredient_name LIKE '%{s}%'" for s in problem_strings]
# any color/kind/type really just a generaliser
problem_condition = "ingredient_name LIKE '%any %'" 
problem_conditions.append(problem_condition)
problem_condition = "ingredient_name LIKE '%add %'"
problem_conditions.append(problem_condition)
problem_condition = "ingredient_name LIKE '%if %'"
problem_conditions.append(problem_condition)
problem_condition = "ingredient_name LIKE '%as well as %'"
problem_conditions.append(problem_condition)
# each can indicate "whole" with a single ingredient on recipeland/kraftrecipes
# each can indicate multiple ingredients more widely
problem_condition = "ingredient_name LIKE 'each %'"
problem_conditions.append(problem_condition)
problem_condition = "ingredient_name REGEXP '[[:digit:]]+'"
problem_conditions.append(problem_condition)

WHERE_INGR_NAME_GOOD = ' AND '.join([f"NOT {c}" for c in problem_conditions])


# Real methods
def extract_ingredient_counts(
        cnx, cursor, 
        constituents_table='constituents',
        ingredients_table_from='filtered_ingredients_counts',
        ingredients_table_to='filtered_ingredient_counts',
        verbose=False, fragile=True,
        drop_old_ingredients_table=False):
    """
    Create new ingredient table with frequency count of the number of recipe.
    """
    # check for name clash with old and new ingredients table
    if ingredients_table_from == ingredients_table_to:
        if verbose:
            print(
                "Old and new ingredient table names are equal, renaming old")
        ingredients_table_tmp = ingredients_table_from + '_tmp'
        rename_table(
            cnx, cursor, ingredients_table_from, ingredients_table_tmp,
            fragile=fragile, verbose=verbose)
        ingredients_table_from = ingredients_table_tmp
        drop_old_ingredients_table = True
    # create ingredients table with frequency counts from associated constituents
    # table
    sql_create = f"""
    CREATE TABLE {ingredients_table_to} AS
        SELECT
            i.ingredient_id, i.ingredient_name, COUNT(*) AS count
          FROM {ingredients_table_from} AS i
            INNER JOIN {constituents_table} AS c
              ON i.ingredient_id = c.ingredient_id
          GROUP BY i.ingredient_id, i.ingredient_name"""
    if verbose:
        print(f"running:\n{sql_create}")
    cursor.execute(sql_create)
    cnx.commit()
    sql_create_index_primary = f"""
        ALTER TABLE {ingredients_table_to} ADD PRIMARY KEY (ingredient_id)"""
    cursor.execute(sql_create_index_primary)
    cnx.commit()
    sql_create_index_count = f"""
        CREATE INDEX count ON {ingredients_table_to} (count)"""
    cursor.execute(sql_create_index_count)
    cnx.commit()

    # optionally remove old ingredients table. automatically done if tmp table
    # created due to name clash.
    if drop_old_ingredients_table:
        drop_table(
            cnx, cursor, ingredients_table_from,
            fragile=fragile, verbose=verbose)

def filter_constituents_by_recipe(
        cnx, cursor, 
        constituents_table_to='filtered_constituents',
        constituents_table_from='constituents',
        recipe_table='recipes', 
        verbose=False, fragile=True,
        drop_old_constituents_table=False):
    """
    Now filter the constituents table to filter
    out the constituents that are not present in the 
    referenced recipe table. This is to be used after the 
    filter_recipes_by_constituent_ingredient_counts
    function has been called, in order that the 
    extract_ingredient_counts
    function can be called to give an updated set of 
    ingredient counts
    """        
    # check for name clash with old and new ingredients table
    if constituents_table_from == constituents_table_to:
        if verbose:
            print("Old and new constituents table names are equal, renaming old")
        constituents_table_tmp = constituents_table_from + '_tmp'
        rename_table(
            cnx, cursor, constituents_table_from, constituents_table_tmp,
            fragile=fragile, verbose=verbose)
        constituents_table_from = constituents_table_tmp
        drop_old_constituents_table = True
        
    sql_create_constituents = f"""
    CREATE TABLE {constituents_table_to} AS
        SELECT c.*
          FROM {constituents_table_from} AS c
            INNER JOIN {recipe_table} AS r
              ON c.recipe_id = r.recipe_id
    """
    if verbose:
        print(f"running:\n{sql_create_constituents}")
    cursor.execute(sql_create_constituents)
    cnx.commit()
    sql_create_index_ingredient_id = f"""
        CREATE INDEX ingredient_id ON {constituents_table_to} (ingredient_id)"""
    cursor.execute(sql_create_index_ingredient_id)
    cnx.commit()
    sql_create_index_recipe_id = f"""
        CREATE INDEX recipe_id ON {constituents_table_to} (recipe_id)"""
    cursor.execute(sql_create_index_recipe_id)
    cnx.commit()

    # optionally remove old ingredients table. automatically done if tmp table
    # created due to name clash.
    if drop_old_constituents_table:
        drop_table(
            cnx, cursor, constituents_table_from,
            fragile=fragile, verbose=verbose)


def filter_ingredients_by_name(
        cnx, cursor,
        ingredients_table_from='ingredient_counts',
        ingredients_table_to='filtered_ingredient_counts',
        select_what = '*',
        where_conditions=WHERE_INGR_NAME_GOOD, 
        fragile=True, verbose=False):
    """
    Copy one table with ingredient names (and most likely counts)
    to another table but restricting ingredient names to not contain problematic
    string patterns. See WHERE_INGR_NAME_GOOD for the default where
    condition
    """
    sql_select = f"""
        SELECT {select_what} FROM {ingredients_table_from}
            WHERE {where_conditions}
        """
    sql_create = f"""
        CREATE TABLE {ingredients_table_to} AS {sql_select}"""
    if verbose:
        print(f"running:\n{sql_create}")
    try:
        cursor.execute(sql_create)
        cnx.commit()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        else:
            print("Error encountered: ", err.msg)
            raise err
        if fragile:
            raise err
    else:
        if verbose:
            print("OK")
    sql_create_index_primary = f"""
        ALTER TABLE {ingredients_table_to} ADD PRIMARY KEY (ingredient_id)"""
    cursor.execute(sql_create_index_primary)
    cnx.commit()
    sql_create_index_count = f"""
        CREATE INDEX count ON {ingredients_table_to} (count)"""
    cursor.execute(sql_create_index_count)
    cnx.commit()

    
def choose_lower_threshold(scores, desired_fraction=0.5, verbose=False):
    """
    Given an array of scores what threshold is needed such that <desired_fraction>
    of the input is greater than the threshold.
    """
    min_count = np.min(scores)
    max_count = np.max(scores)
    N = len(scores)
    desired_N = int(N*desired_fraction)

    threshold = min_count//2
    step = (max_count-min_count)//4
    mult = 1
    while step > 0:
        threshold += mult*step
        count_above_thresh = np.sum(scores >= threshold)
        if verbose:
            print(f"{count_above_thresh} items ({count_above_thresh/N*100:.1f}%), with count >= {threshold}")
        if count_above_thresh > desired_N:
            mult = 1
        else:
            mult = -1
        step = step // 2
    return threshold

def filter_recipes_by_constituent_ingredient_counts(
        cnx, cursor, threshold=None,
        ingredient_counts_table='filtered_ingredient_counts',
        recipe_table_from='recipes',
        recipe_table_to='filtered_recipes',
        constituents_table='constituents',
        agg_func='MIN',
        desired_fraction=0.5, drop_old_recipe_table=False,
        fragile=True, verbose=False):
    """
    Make a filtered copy of the recipes table excluding recipes with
    constituents whose recipe counts do not meet certain frequency requirements.
    Default behaviour is to exclude recipes based on the minimium ingredient
    count of all constituents in the recipe. Control over the strength of the
    filter is given by the desired_fraction parameter which states by
    what factor you wish your number of recipes to be reduced by OR
    by the threshold parameter which gives a numeric threshold on the 
    minimum count.
    
    
    parameters
    ----------
    desired_fraction [float]
        If threshold is not specified, desired_fraction can be used to find
        an appropriate threshold to reduce the number of recipes to a fraction
        of the original.
    threshold [int]
        The minimum score by which a recipe will be excluded. See agg_func for
        the meaning of this score.
    agg_func [str] ('MIN'|'MAX'|'MEAN')
        How a recipe is scored in terms of its constituent ingredient counts.    
    """
    # check for name clash with old and new recipe table
    if recipe_table_from == recipe_table_to:
        if verbose:
            print("Old and new recipe names are equal, renaming old")
        recipe_table_tmp = recipe_table_from + '_tmp'
        rename_table(
            cnx, cursor, recipe_table_from, recipe_table_tmp,
            fragile=fragile, verbose=verbose)
        recipe_table_from = recipe_table_tmp
        drop_old_recipe_table = True
            
    # if threshold not specified then choose based on either desired fraction
    # or TODO new size of recipe table (number of recipe ids)
    sql_get_scores = f"""
            SELECT {agg_func}(i.count) AS score
                    FROM {ingredient_counts_table} AS i
                        INNER JOIN {constituents_table} AS c
                      ON i.ingredient_id = c.ingredient_id
                    GROUP BY c.recipe_id
        """
    if threshold is None:
        if verbose:
            print(f"running:\n{sql_get_scores}")        
        cursor.execute(sql_get_scores)
        scores = np.array(cursor.fetchall())
        threshold = choose_lower_threshold(
            scores, desired_fraction=desired_fraction)

    # now create new recipe table by filtering out recipes with less frequently
    # used ingredients
    # TODO (currently uses MIN but should support AVG and MAX)
    sql_create_filtered_recipes = f"""
        CREATE TABLE {recipe_table_to} AS
            SELECT r.* FROM
                {recipe_table_from} AS r
                INNER JOIN
                    (SELECT c.recipe_id AS recipe_id, {agg_func}(i.count) AS score
                        FROM {ingredient_counts_table} AS i
                            LEFT JOIN {constituents_table} AS c
                          ON i.ingredient_id = c.ingredient_id
                        GROUP BY c.recipe_id) AS filtered
                ON r.recipe_id = filtered.recipe_id
                WHERE filtered.score > {threshold}
            """
    if verbose:
        print(f"running:\n{sql_create_filtered_recipes}")
    cursor.execute(sql_create_filtered_recipes)
    cnx.commit()
    sql_create_index_primary = f"""
        ALTER TABLE {recipe_table_to} ADD PRIMARY KEY (recipe_id)"""
    cursor.execute(sql_create_index_primary)
    cnx.commit()
    
    # optionally remove old recipe table. automatically done if tmp table
    # created due to name clash.
    if drop_old_recipe_table:
        drop_table(
            cnx, cursor, recipe_table_from,
            fragile=fragile, verbose=verbose)


# helper methods
def copy_table(
        cnx, cursor,
        table_from='ingredient_counts',
        table_to='filtered_ingredient_counts',
        verbose=False, preserve=False):
    """
    parameters
    ----------
    preserve - preserves indices and triggers from the original table
    """
    if preserve:
        sql_create = f"""
            CREATE TABLE {table_to} LIKE {table_from}
            """
        sql_insert = f"""
            INSERT INTO {table_to} SELECT * FROM {table_from}
            """
        if verbose:
            print(f"running:\n{sql_create}")
        cursor.execute(sql_create)
        cnx.commit()
        if verbose:
            print(f"running:\n{sql_insert}")
        cursor.execute(sql_insert)
        cnx.commit()
    else:
        sql_create_from = f"""
            CREATE TABLE {table_to} AS SELECT * FROM {table_from}
            """
        cursor.execute(sql_create_from)
        cnx.commit()

SQL_COUNT_TEMPLATE = "SELECT COUNT(*) FROM %s"
def get_table_count(cnx, cursor, table_name,
        sql_count_template=SQL_COUNT_TEMPLATE):
    cursor.execute(sql_count_template % (table_name,))
    number = cursor.fetchall()[0][0]
    return number

def report_table_count(
        cnx, cursor, table_name,
        sql_count_template=SQL_COUNT_TEMPLATE):
    number = get_table_count(
        cnx, cursor, table_name,
        sql_count_template)
    print(f"Count of {table_name}: {number}")

