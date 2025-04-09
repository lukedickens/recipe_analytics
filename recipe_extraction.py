import numpy as np

from repurposing.mysql.create import get_connection

from repurposing.mysql.filter import extract_ingredient_counts
from repurposing.mysql.filter import filter_constituents_by_recipe
from repurposing.mysql.filter import filter_ingredients_by_name
from repurposing.mysql.filter import choose_lower_threshold
from repurposing.mysql.filter import filter_recipes_by_constituent_ingredient_counts
# TODO: move next functions to repurposing.mysql.create
from repurposing.mysql.filter import copy_table
# TODO: move next functions to repurposing.mysql.query
from repurposing.mysql.filter import get_table_count
from repurposing.mysql.filter import report_table_count

from repurposing.mysql.export import export_recipes_to_json

from repurposing.mysql.create import drop_tables

def main(
        user=None, password=None,
        desired_number_recipes=None,
        iterations=None, refresh_tables=False):
    cnx = get_connection(user=user, password=password)
    cursor = cnx.cursor()
    
    # filtering the recipes
    ingredient_counts_table = 'ingredient_counts'
    filtered_ingredient_counts_table = 'filtered_ingredient_counts'
    recipes_table = 'recipes'
    filtered_recipes_table = 'filtered_recipes'
    constituents_table = 'constituents'
    filtered_constituents_table='filtered_constituents'

    if refresh_tables:
        these_table_names = [
            filtered_ingredient_counts_table,
            filtered_recipes_table, 
            filtered_constituents_table]
        drop_tables(cnx, cursor, these_table_names)

    # first we filter ingredients by name to clean up some obvious parsing
    # errors
    filter_ingredients_by_name(
            cnx, cursor,
            ingredients_table_from=ingredient_counts_table,
            ingredients_table_to=filtered_ingredient_counts_table,
            select_what = '*',
            fragile=False, verbose=True)

    report_table_count(
            cnx, cursor, filtered_ingredient_counts_table)

    # copy the tables to new locations so we don't
    # interfere with the stable copies
    # recipes
    copy_table(
            cnx, cursor,
            table_from=recipes_table,
            table_to=filtered_recipes_table,
            verbose=True)
    report_table_count(
            cnx, cursor, filtered_recipes_table)
    # constituents
    copy_table(
            cnx, cursor,
            table_from=constituents_table,
            table_to=filtered_constituents_table,
            verbose=True)
    report_table_count(
            cnx, cursor, filtered_constituents_table)

    for i in range(iterations):
        current_number_recipes = get_table_count(cnx, cursor, filtered_recipes_table)
        factor_reduce = desired_number_recipes/current_number_recipes
        print(f"current number of recipes = {current_number_recipes}")
        print(f"desired_number_recipes = {desired_number_recipes}")
        print(f"remaining desired factor reduction: {factor_reduce}")
        remaining_iters = iterations - i
        desired_fraction=factor_reduce**(1/remaining_iters)
        print(f"reduction sought this iteration: {desired_fraction}")
        filter_recipes_by_constituent_ingredient_counts(
            cnx, cursor, 
            #threshold=None,
            ingredient_counts_table=filtered_ingredient_counts_table,
            recipe_table_from=filtered_recipes_table,
            recipe_table_to=filtered_recipes_table,
            constituents_table=filtered_constituents_table,
            desired_fraction=desired_fraction,
            #drop_old_recipe_table=False,
            verbose=False, fragile=True)
        report_table_count(
            cnx, cursor, filtered_recipes_table)
        filter_constituents_by_recipe(
            cnx, cursor, 
            constituents_table_to=filtered_constituents_table,
            constituents_table_from=filtered_constituents_table,
            recipe_table=filtered_recipes_table, 
            verbose=False, fragile=True)
        report_table_count(
                cnx, cursor, filtered_constituents_table)
        extract_ingredient_counts(
            cnx, cursor, 
            constituents_table=filtered_constituents_table,
            ingredients_table_from=filtered_ingredient_counts_table,
            ingredients_table_to=filtered_ingredient_counts_table,
            #drop_old_ingredients_table=False,
            verbose=False, fragile=True)
        report_table_count(
            cnx, cursor, filtered_ingredient_counts_table)

    #TODO Check indentation
    ## now export them down to json file
    export_recipes_to_json(
        cnx, cursor,
        recipes_table=filtered_recipes_table,
        ingredients_table=filtered_ingredient_counts_table,
        constituents_table=filtered_constituents_table,
        ## other arguments are the defaults (at time of writing these were)
        #     include_title=True, include_id=False, include_ingredients=True,
        #     include_constituents=False, title_key='title',
        #     ingredients_key='ingredients', constituents_key='ingredients',
        #     batch_size=5000, json_fname=None,
        #     exportdir = '../data/repurposing/export',
        verbose=False)


def create_parser():
    description= """
        Provides functionality to extract a set of filtered recipes 
        and ingredients such that the size and quality of the returned
        items are better """
    parser = argparse.ArgumentParser(
        prog='recipe_extraction',
        description=description,
        epilog='See git repository readme for more details.')
        
    parser.add_argument('--user', '-u', type=str,
        help='mysql user-name for secure connection.')
    parser.add_argument('--password', '-p', type=str,
        help='mysql password for secure connection.')
    parser.add_argument('--desired-number-recipes', '-n', type=int,
        default=5000,
        help='How many recipes do you want after filtering.')
    parser.add_argument('--refresh-tables', action="store_true",
        help='Do you want to purge the old filtered tables. Normally true but you must say.')
    parser.add_argument('--iterations', '-i', type=int,
        default=5,
        help='How many iterations of filtering do you want.')
    
    return parser


if __name__ == '__main__':
    import argparse
    args = create_parser().parse_args()
    main(**vars(args))    

