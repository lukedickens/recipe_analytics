# Recipe1M processing

This repository contains various functionality to process the data fro mthe Recipe1M+ dataset and to store this to a mysql database.


# Dataset construction and population

The primary construction of the database is done by calling the `recipe_database_construction.py` module. This runs with a number of different options which must be done in order or use the `all` option. Below I list these in order.

### creating a new database.

You must already have a user accoutn with a password on your mysql database. Then run:

```
python3 recipe_database_construction.py -u <username> -p '<password>' -o create_database
```

You can check the results of this by logging into mysql directly and then checking whether there is a database called `recipe_substitution`

### creating the basic tables

This creates the base tables of the recipe database

```
python3 recipe_database_construction.py -u <username> -p '<password>' -o create_tables
```

You can check the results of this by logging into mysql directly and then running
```
USE recipe_substitution;
SHOW tables;
```


### Populating the recipes table

This will read the data from the appropriate folder and insert recipes into the `recipes` table for each entry in the json files.

```
python3 recipe_database_construction.py -u <username> -p '<password>' -o insert_recipes
```

You can check the results of this by logging into mysql and going to the `recipe_substitution` database then running the following query:
```
SELECT COUNT(*) FROM recipes;
```
It should give something like the following output:
```
+----------+
| COUNT(*) |
+----------+
|  1029720 |
+----------+
1 row in set (0.22 sec)
```


### Populating the ingredients table

This will read the data from the appropriate folder and attempt to extract ingredients from the ingredients strings within the recipes in your data folder. This may be noisy and imperfect.

```
python3 recipe_database_construction.py -u <username> -p '<password>' -o insert_ingredients
```

You can check the results of this by logging into mysql and going to the `recipe_substitution` database then running the following query:
```
SELECT COUNT(*) FROM ingredients;
```
It should give something like the following output:
```
+----------+
| COUNT(*) |
+----------+
|   709656 |
+----------+
1 row in set (0.13 sec)
```


### Populating the constituents table

This will read the data from the appropriate folder and attempt to extract ingredients again from ingredient strings, then insert the ingredient into the constituents table which links each ingredient id to the recipe id. A constituent is an ingredient within a recipe.

```
python3 recipe_database_construction.py -u <username> -p '<password>' -o insert_constituents
```

You can check the results of this by logging into mysql and going to the `recipe_substitution` database then running the following query:
```
SELECT COUNT(*) FROM constituents;
```
It should give something like the following output:
```
+----------+
| COUNT(*) |
+----------+
|  9596883 |
+----------+
1 row in set (1.18 sec)
```


### Counting ingredients

This will count the number of recipes in which each ingredient is used and store this to a new table `ingredient_counts`.
```
python3 recipe_database_construction.py -u <username> -p '<password>' -o create_ingredient_counts
```

You can check the results of this by logging into mysql and going to the `recipe_substitution` database then running the following query:
```
SELECT * FROM ingredient_counts LIMIT 10;
```
It should give something like the following output:
```
+---------------+--------------------------------+--------+
| ingredient_id | ingredient_name                | count  |
+---------------+--------------------------------+--------+
|             1 | penne                          |    662 |
|             2 | beechers flagship cheese sauce |      2 |
|             3 | cheddar                        |    215 |
|             4 | gruyere cheese, grated         |    426 |
|             5 | chipotle chili powder          |    142 |
|             6 | unsalted butter                |  64087 |
|             7 | all-purpose flour              |  87753 |
|             8 | milk                           | 108800 |
|             9 | semihard cheese , grated       |     19 |
|            10 | semisoft cheese , grated       |      6 |
+---------------+--------------------------------+--------+
10 rows in set (0.00 sec)
```

<!--```python3 recipe_database_construction.py -u <username> -p '<password>' -o insert_constituents --input-subdir 230323```-->

### Filter ingredient names

This removes some of the known issues with ingredients to a new table `filtered_ingredient_counts`:
```
python3 recipe_database_construction.py -u <username> -p '<password>' -o create_ingredient_counts
```

You can check the results of this by logging into mysql and going to the `recipe_substitution` database then running the following query:
```
SELECT * FROM ingredient_counts LIMIT 10;
```
It should give something like the following output:
```
+---------------+--------------------------------+--------+
| ingredient_id | ingredient_name                | count  |
+---------------+--------------------------------+--------+
|             1 | penne                          |    662 |
|             2 | beechers flagship cheese sauce |      2 |
|             3 | cheddar                        |    215 |
|             4 | gruyere cheese, grated         |    426 |
|             5 | chipotle chili powder          |    142 |
|             6 | unsalted butter                |  64087 |
|             7 | all-purpose flour              |  87753 |
|             8 | milk                           | 108800 |
|             9 | semihard cheese , grated       |     19 |
|            10 | semisoft cheese , grated       |      6 |
+---------------+--------------------------------+--------+
10 rows in set (0.00 sec)
```



# Recipe1M Dataset

## Layers

### layer1.json

```js
{
  id: String,  // unique 10-digit hex string
  title: String,
  instructions: [ { text: String } ],
  ingredients: [ { text: String } ],
  partition: ('train'|'test'|'val'),
  url: String
}
```

### layer2.json

```js
{
  id: String,   // refers to an id in layer 1
  images: [ {
    id: String, // unique 10-digit hex + .jpg
    url: String
  } ]
}
```

## Images

The images in each of the partitions, train/val/test, are arranged in a four-level hierarchy corresponding to the first four digits of the image id.

For example: `val/e/f/3/d/ef3dc0de11.jpg`

The images are in RGB JPEG format and can be loaded using standard libraries.


# Added by Luke post download

 
