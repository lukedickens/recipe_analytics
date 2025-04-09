import mysql.connector
import json

from repurposing.mysql.create import get_connection
from repurposing.mysql.create import safe_create_indices


def get_canonical_recipes(cnx, cursor):
    safe_create_indices(cursor, [
        ('canonical_constituents','recipe_id'), ('validated_recipes','recipe_id')])
    select_valid_ingredients_query = """
        SELECT DISTINCT c.recipe_id
            FROM canonical_constituents AS c INNER JOIN validated_recipes AS r
            ON c.recipe_id = r.recipe_id
        """
    cursor.execute(select_valid_ingredients_query)
    return [row[0] for row in cursor.fetchall()]


def get_canonical_ingredients(cnx, cursor):
    safe_create_indices(cursor, [
        ('canonical_constituents','canonical_id'), ('validated_ingredients','ingredient_id')])
    select_valid_ingredients_query = """
        SELECT DISTINCT i.ingredient_id
            FROM canonical_constituents AS c INNER JOIN validated_ingredients AS i
            ON c.canonical_id = i.ingredient_id
        """
    cursor.execute(select_valid_ingredients_query)
    return [row[0] for row in cursor.fetchall()]

def get_canonical_constituents(cnx, cursor):
    safe_create_indices(cursor, [('canonical_constituents','constituent_id')])
    select_valid_constituents_query = """
        SELECT recipe_id, canonical_id
            FROM canonical_constituents
        """
    cursor.execute(select_valid_constituents_query)
    return cursor.fetchall()


def get_validated_ingredient_names(cnx, cursor):
    safe_create_indices(cursor, [
        ('validated_ingredients','ingredient_id'), ('ingredients','ingredient_id')])
    select_valid_ingredients_query = """
        SELECT i.ingredient_id, i.ingredient_name
            FROM validated_ingredients AS v INNER JOIN ingredients AS i
            ON v.ingredient_id = i.ingredient_id
        """
    cursor.execute(select_valid_ingredients_query)
    return {row[0]:row[1] for row in cursor.fetchall()}

def get_validated_recipe_titles(cnx, cursor):
    safe_create_indices(cursor, [
        ('canonical_constituents','recipe_id'), ('validated_recipes','recipe_id')])
    select_valid_ingredients_query = """
        SELECT v.recipe_id, r.recipe_name
            FROM validated_recipes AS v INNER JOIN recipes AS r
            ON v.recipe_id = r.recipe_id
        """
    cursor.execute(select_valid_ingredients_query)
    return {row[0]:row[1] for row in cursor.fetchall()}

