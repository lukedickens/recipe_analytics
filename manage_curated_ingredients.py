#from nltk.corpus import wordnet
#from textblob import TextBlob
#import inflect
from textblob import Word
import csv
import os
import re
import copy
import numpy as np
import pandas as pd
import mysql
import json
from datetime import datetime

from repurposing.mysql.create import get_connection
from repurposing.mysql.create import DB_NAME
#from repurposing.mysql.create import index_exists
#from repurposing.mysql.create import create_index
from repurposing.mysql.create import safe_create_indices



def safe_dataframe_to_csv(df,fpath,n_backups=5, **kwargs):
    rename_old_files(fpath)
    df.to_csv(fpath, **kwargs)

def rename_old_files(file_path, n_backups=5):
    base, ext = os.path.splitext(file_path)

    # Check for existing files up to '_old5' and rename them accordingly
    for i in range(n_backups, 0, -1):
        old_file = f"{base}_old{i}{ext}"
        if os.path.exists(old_file):
            if i == n_backups:
                # Overwrite the oldest backup file
                os.remove(old_file)
            else:
                new_file = f"{base}_old{i+1}{ext}"
                os.rename(old_file, new_file)

    # Rename the original file to '_old1'
    if os.path.exists(file_path):
        os.rename(file_path, f"{base}_old1{ext}")

def filter_alphanumeric(strings):
    # Define a regular expression pattern to match strings starting with an alphanumeric character
    pattern = re.compile(r'^[a-zA-Z0-9]')

    # Filter the list using the pattern
    filtered_list = [s for s in strings if pattern.match(s)]

    return filtered_list

def add_to_dict_list(dict_, key, to_add):
    entry_list = dict_.get(key, [])
    entry_list.append(to_add)
    dict_[key] = entry_list
    return dict_

def add_to_dict_set(dict_, key, to_add):
    entry_set = dict_.get(key, set([]))
    entry_set.add(to_add)
    dict_[key] = entry_set
    return dict_


def create_aliases_spacing(ingredients, aliases=None):
    if aliases is None:
        aliases = {}
    discovered_ingredients = []
    relations = []
    for s in ingredients:
        alias = s.replace('  ',' ')
        if s != alias:
            # removing double spacing
            add_to_dict_set(aliases, s, alias)
            relations.append((s, "alias:spacing", alias))
            if not alias in ingredients:
                discovered_ingredients.append(alias)
    return aliases, discovered_ingredients, relations

def create_aliases_hyphens(ingredients, aliases=None):
    if aliases is None:
        aliases = {}
    discovered_ingredients = []
    relations = []
    for s in ingredients:
        if '-' in s:
            # both the hyphenated string and the string without the space
            # are aliases of the string with a space
            alias = s.replace('-', ' ')
            alias = alias.replace('  ',' ')
            add_to_dict_set(aliases, s, alias)
            relations.append((s, "alias:hypenation", alias))
            if not alias in ingredients:
                discovered_ingredients.append(alias)
            alternate = s.replace('-', '')
            if alternate in ingredients:
                add_to_dict_set(aliases, alternate, alias)
                relations.append((alternate, "alias:spacing", alias))
#            if not alternate in ingredients:
#                discovered_ingredients.append(alternate)
    return aliases, discovered_ingredients, relations

def create_aliases_plurals(ingredients, aliases=None):
    if aliases is None:
        aliases = {}
#    matched_plurals = []
    relations = []
    for s in ingredients:
        singular_candidate = str(Word(s).singularize())
#        singular_candidate = singular_candidate.replace('  ',' ')

        if (singular_candidate != s) and (singular_candidate in ingredients):
            # cannot be an alias of itself
            # but if it's singularization is also in the list then it is an alias
            alias = singular_candidate
            add_to_dict_set(aliases, s, alias)
#            matched_plurals.append(s)
            relations.append((s, "alias:plural-of", alias))
    return aliases, relations

def create_aliases_singular_forms(ingredients, aliases=None):
    if aliases is None:
        aliases = {}
#    matched_singular_forms = []
    relations = []
    for s in ingredients:
        plural_candidate = str(Word(s).pluralize())
#        plural_candidate = plural_candidate.replace('  ',' ')

        if (plural_candidate != s) and (plural_candidate in ingredients):
            # cannot be an alias of itself
            # but if it's singularization is also in the list then it is an alias
            alias = plural_candidate
            add_to_dict_set(aliases, s, alias)
#            matched_singular_forms.append(s)
            relations.append((s, "alias:singular-of", alias))
    return aliases, relations

def create_aliases_stemmed_forms(ingredients, aliases=None):
    if aliases is None:
        aliases = {}

#    matched_stemmed_forms = []
    relations = []
    for s in ingredients:
        w = Word(s)
        stemmed_candidate = str(w.stem())
#        stemmed_candidate = stemmed_candidate.replace('  ',' ')
        singular_candidate = str(w.singularize())
#        singular_candidate = singular_candidate.replace('  ',' ')

        if (stemmed_candidate != s) \
                and (stemmed_candidate != singular_candidate) \
                and (stemmed_candidate in ingredients):
            # cannot be an alias of itself
            # but if it's singularization is also in the list then it is an alias
            add_to_dict_set(aliases, stemmed_candidate, s)
#            matched_stemmed_forms.append(stemmed_candidate)
            relations.append((stemmed_candidate, "alias:stem-of", s))
    return aliases, relations


def create_aliases_abbreviations(ingredients, abbreviations, aliases=None):
    if aliases is None:
        aliases = {}

    discovered_ingredients = []
    relations = []
    for s in ingredients:
        alt = s
#        alt = alt.replace('  ',' ')
        for abbr, expanded in abbreviations.items():
            pattern = rf'(?<!\S){re.escape(abbr)}(?!\S)'
            alt = re.sub(pattern, expanded, alt)

#            alt = alt.replace(abbr, expanded)
        if s != alt:
            # both the hyphenated string and the string without the space
            # are aliases of the string with a space
            add_to_dict_set(aliases, s, alt)
            relations.append((s, "alias:abbreviation", alt))
            if not alt in ingredients:
                discovered_ingredients.append(alt)
    return aliases, discovered_ingredients, relations

def create_aliases(ingredients, abbreviations, aliases=None):
    #
    aliases, discovered_ingredients, relations = create_aliases_spacing(
        ingredients, aliases)
    discovered_ingredients = set(discovered_ingredients)
    #
    aliases, more_discovered_ingredients, more_relations = create_aliases_hyphens(
        ingredients, aliases)
    discovered_ingredients |= set(more_discovered_ingredients)
    relations = relations + more_relations
    #
    aliases, more_relations = create_aliases_plurals(
        ingredients, aliases)
    relations = relations + more_relations
    #
    aliases, more_relations = create_aliases_singular_forms(
        ingredients, aliases)
    relations = relations + more_relations
    #
    aliases, more_relations = create_aliases_stemmed_forms(
        ingredients, aliases)
    relations = relations + more_relations
    #
    aliases, more_discovered_ingredients, more_relations = create_aliases_abbreviations(
        ingredients, abbreviations, aliases)
    relations =  relations + more_relations
    discovered_ingredients |= set(more_discovered_ingredients)
    return aliases, discovered_ingredients, relations

def create_childof_candidates(ingredients, modifiers, childofs=None):
    if childofs is None:
        childofs = {}

    relations = []
    for k, m in enumerate(modifiers):
        try:
            n_toks = len(m.split(' '))
        except:
            print(f"Error with {m} at position {k}")
            raise
        for s in ingredients:
            ingr_tokens = s.split(' ')
            opening = ' '.join(ingr_tokens[:n_toks])
            cand_parent = ' '.join(ingr_tokens[n_toks:]).strip()
       
            if (m != opening):
                # skipp if not the opening
                pass
            elif (cand_parent == ''):
                # skip if empty string
                pass
            elif cand_parent.startswith('and '):
                # skip if empty string
                pass
            elif cand_parent.startswith("'n "):
                # skip if empty string
                pass
            elif cand_parent.startswith('&'):
                # skip if empty string
                pass
            else:
                add_to_dict_set(childofs, s, cand_parent)
                relations.append((s, f"child-of:starts-with:{m}", cand_parent))

    return childofs, relations

def create_all_childof_candidates(ingredients, modifiers, childofs=None):
    discovered_ingredients = set()
    ingredients = set(ingredients)
    childofs, relations = create_childof_candidates(ingredients, modifiers, childofs)
    all_parents = [ parent for child, parents in childofs.items() for parent in parents ]
    all_parents = set(all_parents)
    fresh_ingredients = all_parents - set(ingredients)
    fresh_ingredients = fresh_ingredients - discovered_ingredients
    discovered_ingredients |= fresh_ingredients
    while len(fresh_ingredients) > 0:
        print(f"len(fresh_ingredients) = {len(fresh_ingredients)}")
        # want to look for parents of all existing andknown ingredients
        ingredients |= all_parents
        childofs, these_relations = create_childof_candidates(ingredients, modifiers, childofs)
        all_parents = [ parent for child, parents in childofs.items() for parent in parents ]
        all_parents = set(all_parents)
        # establish what are newly discovered (fresh) ingredients and record
        fresh_ingredients = all_parents - set(ingredients)
        fresh_ingredients = fresh_ingredients - discovered_ingredients
        discovered_ingredients |= fresh_ingredients
        relations = relations + these_relations
    return childofs, discovered_ingredients, relations

def discover_subtypes_from_local_roots(roots_of_valid_connected):
    unit_roots = [ r for r in roots_of_valid_connected if len(r.split(' ')) == 1]
    print(f"there are {len(unit_roots)} single term local roots")
    non_unit_roots = [ r for r in roots_of_valid_connected if len(r.split(' ')) > 1]
    #
    local_root_relations = []
    for phrase in non_unit_roots:
        tokens = phrase.split()
        if tokens[-2] == 'and':
            continue
        first = tokens[0]
        last = tokens[-1]
        for term in unit_roots:
            if unit_term_related(last, term):
                local_root_relations.append((phrase, 'subtype-of:last-word', term))
            if unit_term_related(first, term):
                local_root_relations.append((phrase, 'subtype-or-composite-of:first-word', term))
    print(f"len(local_root_relations) = {len(local_root_relations)}")
    return local_root_relations

def update_dataframe_with_validity(df, known_ingredients):
    """
    Updates dataframe with known ingredients. The assumption is that the
    ingredient is valid unless specifically declared not to be within the
    dataframe.
    """
    unmatched = []

    for s in known_ingredients:
        if s in df.index:
            if df.at[s, 'valid'] == -1:
                print(f'I thought that {s} was invalid. Skipping!')
            df.at[s, 'valid'] = 1
        else:
            unmatched.append(s)

    return unmatched

def validate_from_aliases_and_childofs(df, aliases, childofs):
    updated = False
    for ingr in df.index:
        this_valid = df.at[ingr,'valid']
        if this_valid == -1:
            continue
        for alias in aliases.get(ingr,[]):
            that_valid = df.at[alias,'valid']
            if that_valid != -1 and (this_valid+that_valid > 0):
                df.at[ingr,'valid'] = 1
                df.at[alias,'valid'] = 1
                updated = True
        for parent in childofs.get(ingr,[]):
            that_valid = df.at[parent,'valid']
            if that_valid == 1:
                df.at[ingr,'valid'] = 1
                updated = True
    return df, updated

def add_unmatched_to_dataframe(df, unmatched, max_id):
    """
    max_id is externally max id that comes from the original database
        we may have added additional ingredients previously with this method
        in which case we will treat a higher local id as the max
    """
    new_rows = []
    max_id = max(max_id, df['id'].max())

    for i, s in enumerate(unmatched, start=max_id + 1):
        new_row = {
            'id': i,
            'count': 0,
            'length': len(s),
            'valid': 0
        }

        new_rows.append((s, new_row))

    # Convert new_rows to a DataFrame and append it to df
    unmatched_df = pd.DataFrame.from_dict(dict(new_rows), orient='index')
    df = pd.concat([df, unmatched_df])

    return df

def drop_duplicate_entries(df):
    # Sort by 'valid' and 'id' so that 'valid' == 0 and smallest 'id' come first
    df_sorted = df.sort_values(by=['valid', 'id'])
    # Drop duplicates, keeping the first occurrence
    df = df_sorted.loc[~df_sorted.index.duplicated(keep='first')]
    return df


def extract_trademarks(working_ingredients, trademark_symbols):

    trademarks = set([])
    for ingr in working_ingredients:
        has_tms = False
        for tms in trademark_symbols:
            if tms in ingr:
                pos = ingr.index(tms)
                trademark = ingr[:pos]
                trademarks.add(trademark)
    return trademarks

def discover_trademark_relations(
        working_ingredients, known_trademarks=None, trademark_symbols=None):
    if trademark_symbols is None:
        trademark_symbols = ['®', '™']
    if known_trademarks is None:
        known_trademarks = set([])
    trademarks = extract_trademarks(working_ingredients, trademark_symbols)
    trademarks |= known_trademarks
    relations_trademark = []
    for ingr in working_ingredients:
        for trademark in trademarks:
            if ingr.startswith(trademark):
                relations_trademark.append((ingr, "contains:trade-mark", trademark))
    return relations_trademark, trademarks

#def check_singular_plural_relationship(singular_candidate, plural_candidate):
#    # Initialize WordNet Lemmatizer
#    lemmatizer = wordnet.WordNetLemmatizer()
#
#    # Check if singular_candidate is the singular of plural_candidate
#    singular_of_plural_candidate = lemmatizer.lemmatize(plural_candidate, 'n')
#    if singular_candidate == singular_of_plural_candidate:
#        return True
#
#    return False

def unit_term_related(term1, term2):
    w1 = Word(term1)
    w2 = Word(term2)
    if w1 == w2:
        return True
    if w1.singularize() == w2:
        return True
    if w2.singularize() == w1:
        return True
    if w1.pluralize() == w2:
        return True
    if w2.pluralize() == w1:
        return True
    if w1.stem() == w2:
        return True
    if w2.stem() == w1:
        return True
    return False

def check_singular_plural_relationship(singular_candidate, plural_candidate):
    singular_blob = Word(singular_candidate)
    plural_blob = Word(plural_candidate)

    # Get the singular form of the plural_candidate
    singular_of_plural_candidate = plural_blob.singularize()

    # Compare the singular form with the known singular
    return singular_candidate == singular_of_plural_candidate

#def check_singular_plural_relationship(singular_candidate, plural_candidate, p=inflect.engine()):
#    if p is None:
#        p = inflect.engine()
#    # Get the singular form of the plural_candidate
#    singular_of_plural_candidate = p.singular_noun(plural_candidate)
#    # Compare the singular form with the known singular
#    return singular_candidate == singular_of_plural_candidate

def load_df_and_set_index(fpath, index_name, default_index_col=0):
    df = pd.read_csv(fpath)
    if index_name in df.columns:
        df.set_index(index_name, inplace=True)
    else:
        col = df.columns[default_index_col]
        df.set_index(col, inplace=True)
        df.index.name = index_name
    return df

def load_working_ingredients(working_fpath):
    return load_df_and_set_index(working_fpath, 'name', default_index_col=0)

def load_ingredient_modifiers(modifiers_fpath):
    return load_df_and_set_index(modifiers_fpath, 'modifier', default_index_col=0)

def load_ingredient_abbreviations(abbreviations_fpath):
    return load_df_and_set_index(abbreviations_fpath, 'abbreviations', default_index_col=0)

def load_childofs(childofs_fpath):
    childofs_df = pd.read_csv(childofs_fpath)
    # convert to dictoinary
    childofs = {}
    for child in childofs_df['child']:
        childofs[child] = set(childofs_df[childofs_df['child'] == child]['parent'].to_list())
    return childofs

def load_aliases(aliases_fpath):
    aliases_df = pd.read_csv(aliases_fpath)

    aliases = {}
    for alias in aliases_df['alias']:
        aliases[alias] = set(aliases_df[aliases_df['alias'] == alias]['ingredient'].to_list())
    return aliases


def integrate_known_ingredients(working_df, new_ingredients, externally_max_id=10000000):
    new_ingredients = [ingr.strip() for ingr in new_ingredients]
    unmatched_ingredients = update_dataframe_with_validity(
        working_df, new_ingredients)
    working_df = add_unmatched_to_dataframe(working_df, unmatched_ingredients, externally_max_id)
    return working_df

def show_table_properties(df):
    length = len(df.index)
    valid_count = (df['valid'] == 1).sum()
    unknown_count = (df['valid'] == 0).sum()
    invalid_count = (df['valid'] == -1).sum()
    print(f"table properties: length = {length}, valid={valid_count}, unknown={unknown_count}, invalid={invalid_count}")
    print(f"df.dtypes = {df.dtypes}")

def insert_new_ingredients_from(cnx, cursor, working_fpath):

    df = load_working_ingredients(working_fpath)

    # Read existing ingredients from the database
    cursor.execute("SELECT ingredient_name FROM ingredients")
    existing_ingredients = cursor.fetchall()

    # Convert to a set for faster lookup, normalize names
    existing_ingredient_set = {row[0] for row in existing_ingredients}

    # Filter out existing ingredients
    new_ingredients = df[~df.index.isin(existing_ingredient_set) & (df['valid']==1)]

    # Prepare insert query
    add_ingredient = ("INSERT INTO ingredients (ingredient_id, ingredient_name) VALUES (%s, %s)")

    # Insert new ingredients
    for name, row in new_ingredients.iterrows():
        if name[-1] == ' ':
            print(f"name = {name} (id: {row['id']}) ends with a space")
        ingredient_data = (int(row['id']), str(name))
        try:
            cursor.execute(add_ingredient, ingredient_data)
        except mysql.connector.Error as err:
            print(f"Error: {err}, data: {ingredient_data}")
#        cursor.execute(add_ingredient, ingredient_data)

    # Commit the transaction
    cnx.commit()

def create_validated_ingredients(cnx, cursor):
    # Create the validated_ingredients table
    print("Creating the validated_ingredients table...")
    create_table_query = """
    CREATE TABLE IF NOT EXISTS validated_ingredients (
        ingredient_id INT,
        FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
    )
    """
    cursor.execute(create_table_query)

def insert_validated_ingredients(cnx, cursor, working_fpath):
    print("Inserting validated ingredients...")
    df = load_working_ingredients(working_fpath)

    cursor.execute("SELECT ingredient_name FROM ingredients")
    existing_ingredients = cursor.fetchall()

    # Convert to a set for faster lookup, normalize names
    existing_ingredient_set = {row[0] for row in existing_ingredients}

    # Filter out existing ingredients
    valid_ingredients = df[df.index.isin(existing_ingredient_set) & (df['valid']==1)]

    # Prepare the insert query
    insert_query = "INSERT INTO validated_ingredients (ingredient_id) VALUES (%s)"


    # Insert the valid ingredient IDs
    added = 0
    for name, row in valid_ingredients.iterrows():
        ingredient_id = int(row['id'])
#        print(f"name = {name}, id: {ingredient_id}")
#    for ingredient_id in valid_ingredients['id']:
        cursor.execute(insert_query, (ingredient_id,))
        added += 1
    print(f"A total of {added} validated ingredients have been added.")
    # Commit the transaction
    cnx.commit()

def create_ingredient_relations(cnx, cursor):
    # Create the validated_recipes view
    create_table_query = """
    CREATE TABLE IF NOT EXISTS ingredient_relations (
        subject_id INT,
        predicate TEXT,
        object_id INT,
        FOREIGN KEY (subject_id) REFERENCES ingredients(ingredient_id),
        FOREIGN KEY (object_id) REFERENCES ingredients(ingredient_id)
    )
    """
    cursor.execute(create_table_query)
    # Commit the transaction (not always necessary for views)
    cnx.commit()

def insert_ingredient_relations(
        cnx, cursor, relations_fpath):
    col_names = ['subject', 'relation', 'object']
    print("Inserting ingredient relations...")
    df = pd.read_csv(relations_fpath, header=None, names=col_names)
    print(f"df = {df}")

    safe_create_indices(cursor, [('ingredients','ingredient_id'),
        ('validated_ingredients','ingredient_id')])
    select_valid_ingredients_query = """
        SELECT i.ingredient_id, i.ingredient_name
            FROM validated_ingredients AS v
            LEFT JOIN ingredients AS i
            ON i.ingredient_id = v.ingredient_id
        """
    cursor.execute(select_valid_ingredients_query)
    valid_id_ingr_pairs = cursor.fetchall()

    # Convert to a set for faster lookup, normalize names
    existing_ingredients = {row[1]:row[0] for row in valid_id_ingr_pairs}
    print(f"len(existing_ingredients) = {len(existing_ingredients)}")

#    # Filter out non-valid ingredients as subject or object
    valid_relations_df = df[
        df['subject'].isin(existing_ingredients) & df['object'].isin(existing_ingredients)]
    print(f"valid_relations_df = {valid_relations_df}")

    # Prepare the insert query
    insert_query = "INSERT INTO ingredient_relations (subject_id, predicate, object_id) VALUES (%s, %s, %s)"


    # Insert the valid ingredient IDs
    added = 0
    for name, row in valid_relations_df.iterrows():
        subject_id = existing_ingredients[row['subject']]
        predicate = row['relation']
        object_id = existing_ingredients[row['object']]
#        print(f"name = {name}, id: {ingredient_id}")
#    for ingredient_id in valid_ingredients['id']:
        cursor.execute(insert_query, (subject_id, predicate, object_id))
        added += 1
    print(f"A total of {added} ingredient relations have been added.")
    # Commit the transaction
    cnx.commit()

def construct_validated_recipes(cnx, cursor):

    """
    Uses validated_ingredients table to construct a list of recipes
    that comprise of only validated_ingredients.
    """
    required_indices = [
        ("constituents", "ingredient_id"),
        ("constituents", "recipe_id"),
        ("validated_ingredients", "ingredient_id")
         ]
    safe_create_indices(cursor, required_indices)
    # Create the validated_recipes view
    create_view_query = """
    CREATE TABLE validated_recipes AS
    SELECT DISTINCT c.recipe_id
    FROM constituents c
    JOIN validated_ingredients vi ON c.ingredient_id = vi.ingredient_id
    WHERE c.recipe_id NOT IN (
        SELECT c2.recipe_id
        FROM constituents c2
        LEFT JOIN validated_ingredients vi2 ON c2.ingredient_id = vi2.ingredient_id
        WHERE vi2.ingredient_id IS NULL
    );
    """
    cursor.execute(create_view_query)
    # Commit the transaction (though not always necessary for views)
    cnx.commit()

def construct_canonical_ingredients(cnx, cursor):

    """
    Uses validated_ingredients table to construct a list of recipes
    that comprise of only validated_ingredients.
    """
    required_indices = [
        ("ingredient_relations", "subject_id"),
#        ("ingredient_relations", "predicate"),
        ("ingredient_relations", "object_id")
         ]
    safe_create_indices(cursor, required_indices)
    select_query = """
        SELECT
                r.subject_id, i1.ingredient_name AS subject_name,
                r.predicate, r.object_id, i2.ingredient_name AS object_name
            FROM ingredient_relations AS r
            LEFT JOIN ingredients AS i1
            ON r.subject_id = i1.ingredient_id
            LEFT JOIN ingredients AS i2
            ON i2.ingredient_id = r.object_id
            WHERE r.predicate LIKE 'alias:%' AND r.subject_id <> r.object_id
        """
    cursor.execute(select_query)
    existing_relations = cursor.fetchall()
    columns = ['subject_id', 'subject_name', 'predicate', 'object_id', 'object_name']
    # load all alias relations
    relations_df = pd.DataFrame(
        existing_relations, columns=columns)
#    print(f"relations_df = {relations_df}")
    # exclude singular-of relations as singulars will be the canonical form
    relations_df = relations_df[
        ~relations_df['predicate'].str.startswith('alias:singular-of')]
    print(f"relations_df = {relations_df}")

    aliases = relations_df.set_index('subject_id')['object_id'].to_dict()
    names = relations_df.set_index('subject_id')['subject_name'].to_dict()
    names.update(relations_df.set_index('object_id')['object_name'].to_dict())

    # Display the dictionary
    
    print(f"len(list(aliases.keys())) = {len(list(aliases.keys()))}")
    print(f"len(set(aliases.values())) = {len(set(aliases.values()))}")

    canonical_aliases, cycle_detected = safe_transitive_closure(aliases)
    print(f"cycle_detected = {cycle_detected}")
    print(f"len(set(canonical_aliases.values())) = {len(set(canonical_aliases.values()))}")
    if cycle_detected:
        print_cycles(canonical_aliases, names)
        raise ValueError("Cycles detected in aliases")

    create_canonical_ingredients(cnx, cursor)
    insert_canonical_ingredients(cnx, cursor, canonical_aliases)

def insert_canonical_ingredients(cnx, cursor, canonical_aliases):
    # Prepare the insert query
    select_query = """
        SELECT i.ingredient_id, i.ingredient_name 
            FROM validated_ingredients AS v 
            LEFT JOIN ingredients AS i
            ON v.ingredient_id = i.ingredient_id"""
    cursor.execute(select_query)
    valid_ingredients = cursor.fetchall()


    insert_query = """
        INSERT INTO canonical_ingredients (ingredient_id, canonical_id)
            VALUES (%s, %s)
        """
    # Insert the valid ingredient IDs
    added = 0
    for row in valid_ingredients:
        ingredient_id = row[0]
        if ingredient_id in canonical_aliases:
            canonical_id = canonical_aliases[ingredient_id]
        else:
            canonical_id = ingredient_id
        cursor.execute(insert_query, (ingredient_id,canonical_id))
        added += 1
    print(f"A total of {added} canonical ingredients have been added.")
    # Commit the transaction
    cnx.commit()


def create_canonical_ingredients(cnx, cursor):
    # Create the validated_recipes view
    create_view_query = """
    CREATE TABLE IF NOT EXISTS canonical_ingredients (
        ingredient_id INT,
        canonical_id INT,
        FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id),
        FOREIGN KEY (canonical_id) REFERENCES ingredients(ingredient_id)
    )
    """
    cursor.execute(create_view_query)
    # Commit the transaction (though not always necessary for views)
    cnx.commit()

def safe_transitive_closure(relation):
    updated_dict = relation
    while True:
        new_dict, changes_made = update_dictionary(updated_dict)
        cycle_detected = has_cycle(new_dict)
        if cycle_detected:
            print("Cycle detected. Rolling back to the original dictionary.")
            updated_dict = relation
            break
        
        if not changes_made:
            print("No more updates to perform. Dictionary update complete.")
            updated_dict = new_dict
            break

        updated_dict = new_dict
    return updated_dict, cycle_detected

def update_dictionary(relation):
    updated_dict = copy.deepcopy(relation)
    changes_made = False
    for key in updated_dict.keys():
        if updated_dict[key] in updated_dict:
            new_value = updated_dict[updated_dict[key]]
            if updated_dict[key] != new_value:
                updated_dict[key] = new_value
                changes_made = True
    return updated_dict, changes_made

def has_cycle(relation):
    for key in relation.keys():
        if key == relation[key]:
            return True
    return False
    
    
def print_cycles(relation, key_to_name):
    for key in relation.keys():
        if key == relation[key]:
            print(f"cycle for {key_to_name[key]}")

def construct_canonical_constituents(cnx, cursor):

    """
    Uses validated_ingredients table to construct a list of recipes
    that comprise of only validated_ingredients.
    """
    required_indices = [
        ("constituents", "ingredient_id"),
        ("constituents", "recipe_id"),
        ("validated_recipes", "recipe_id"),
        ("canonical_ingredients", "ingredient_id")
         ]
    safe_create_indices(cursor, required_indices)
    # Create the validated_recipes view
    create_view_query = """
    CREATE TABLE canonical_constituents AS
        SELECT DISTINCT c.constituent_id, c.recipe_id, i.canonical_id
            FROM validated_recipes AS r
            INNER JOIN constituents AS c
            ON r.recipe_id = c.recipe_id
            INNER JOIN canonical_ingredients AS i
            ON c.ingredient_id = i.ingredient_id;
    """
    cursor.execute(create_view_query)
    # Commit the transaction (though not always necessary for views)
    cnx.commit()

def sample_canonical_recipes(
        cnx, cursor, n_samples=50, p_restart=0.1, first_recipe_id=None):
    recipe_titles = {}
    recipe_constituents = {}
    ingredients = {}

    required_indices = [
        ("canonical_constituents", "recipe_id"),
        ("canonical_constituents", "canonical_id")
         ]
    safe_create_indices(cursor, required_indices)

    select_random_recipe_query = """
        SELECT recipe_id FROM canonical_constituents
            GROUP BY recipe_id ORDER BY RAND() LIMIT 1"""
    select_cond_random_recipe_query = """
        SELECT recipe_id FROM canonical_constituents
            WHERE canonical_id = %s 
            ORDER BY RAND() LIMIT 1"""

    
    # seeding the search with a recipe
    if first_recipe_id is None:
        cursor.execute(select_random_recipe_query)
        recipe_id = cursor.fetchall()[0][0]
        first_recipe_id = recipe_id
    else:
        recipe_id = first_recipe_id
    these_constituents = get_canonical_recipe_details(
        cnx, cursor, recipe_id, recipe_titles, recipe_constituents, ingredients)
    first_constituents = these_constituents
    # now iterate over
    while len(recipe_titles) < n_samples:
        if np.random.random() < p_restart:
            recipe_id = first_recipe_id
            these_constituents = first_constituents
        anchor_id = np.random.choice(these_constituents)
        cursor.execute(select_cond_random_recipe_query, (int(anchor_id),))
        recipe_id = cursor.fetchall()[0][0]
        these_constituents = get_canonical_recipe_details(
            cnx, cursor, recipe_id, recipe_titles, recipe_constituents, ingredients)
    data = dict(
        recipe_titles=recipe_titles, recipe_constituents=recipe_constituents,
        ingredients=ingredients)
#    print(f"recipe_titles = {recipe_titles}")
#    print(f"recipe_constituents = {recipe_constituents}")
#    print(f"ingredients = {ingredients}")
    print(f"len(recipe_titles) = {len(recipe_titles)}, len(ingredients) = {len(ingredients)}")
    fname = get_timestamped_filename("sampled_recipes", "json")
    resdir = 'data/samples/sampled_recipes'
    res_fpath = os.path.join(resdir, fname)
    print(f"Saving sampled recipes to {res_fpath}")
    with open(res_fpath, 'w') as f:
        json.dump(data, f)


def get_timestamped_filename(stem, ext):
    # Get the current date and time
    now = datetime.now()

    # Format the date and time
    # Example format: "2024-07-24_15-26-30"
    return f"{stem}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.{ext}"

def get_canonical_recipe_details(
        cnx, cursor, recipe_id, recipe_titles, recipe_constituents, ingredients):
    # queries
    select_recipe_name_query = """
        SELECT recipe_name FROM recipes
            WHERE recipe_id = %s LIMIT 1"""
    select_recipe_constituents_query = """
        SELECT DISTINCT canonical_id FROM canonical_constituents
            WHERE recipe_id = %s"""
    select_ingredient_name_query = """
        SELECT DISTINCT ingredient_name FROM ingredients
            WHERE ingredient_id = %s"""
    #   
    # getting details of recipe
    # title
    cursor.execute(select_recipe_name_query, (recipe_id,))
    recipe_name = cursor.fetchall()[0][0]
    recipe_titles[recipe_id] = recipe_name
    print(f"recipe (id: {recipe_id}) - {recipe_name}")
    # constituents
    cursor.execute(select_recipe_constituents_query, (recipe_id,))
    these_constituents = [ result[0] for result in cursor.fetchall()]
    recipe_constituents[recipe_id] = these_constituents
    # storing newly discovered ingredient names
    for ingr_id in these_constituents:
        if not ingr_id in ingredients:
            cursor.execute(select_ingredient_name_query, (ingr_id,))
            ingr_name = cursor.fetchall()[0][0]
            ingredients[ingr_id] = ingr_name
        print(f"* {ingr_id}: {ingredients[ingr_id]}")
    return these_constituents

def correct_ingredient_ids_from_master(
        cnx, cursor, working_fpath, n_backups):
    """
    There is a possibility that when curating ingredients we discovered
    ingredients which we thought were new but were in the master ingredient
    list. This happesn because we filter master ingredients by frequency before
    curating.
    """

    # Load existing ingredients from the database
    query = "SELECT ingredient_id, ingredient_name FROM ingredients"
    cursor.execute(query)
    existing_ingredients = cursor.fetchall()

    # Create a DataFrame from the existing ingredients
    existing_ingredients_df = pd.DataFrame(
        existing_ingredients, columns=['ingredient_id', 'ingredient_name'])
#    existing_ingredients_df['ingredient_name'] = existing_ingredients_df['ingredient_name'].str.lower().str.strip()


    working_df = load_working_ingredients(working_fpath)
#    # Normalize the index names in your DataFrame
#    df.index = df.index.str.lower().str.strip()

    # Merge the DataFrames to update the IDs
    updated_df = working_df.reset_index().merge(
        existing_ingredients_df, how='left', left_on='name', right_on='ingredient_name')

    # If an ingredient from the DataFrame already exists in the database, use the existing id
    # Otherwise, keep the original id from the DataFrame
    updated_df['id'] = updated_df['ingredient_id'].combine_first(updated_df['id'])

    # Drop the now redundant 'ingredient_name' and 'ingredient_id' columns
    updated_df = updated_df.drop(columns=['ingredient_name', 'ingredient_id'])
    updated_df = updated_df.set_index('name')
    safe_dataframe_to_csv(updated_df, working_fpath, n_backups=n_backups)

def main(
        option, working_fpath=None, relations_fpath=None,
        user=None, password=None, db_name=DB_NAME,
        n_backups=5, n_samples=50, first_recipe_id=None, p_restart=None):
    if not user is None:
        cnx = get_connection(user=user, password=password, db_name=db_name)
        cursor = cnx.cursor()
    else:
        cnx = None
        cursor = None


    if option == 'show':
        working_df = load_working_ingredients(working_fpath)
        with pd.option_context('display.max_rows', 1000, 'display.max_columns', None):
            print(working_df[working_df['valid']==1])
        print()
        show_table_properties(working_df)
        print(f"working_df.index.name = {working_df.index.name}, columns = {working_df.columns}")
    elif option == 'insert_new_ingredients':
        insert_new_ingredients_from(cnx, cursor, working_fpath)
    elif option == 'correct_ingredient_ids':
        correct_ingredient_ids_from_master(
            cnx, cursor, working_fpath, n_backups)
    elif option == 'construct_validated_ingredients':
        create_validated_ingredients(cnx, cursor)
        insert_validated_ingredients(cnx, cursor, working_fpath)
    elif option == 'construct_validated_recipes':
        construct_validated_recipes(cnx, cursor)
    elif option == 'construct_ingredient_relations':
        create_ingredient_relations(
            cnx, cursor)
        insert_ingredient_relations(
            cnx, cursor, relations_fpath)
    elif option == 'construct_canonical_ingredients':
        construct_canonical_ingredients(
            cnx, cursor)
    elif option == 'construct_canonical_constituents':
        construct_canonical_constituents(
            cnx, cursor)
    elif option == 'sample_canonical_recipes':
        sample_canonical_recipes(
            cnx, cursor, n_samples=n_samples, first_recipe_id=first_recipe_id)
    elif option == 'integrate_ingredient_lists':
        raise NotImplementedError('Yet')
        new_ingredients = load_ingredients(add_known_fpath)
        integrate_known_ingredients(working_fpath, new_ingredients)
        safe_dataframe_to_csv(df, fpath, n_backups=n_backups, **kwargs)
#    elif mode == 'integrate_ingredient_lists':
#        new_ingredients = load_ingredients(add_known_fpath)
#        integrate_known_ingredients(working_fpath, new_ingredients)
#        safe_dataframe_to_csv(df,fpath,n_backups=5, **kwargs)
#    elif mode == 'intra-validate':
#        modifiers_df = load_ingredient_modifiers(modifiers_fpath)
#        childofs = load_childofs(childofs_fpath)
#    raise NotImplementedError('Yet!')
    # insert constituents these are the ingredients for specific recipes
    else:
        raise ValueError(f"Unrecognised option {option}")
    if not cnx is None:
        cursor.close()
        cnx.close()

def create_parser():
    description= """
        Provides functionality to:
            * manage lists of ingredients and ingredient terms
            * integrate multiple ingredient lists
            * rapidly annotate them as validated
            * derived facts from this ingredient list
            * import improved ingredient lists and validation labels back into
            the database
        """
    parser = argparse.ArgumentParser(
        prog='Manage curated ingredients',
        description=description,
        epilog='See git repository readme for more details.')

    parser.add_argument('--user', '-u', type=str,
        help='mysql user-name for secure connection.')
    parser.add_argument('--password', '-p', type=str,
        help='mysql password for secure connection.')
    options = [
        'show', 'insert_new_ingredients', 'construct_validated_ingredients',
        'correct_ingredient_ids',
        'construct_validated_recipes', 'construct_ingredient_relations',
        'construct_canonical_ingredients', 'construct_canonical_constituents',
        'sample_canonical_recipes']
    parser.add_argument('--option', '-o', type=str, choices=options,
        default='show', help='What do you want to do?')
    # inserting recipes
    parser.add_argument('--working-fpath', type=str,
        help='Input path for working ingredients')
    parser.add_argument('--relations-fpath', type=str,
        help='Input path for ingredient relations')
    parser.add_argument('--first-recipe-id', type=int,
        help='Seed the sampling algorithm with a first recipe id')
    parser.add_argument('--n-samples', type=int, default=50,
        help='How many samples')
    parser.add_argument('--p-restart', type=float, default=0.1,
        help='Probability of restart with random walk sampling')

    return parser




if __name__ == '__main__':
    import argparse
    args = create_parser().parse_args()
    main(**vars(args))

