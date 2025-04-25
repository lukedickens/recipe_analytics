# Recipe1M processing

This repository contains various functionality to process the data fro mthe Recipe1M+ dataset and to store this to a mysql database. This proceeds in the following main steps. The first step JSON preprocessing, is to process the json files provided by the Recipe1M+ dataset layer 1.  The second step is to load the processed json files into a database. The partitioning of this process into two main steps means that you can reconstruct the dataset without using the same json files.

## JSON preprocessing

Begin by downloading a copy of the Recipe1M+ data and placing a copy in the file with relative path `data/1M+recipes/layer1.json`. The following command was run, and output generated, on the reference system showing this file and its filesize:

```bash
$ ls -sh data/1M+recipes/layer1.json 
1.4G data/1M+recipes/layer1.json
```

Then you should partition this json file into parts each a json file with a subset of the recipes. We recommend `15` parts. These subfiles should be named `layer1_<PART>.json` where `<PART>` is a zero padded integer, where the integers run contiguously from minimum to maximum id. In our case, the first file is `layer1_01.json` and the last is `layer1_15.json`. The following command was run, and output generated, on the reference system showing these files and their sizes:

```bash
$ ls -sh1 data/1M+recipes/layer1_{0,1}*.json 
90M data/1M+recipes/layer1_01.json
90M data/1M+recipes/layer1_02.json
90M data/1M+recipes/layer1_03.json
90M data/1M+recipes/layer1_04.json
90M data/1M+recipes/layer1_05.json
90M data/1M+recipes/layer1_06.json
90M data/1M+recipes/layer1_07.json
90M data/1M+recipes/layer1_08.json
90M data/1M+recipes/layer1_09.json
90M data/1M+recipes/layer1_10.json
90M data/1M+recipes/layer1_11.json
90M data/1M+recipes/layer1_12.json
90M data/1M+recipes/layer1_13.json
90M data/1M+recipes/layer1_14.json
90M data/1M+recipes/layer1_15.json
```

At this point, you should run the following command:
```
python recipe_json_preprocessing.py
```

By default this will load each file `data/1M+recipes/layer1_<PART>.json`, process it to add additional fields to each recipe and save the resulting data structure in json format to `data/repurposing/250425/layer1_proc1_<PART>.json`. The following command was run, and output generated, on the reference system showing these processed files and their sizes:

```bash
ls -sh1 data/repurposing/230323/layer1_proc1_{0,1}*
248M data/repurposing/230323/layer1_proc1_01.json
248M data/repurposing/230323/layer1_proc1_02.json
248M data/repurposing/230323/layer1_proc1_03.json
249M data/repurposing/230323/layer1_proc1_04.json
248M data/repurposing/230323/layer1_proc1_05.json
249M data/repurposing/230323/layer1_proc1_06.json
249M data/repurposing/230323/layer1_proc1_07.json
249M data/repurposing/230323/layer1_proc1_08.json
248M data/repurposing/230323/layer1_proc1_09.json
248M data/repurposing/230323/layer1_proc1_10.json
249M data/repurposing/230323/layer1_proc1_11.json
248M data/repurposing/230323/layer1_proc1_12.json
249M data/repurposing/230323/layer1_proc1_13.json
248M data/repurposing/230323/layer1_proc1_14.json
248M data/repurposing/230323/layer1_proc1_15.json
```

## Dataset construction and population

The primary construction of the database is done by calling the `recipe_database_construction.py` module. This runs with a number of different options which must be done in order or use the `all` option. These are listed below in order.

### creating a new database.

You must already have a user account with a password on your mysql database. Then run:

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
python3 recipe_database_construction.py -u <username> -p '<password>' -o filter_ingredient_names
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

## Original data

The original Recipe1M dataset is provided in two layers. The first is the text data in a single json file (that we operate on here). The second is a json file and associated images. The following descriptions were adapted from the original source descriptions.

### layer1.json

Layer 1 data, is text data, and is provided in a json file with a single outer list object containing a number of recipe dictionaries. A single recipe dictionary has the following form:


```js
{
  id: String,  // unique 10-digit hex string
  title: String,
  instructions: [...],
  ingredients: [...],
  partition: ('train'|'test'|'val'),
  url: String
}
```

The two elements `ingredients` and `instructions` represent lists of what we call **ingredient strings** and **instruction strings** respectively.

#### Ingredient strings

Each element of the `ingredients` list is a dictionary with the following structure:

```js
{ 
  text: String
}  
```

Where `text` is a text representation of the original string that was scraped from the associated recipe webpage. The original recipes typically contained a block of ingredients, commonly given as a bullet point list. We have identified some issues with these text elements. For instance, often the original recipe gives fractions as vulgar fractions, e.g. 1/2 for one half. However, at times, the text elements in the json will simply omit the slash character. For example, in recipe id `110542b55e` (see the original recipe [here](http://www.food.com/recipe/garlic-pasta-522136)), the third ingredient string is `"12 cup extra virgin olive oil (EVOO)"` rather than `"1/2 cup extra virgin olive oil (EVOO)"`.


#### Instruction strings

Similarly, Each element of the `instructions` list is a dictionary with the following structure:

```js
{ 
  text: String
}  
```
This describes a single methodological step from the recipe.



## Processed data 

After processing the json recipe dictionaries will be updated primarily in the `ingredients` element. In particular, the typical ingredient list element will now have the following form:

```js
{
    text: String,
    name: String,
    unit: String,
    quantity_str: String,
    quantity: Numeric,
    modifier: String (optional),
    parenthetic: String (optional),
    matched: String (optional),
    substitutions (optional): [...]
}
```

Here:
* The `text` element is the original `text` element from the unprocessed recipe
* The `name` element is the short ingredient name extracted from the `text`.
* The `quantity_str` and `unit` are the associated Strings extracted corresponding to a number and unit stating the quantity of the ingredient described in `text`. `quantity` converts `quantity_str` into an Integer type. 
* The `modifier` and `parenthetic` elements are for debugging and should be ignored.
* The `substitutions` elements are lists of substituted ingredients that the parser interprets as being stated in the original `text` element.


For example the following processed `ingredient` element appears in the first recipe in the original json :

```js
{
   'text': '6 ounces penne',
   'name': 'penne',
   'unit': 'oz',
   'quantity_str': '6',
   'quantity': 6
}
```

The following is an example of an ingredient with a substitutions list.

```
{
    'text': 12 cup butter or 12 cup margarine, melted
	'name': butter
    'unit': 'cup',
    'quantity_str': '12',
    'quantity': 0.5,
	'substitutions': [
	    {
	        'name': 'margarine, melted',
	        'unit': 'cups',
	        'quantity_str': '12',
	        'quantity': 0.5
        }
    ]
}
```

Here we can see that a poorly captured quantity of 12 was interpreted as a fractional value (due to the singular form of the unit).
