import unittest
import json
import repurposing.text.ingredients as ingredients_module
from repurposing.text.ingredients import process_ingredient
from repurposing.text.ingredients import process_recipe_ingredients



class Test(unittest.TestCase):
    """
    The basic class that inherits unittest.TestCase
    """

    # test case function to check the Person.set_name function
    def test_00_process_ingredient_std(self):
        test_data_fname_input = 'process_ingredient_std_input.json'
        test_data_fname_target = 'process_ingredient_std_target.json'
        self.process_ingredient_standard_tester(
                    test_data_fname_input,
                    test_data_fname_target)

            
    # test case function to check the Person.set_name function
    def test_01_process_ingredient_outer_subs(self):
        test_data_fname_input = 'process_ingredient_outer_subs_input.json'
        test_data_fname_target = 'process_ingredient_outer_subs_target.json'
        self.process_ingredient_substitution_tester(
            test_data_fname_input,
            test_data_fname_target)

    # test case function to check the Person.set_name function
    def test_02_process_ingredient_inner_subs_named(self):
        """
        Inner substitutions that appear within the quantified name of the
        ingredient
        """
        test_data_fname_input = 'process_ingredient_inner_subs_named_input.json'
        test_data_fname_target = 'process_ingredient_inner_subs_named_target.json'
        self.process_ingredient_substitution_tester(
            test_data_fname_input,
            test_data_fname_target)

    def test_03_process_ingredient_problematic(self):
        test_data_fname_input = 'process_ingredient_problematic_input.json'
        test_data_fname_target = 'process_ingredient_problematic_target.json'
        self.process_ingredient_standard_tester(
                    test_data_fname_input,
                    test_data_fname_target)

    def test_04_is_equipment_std(self):
        """
        Inner substitutions that appear within the quantified name of the
        standard parsing of the ingredient.
        """
        test_data_dir = 'tests/text'
        test_data_fname_input = 'is_equipment_strings_std.json'
        input_fpath = test_data_dir+'/'+test_data_fname_input
        #
        with open(input_fpath,'r') as input_file:
            input_data = json.load(input_file)
        for input_ingr in input_data:
            test_ingr, is_equipment = process_ingredient(input_ingr)
            self.assertTrue(is_equipment)

    def test_05_process_recipe_ingredients_std(self):
        """
        Full recipe processing (standard cases)
        """
        test_data_dir = 'tests/text'
        test_data_fname_input = 'process_recipe_ingredients_std_input.json'
        test_data_fname_target = 'process_recipe_ingredients_std_target.json'
        input_fpath = test_data_dir+'/'+test_data_fname_input
        target_fpath = test_data_dir+'/'+test_data_fname_target        
        #
        with open(input_fpath,'r') as input_file:
            input_data = json.load(input_file)
        with open(target_fpath,'r') as target_file:
            target_data = json.load(target_file)
            
        for input_recipe, target_recipe in zip(input_data, target_data):
            test_recipe = process_recipe_ingredients(input_recipe)
            test_ingredients = test_recipe['ingredients']
            target_ingredients = target_recipe['ingredients']
            mainkeys = ['name', 'unit', 'quantity']
            subkeys = ['name', 'unit', 'quantity']
            for test_ingr, target_ingr in zip(test_ingredients, target_ingredients):
                self.check_ingr_and_subs(
                    test_ingr, target_ingr, mainkeys, subkeys)
            test_equipment = test_recipe.get('equipment',[])
            target_equipment = target_recipe.get('equipment',[])
            equipkeys = ['text']
            for test_equip, target_equip in zip(test_equipment, target_equipment):
                self.check_dict_contents(
                    test_equip, target_equip, equipkeys)


    def process_ingredient_standard_tester(
            self, test_data_fname_input,
            test_data_fname_target):
        test_data_dir = 'tests/text'
        input_fpath = test_data_dir+'/'+test_data_fname_input
        target_fpath = test_data_dir+'/'+test_data_fname_target        
        #
        with open(input_fpath,'r') as input_file:
            input_data = json.load(input_file)
        with open(target_fpath,'r') as target_file:
            target_data = json.load(target_file)
        for input_ingr, target_ingr in zip(input_data, target_data):
            #print(f"testing: {target_ingr}")
            test_ingr, is_equipment = process_ingredient(input_ingr)
            self.assertFalse(is_equipment)
            self.check_dict_contents(
                test_ingr, target_ingr, ['name', 'unit', 'quantity'])

    def process_ingredient_substitution_tester(
            self, test_data_fname_input,
            test_data_fname_target):
        test_data_dir = 'tests/text'
        input_fpath = test_data_dir+'/'+test_data_fname_input
        target_fpath = test_data_dir+'/'+test_data_fname_target        
        #
        with open(input_fpath,'r') as input_file:
            input_data = json.load(input_file)
        with open(target_fpath,'r') as target_file:
            target_data = json.load(target_file)
        for input_ingr, target_ingr in zip(input_data, target_data):
            test_ingr, is_equipment = process_ingredient(input_ingr)
            self.assertFalse(is_equipment)
            self.check_dict_contents(
                test_ingr, target_ingr, ['name', 'unit', 'quantity'])
            for subs_ingr in  target_ingr.get('substitutions', []):
                self.check_dict_contents(
                    test_ingr, target_ingr, ['name', 'unit', 'quantity'])

    def check_dict_contents(self, test_dict, target_dict, keys):
#        text = target_dict['text']
        for key in keys:
            if key in target_dict:
                target_val = target_dict[key]
                test_val = test_dict[key]
                if key == 'quantity' and type(target_val) is list:
                    target_val = tuple(target_val)
                try:
                    self.assertEqual(test_val, target_val,
                        f'Mismatch value: key={key}, test={test_val}, target={target_val}\nFor text: {target_dict.get("text")}')
                except:
                    print(f"\ntest_dict = {test_dict}")
                    print(f"target_dict = {target_dict}")
                    raise
            else:
                self.assertFalse(key in test_dict,
                    f'Should not find: {key} for {target_dict} in {test_dict}')

    def check_ingr_and_subs(self, test_ingr, target_ingr, mainkeys, subkeys):
            self.check_dict_contents(
                test_ingr, target_ingr, mainkeys)
            target_subs = target_ingr.get('substitutions', [])
            test_subs = test_ingr.get('substitutions',[])
            self.assertEqual(len(test_subs), len(target_subs))
            for test_subs_ingr, target_subs_ingr in zip(test_subs, target_subs):
                self.check_dict_contents(
                    test_subs_ingr, target_subs_ingr, subkeys)


if __name__ == '__main__':
    pass
