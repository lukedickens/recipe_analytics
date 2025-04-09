from fractions import Fraction
import itertools
import re
import spacy
nlp = spacy.load('en_core_web_lg')
import inflect
inflect_engine = inflect.engine()

# equipment
base_equipment = [
    'pan', 'paper', 'cutter', 'cooker', 'scraper', 'bowl',
    'toothpicks']
re_possible_equipment = re.compile(fr"({'|'.join(base_equipment)})")

juicy_things = ['oranges?', 'lemons?', 'limes?', 'grapefruits?', 'tangerines?',
               'mango', 'mangoes', '(?:rasp|black|blue|cran|straw)(?:berry|berries)',
               'ginger', 'garlic', 'carrots?', 'clementines?', 'pomegranates?',
               'apples?', '(?:cherry|cherries)', 'plums?', 'oysters?', 'clams?',
               'coconuts?', '(?:water)?melons?', 'tomato(?:es)?', 'tangelo']
explicit_quantifiers_and_vals = [
    ('an?',1), ('one',1), ('two',2), ('three',3), ('four',4), ('five',5), ('six',6),
    ('seven',7), ('eight',8), ('nine',9), ('ten',10), ('(?:a )?half(?: of)?',0.5),
     ('(?:a )?quarter(?: of)?',0.25)
    ]
explicit_quantifiers = [qstr for qstr, _ in explicit_quantifiers_and_vals]
quantifiers = explicit_quantifiers + ['[1-9][0-9/ ]*']

#more_than_juice = [
#    'seeds?', '(?:grated )(?:rind|zest|peel)', 'juice', 'and'
#    ]
more_than_juice = [
    'seeds?', 'grated', 'rind','zest','peel', 'juice', 'and', 'skin',
    ]
#re_juice_of = re.compile(fr"((?:{' |'.join(more_than_juice)})+(?:of |from ))({'|'.join(quantifiers)} )?(?:whole )?(?:fresh )?({'|'.join(juicy_things)})")
re_juice_of = re.compile(fr"((?:{' |'.join(more_than_juice)})+(?:of |from ))({'|'.join(quantifiers)} )?(?:the |a )?((?:[a-z]* )*(?:{'|'.join(juicy_things)}))")
re_juicy_thing = re.compile(rf"({'|'.join(juicy_things)})")
re_juice_of_confounds = re.compile(r"juice of (?:your) choice")


size_res = ['small', 'medium', 'med\\.?', 'large', 'lr?g\\.?']
# units
std_unit_aliases = {}
arbitrary_unit_aliases = {}
# std_unit_res = 
std_unit_aliases['in'] = ['inche?s?', 'in', '\"']
std_unit_aliases['cm'] = ['cms?']
std_unit_aliases['fl oz'] = ['fl\\.? oz\\.?', 'fluid ounces?']
std_unit_aliases['pt'] = ['pints?', 'pts?\\.?']
std_unit_aliases['qt'] = ['quarts?\\.?', 'qts?\\.?']
std_unit_aliases['gal'] = ['gals?\\.?', 'gallons?']
std_unit_aliases['lb'] = ['lbs?\\.?', 'pounds?']
std_unit_aliases['g'] = ['grms?\\.?', 'grams?', 'grammes?', 'gs?\\.?']
std_unit_aliases['kg'] = ['kilograms?', 'kilogramme?s?', 'kgs?\\.?']
std_unit_aliases['ml'] = ['mls?', 'milliliters?', 'millilitres?']
std_unit_aliases['l'] = ['liters?', 'litres?', 'l\\.?']
std_unit_aliases['tsp'] = ['teaspoons?', 'tspn?s?\\.?']
std_unit_aliases['tbsp'] = ['tablespoons?', 'tbsp?n?s?\\.?']
std_unit_aliases['oz'] = ['ounces?\\.?', 'ozs?\\.?']
std_unit_aliases['cups'] = ['cups?', 'c\\.']
## counts and fractions
std_unit_aliases['whole'] = ['whole']
std_unit_aliases['half'] = ['half', 'halves']
std_unit_aliases['dozens'] = ['dozens?\\.?']
# ?? scores, braces ??
# arbitrary_unit_res
arbitrary_unit_aliases['bags'] = ['bags?']
arbitrary_unit_aliases['balls'] = ['balls?']
arbitrary_unit_aliases['bars'] = ['bars?']
arbitrary_unit_aliases['barspoons'] = ['barspoons?']
arbitrary_unit_aliases['batches'] = ['batch(?:es)?']
arbitrary_unit_aliases['blocks'] = ['blocks?']
arbitrary_unit_aliases['bottles'] = ['bottles?']
arbitrary_unit_aliases['boxes'] = ['box(?:es)?']
arbitrary_unit_aliases['bunches'] = ['bunche?s?','bn']
arbitrary_unit_aliases['cans'] = ['cans?\\.?']
arbitrary_unit_aliases['cartons'] = ['cartons?\\.?']
arbitrary_unit_aliases['cloves'] = ['cloves?', 'cloves? of', 'clvs?\\.?']
arbitrary_unit_aliases['containers'] = ['containers?\\.?']
arbitrary_unit_aliases['dashes'] = ['dashe?s?', 'dsh\\.?']
arbitrary_unit_aliases['drops'] = ['drops?']
arbitrary_unit_aliases['drizzle'] = ['drizzles?', 'drizzles? of']
arbitrary_unit_aliases['envelopes'] = ['envelopes?']
arbitrary_unit_aliases['grinds'] = ['grinds?']
arbitrary_unit_aliases['handfuls'] = ['handfuls?']
arbitrary_unit_aliases['heads'] = ['heads?']
arbitrary_unit_aliases['jars'] = ['jars?']
arbitrary_unit_aliases['knobs'] = ['knobs?']
arbitrary_unit_aliases['leaves'] = ['leaf', 'leaves']
arbitrary_unit_aliases['legs'] = ['legs?']
arbitrary_unit_aliases['loaves'] = ['loaf', 'loaves']
arbitrary_unit_aliases['packets'] = ['packets?', 'pkts?\\.?']
arbitrary_unit_aliases['packages'] = ['packages?', 'pkgs?\\.?']
arbitrary_unit_aliases['pieces'] = ['pieces?']
arbitrary_unit_aliases['pinches'] = ['pinche?s?','pchs?\\.?']
arbitrary_unit_aliases['pouches'] = ['pouche?s?']
arbitrary_unit_aliases['racks'] = ['racks?']
arbitrary_unit_aliases['rashers'] = ['rashers?']
arbitrary_unit_aliases['scoops'] = ['scoops?']
arbitrary_unit_aliases['sheets'] = ['sheets?']
arbitrary_unit_aliases['slices'] = ['slices?', 'slcs?\\.?']
arbitrary_unit_aliases['sprigs'] = ['sprigs?', 'sprgs?\\.']
arbitrary_unit_aliases['stalks'] = ['stalks?']
arbitrary_unit_aliases['sticks'] = ['sticks?']
arbitrary_unit_aliases['strips'] = ['strips?']
arbitrary_unit_aliases['taste'] = ['taste']
arbitrary_unit_aliases['tins'] = ['tins?']
arbitrary_unit_aliases['tubs'] = ['tubs?']
unit_aliases = std_unit_aliases | arbitrary_unit_aliases
all_std_unit_res = list(itertools.chain(*std_unit_aliases.values()))
all_arbitrary_unit_res = list(itertools.chain(*arbitrary_unit_aliases.values()))
all_unit_res = all_std_unit_res + all_arbitrary_unit_res
std_unit_res_map = {
    k:re.compile(fr"(?:{'|'.join(aliases)})") \
        for k, aliases in std_unit_aliases.items()}
arbitrary_unit_res_map = {}
for k, aliases in arbitrary_unit_aliases.items():
#    print(f"k, aliases = {(k, aliases)}")
    arbitrary_unit_res_map[k ] = re.compile(fr"(?:{'|'.join(aliases)})")
#arbitrary_unit_res_map = {
#    k:re.compile(fr"(?:{'|'.join(aliases)})") \
#        for k, aliases in arbitrary_unit_aliases.items()}

unit_res_map = std_unit_res_map | arbitrary_unit_res_map

def unit_belongs_to(unit, unit_res_map):
    for unit_re in unit_res_map.values():
        if unit_re.fullmatch(unit):
            return True
    return False

def is_compound_unit(unit, std_unit_res_map, arbitrary_unit_res_map):
    unit = unit.replace('-', ' ')
    unit = unit.replace('  ', ' ')
    tokens = unit.split(' ')
    if len(tokens) < 2:
        return False
    subtoks = re.split('(\d+)',tokens[-2])
    if len(subtoks) == 3:
        tokens
    if not len(tokens) in [3,4]:
        return False
    if not unit_belongs_to(tokens[-2], std_unit_res_map):
        return False
    if not unit_belongs_to(tokens[-1], arbitrary_unit_res_map):
        return False
    return True
    
def is_simple_unit(unit, unit_res_map):
    if find_canonical_unit_simple(unit, unit_res_map) is None:
        return False
    return True
    
def find_canonical_unit_simple(unit, unit_res_map):
    for canonical, unit_re in unit_res_map.items():
        if unit_re.fullmatch(unit):
            return canonical
    return None

def find_canonical_unit_compound(
        unit, std_unit_res_map, arbitrary_unit_res_map):
    unit = unit.replace('-', ' ')
    unit = unit.replace('  ', ' ')
    tokens = unit.split(' ')
    tokens[-2] = find_canonical_unit_simple(tokens[-2], std_unit_res_map)
    tokens[-1] = find_canonical_unit_simple(tokens[-1], arbitrary_unit_res_map)
    return ' '.join(tokens)

def find_canonical_unit(
        unit, std_unit_res_map, arbitrary_unit_res_map):
    if is_compound_unit( unit, std_unit_res_map, arbitrary_unit_res_map):
        return find_canonical_unit_compound(
            unit, std_unit_res_map, arbitrary_unit_res_map)
    unit_res_map = std_unit_res_map | arbitrary_unit_res_map
    return find_canonical_unit_simple(unit, unit_res_map)


# old unit stuff
#std_unit_res = [
#    'pounds?', 'c\\.', 'teaspoons?', 'tsps?\\.?', 'tablespoons?', 'tbsps?\\.?',
#    'tbs\\.?', 
#    'inche?s?', 'cups?', 'dozen',
#    'lbs?\\.?', 'ounces?\\.?', 'ozs?\\.?', 'fl\\.? oz\\.?', 'fluid ounces?',
#    'pints?', 'quarts?', 'ml',
#    'gals?\\.?', 'gallons?', 'grm',
#    'grams?', 'grammes?', 'g', 'kilograms?', 'kilogramme?s?', 'kgs?',
#    'liters?', 'litres?',
#    'whole']
#arbitrary_unit_res = [
#    'cans?\\.?', 'tins?', 'bottles?', 
#    'packages?', 'pkgs?\\.?', 'packets?', 'pkts?\\.?', 'pouche?s?', 'drops?', 'racks?', 'slices?',
#    'cloves?', 'sticks?', 'jars?', 'tubs?', 'heads?', 'stalks?', 'sprigs?', 
#    'leaf', 'leaves', 'loaf', 'loaves',
#    'pinche?s?', 'dashe?s?', 'bunche?s?', 'blocks?', 'barspoons?', 'sheets?', 'bags?', 'envelopes?', 'handfuls?']
#all_unit_res = std_unit_res + arbitrary_unit_res


# parsing the ingredient string (first way)
re_numerics_str = fr"((?:[0-9]|/| |\.|\-|x|to|{'|'.join(explicit_quantifiers)})*)"
#re_ingredient_all_parts = fr"^\*?\-? ?([0-9/ \.\-x]+)( \((.*?)\))?( ({'|'.join(all_unit_res+size_res)}))*( \((.*?)\))? (.*)"
#re_ingredient_all_parts = fr"^\*?\-? ?((?:[0-9/ \.\-x]+|(?:{'|'.join(explicit_quantifiers)} )))( \((.*?)\))?(({'|'.join(all_unit_res)}))*( \((.*?)\))? (.*)"

re_ingredient_all_parts_str = fr"^\*?\-? ?{re_numerics_str}( \((.*?)\))?(({'|'.join(all_unit_res)}))*( \((.*?)\))? (.*)"
re_ingredient_all_parts = re.compile(re_ingredient_all_parts_str)


re_numerics2_str = fr"((?:[0-9]|/| |\.|\-|x|to|\(|\)|{'|'.join(explicit_quantifiers)}|{'|'.join(all_unit_res)})*)"
re_measure_ext_name_str = fr"^\*?\-? ?{re_numerics2_str} (.*)"
re_measure_ext_name = re.compile(re_measure_ext_name_str)


#re_paren = re.compile(r'\((.*?)\)')
re_paren = re.compile(r'\(([^()]*)\)')
re_unit = re.compile(fr"(?:{'|'.join(all_unit_res)})")
re_weighted_containers = re.compile(fr"\([1-9][0-9]?(?: 1/?2)?[ -]*(?:{'|'.join(all_std_unit_res)})\) (?:{'|'.join(all_arbitrary_unit_res)})")
re_weighted_containers_stripped = re.compile(fr"[1-9][0-9]?[ -]*(?:{'|'.join(all_std_unit_res)}) (?:{'|'.join(all_arbitrary_unit_res)})")
re_non_parenthetic_or = "( or (?![^(]*\)))"

def is_plural_unit(unit):
    if unit[-1] == 's':
        return True
    if unit == 'g':
        return True
    return False

def is_range(quantity_str):
    if '-' in quantity_str:
        return True
    if ' to ' in quantity_str:
        return True 
    return False

def is_decimal(sub_quantity_str):
    if '.' in sub_quantity_str:
        return True
    return False

def is_fraction(sub_quantity_str):
    if '/' in sub_quantity_str:
        return True
    return False


def process_quantity_str(quantity_str, unit=''):
    if is_range(quantity_str):
        return process_range_quantity_str(quantity_str, unit)
    return process_single_quantity_str(quantity_str, unit)

def infer_hidden_fraction(value):
    if value == 12:
        return 0.5
    if value == 13:
        return 0.33
    if value == 14:
        return 0.25
    if value == 23:
        return 0.67
    if value == 34:
        return 0.75
    raise ValueError("No hidden fraction rule")
    
def process_single_quantity_str(quantity_str, unit):
    tokens = quantity_str. split(" ")
    parts = []
    for t in tokens:
        parts.append(process_simple_quantity_str(t))
    if len(parts) == 1:
        if (parts[0] in (12,13,14,23,34)) and ((unit == '') or (not is_plural_unit(unit))):
            parts[0] = infer_hidden_fraction(parts[0])
        return parts[0]
    if len(parts) == 2:
        if type(parts[0]) is int:
            if parts[1] in (12,13,14,23,34):
                parts[1] = infer_hidden_fraction(parts[1])
            if parts[1] < 1:
                return parts[0]+parts[1]
        raise ValueError(f"two parts which do not make sense: {parts[0]} and {parts[1]}")    
    raise ValueError("more than two parts to single quantity")    
        
def process_simple_quantity_str(quantity_str):
    if is_fraction(quantity_str):
        return float(Fraction(quantity_str))
    if is_decimal(quantity_str):
        return float(quantity_str)
    try:
        return int(quantity_str)
    except:
        return process_text_quantity(quantity_str)    
        
def process_text_quantity(quantity_str):
    for re_quant, val in explicit_quantifiers_and_vals:
        if re.match(re_quant, quantity_str):
            return val
    raise ValueError(f"cannot process {quantity_str} as text quantity")
    
def process_range_quantity_str(quantity_str, unit):
    tokens = [ t.strip() for t in  quantity_str.split("-")]
    if len(tokens) != 2:
        tokens = [ t.strip() for t in  quantity_str.split(" to ")]
    if len(tokens) == 2:
        l = process_single_quantity_str(tokens[0], unit)
        u = process_single_quantity_str(tokens[1], unit)
        return (l,u)
    raise ValueError("Cannot interpret as ranged quantity")


def get_multipart_match_quantity(parts):
    return parts[0].strip('x ')

def get_multipart_match_extended_name(parts):
    return parts[7]

def split_extended_name(extended_name):
    extended_name = extended_name.strip(' ,')
    name, parenthetic = extract_parenthetic_text(extended_name)
    name, modifier = split_at_first_noun_phrase(name)
    if name[:3] == 'of ':
        name = name[3:]
    return name.strip(), modifier, parenthetic
    
def get_multipart_match_unit(parts):
    return parts[4]

def extract_ingredient_details(
        ingr_text, verbose=False, 
        re_measure_ext_name=re_measure_ext_name,
        re_paren=re_paren,
        **kwargs):
#    re_measure_ext_name = kwargs.get('re_measure_ext_name', re_measure_ext_name)
#    re_paren = kwargs.get('re_paren', re_paren)
    ingr_text = ingr_text.lower()
    multi_parts = re_measure_ext_name.findall(ingr_text)
    if len(multi_parts) == 0:
        if verbose:
            print(f"failed to parse: {ingr_text}")
        return handle_failed_extract_ingredient_details(ingr_text, **kwargs)
    parts = multi_parts[0]
    measure_str = parts[0].strip()
    extended_name = parts[1].strip()
    if verbose:
        print(f"parts={parts}, measure_str={measure_str}, extended_name={extended_name}")
    whole_len = len('whole')
    if measure_str[whole_len:] == 'whole':
        measure_str = measure_str[whole_len:].strip()
        extended_name = 'whole '+extended_name
    try:
        name, modifier, parenthetic = split_extended_name(extended_name)
    except:
        if verbose:
            print("Failed to split extended name")
    if verbose:
        print(f"ingr_text = {ingr_text}")
        print(f"extended_name = {extended_name}")
    updated_ingr = dict(name=name.strip())
    if len(parenthetic) > 0:
        updated_ingr['parenthetic'] = parenthetic
    if not modifier == '':
        len_juice_of = len('juice of')
        if modifier[:len_juice_of] == 'juice of':
            updated_ingr['name'] += ', juice of'
            updated_ingr['modifier'] = modifier[len_juice_of:].strip(' ,')
        else:
            updated_ingr['modifier'] = modifier
    # check for weighted containers (e.g. 16-ounce can)    
    matches_weighted_container = re_weighted_containers.search(measure_str)
    matches_weighted_container_stripped = \
        re_weighted_containers_stripped.search(measure_str)
    if verbose:
        print(f"matches_weighted_container = {matches_weighted_container}")
        print(f"matches_weighted_container_stripped = {matches_weighted_container_stripped}")
    if matches_weighted_container:
        weighted_container = matches_weighted_container.group(0)
        unit = re.sub('(\(|\))', '', weighted_container)
        quantity_str = re_weighted_containers.sub('', measure_str)
        if verbose:
            print("matches weighted container")
            print(f"\tweighted_container = {weighted_container}")
            print(f"\tunit = {unit}")
            print(f"\tquantity_str = {quantity_str}")
    elif matches_weighted_container_stripped:
        weighted_container = matches_weighted_container_stripped.group(0)
        unit = re.sub('(\(|\))', '', weighted_container)
        quantity_str = re_weighted_containers_stripped.sub('', measure_str)
        if verbose:
            print("matches weighted container")
            print(f"\tweighted_container = {weighted_container}")
            print(f"\tunit = {unit}")
            print(f"\tquantity_str = {quantity_str}")
    else:
        measure_str, extracted = extract_parenthetic_text(
            measure_str, re_paren=re_paren)
        unit_match = re_unit.search(measure_str)
        if unit_match:
            unit = unit_match.group(0)
            quantity_str = re_unit.sub('', measure_str)
        else:
            unit = ''
            quantity_str = measure_str
    quantity_str = re.sub('whole' ,'', quantity_str)
    if not unit == '':
        updated_ingr['unit'] = unit
    if not quantity_str == '':
        updated_ingr['quantity_str']=quantity_str.strip()
    if verbose:
        print(f"Before quantity_str processed:\n\tupdated_ingr={updated_ingr}")
    try:
        if 'quantity_str' in updated_ingr:
            quantity = process_quantity_str(
                updated_ingr['quantity_str'], unit=updated_ingr.get('unit',''))
            updated_ingr['quantity'] = quantity
    except ValueError:
        if verbose:
            print("Value raised on quantity")
            print(f"entry:\n{entry}")
        pass
#    print(f"returning from extract_ingredient_details with:\n\t{updated_ingr}")
    if 'unit' in updated_ingr:
        unit = updated_ingr['unit']
        canonical = find_canonical_unit(
            unit, std_unit_res_map, arbitrary_unit_res_map)
        if not canonical is None:
            updated_ingr['unit'] = canonical
        else:
            updated_ingr['unit'] = unit
    return updated_ingr

def extract_ingredient_details_old(
        ingr_text, verbose=False, **kwargs):
    re_ingredient_all_parts= kwargs.get(
        're_ingredient_all_parts', re_ingredient_all_parts)
    ingr_text = ingr_text.lower()
    multi_parts = re.findall(re_ingredient_all_parts, ingr_text)
    if len(multi_parts) == 0:
        if verbose:
            print(f"failed to parse: {ingr_text}")
        return handle_failed_extract_ingredient_details(ingr_text, **kwargs)
    parts = multi_parts[0]
    try:
        quantity_str = get_multipart_match_quantity(parts)
        extended_name = get_multipart_match_extended_name(parts)
        name, modifier, parenthetic = split_extended_name(extended_name)
        updated_ingr = dict(quantity_str=quantity_str, name=name)
        if len(parenthetic) > 0:
            updated_ingr['parenthetic'] = parenthetic
        if not modifier == '':
            updated_ingr['modifier'] = modifier
        unit = get_multipart_match_unit(parts)
        if not unit == '':
            updated_ingr['unit']=unit
    except IndexError:
        raise ValueError(f"unexpectly short list:\n\t{ingr_text}\n\t{parts}")


    if (not parts[2] == '') or (not parts[6] == ''):
        updated_ingr['alt_measure'] = (parts[2] + " " + parts[6]).strip(" ")

    try:
        if 'quantity_str' in updated_ingr:
            quantity = process_quantity_str(
                updated_ingr['quantity_str'], unit=updated_ingr.get('unit',''))
            updated_ingr['quantity'] = quantity
    except ValueError:
        #print("Value raised on quantity")
        #print(f"entry:\n{entry}")
        pass
    

    return updated_ingr

def parse_for_outer_substitutions(ingr_text, verbose=False, **kwargs):
    # Still problems with
    # "6 cups canola or vegetable oil..."
    # "4 tbs. extra-virgin olive oil or 3 tbs. vegetable oil and 1 tbs. walnut oil..."
    # "sunflower or light vegetable oil for deep-frying..."
    # "yukon gold potatoes (optional) or new potato, peeled or scrubbed, halved or quartered if large (optional)"
    # "Savory pie crust for a deep 9 or 10-inch pie pan, recipe follows"
    
    # start by assuming suitable substitution not found
    success = False
    # so it is not a substitutable ingredient and a null return is given
    ingr_dict = None
    if ' or ' in ingr_text:
        if verbose:
            print(f"attempting: {ingr_text}")
        tokens = [ t for t in re.split(re_non_parenthetic_or, ingr_text)
                    if t != " or "]
        proposed_ingr_dicts = []
        if len(tokens) > 1:
            if verbose:
                print("\tmore than one token")
                print(f"\ttokens = {tokens}")
            # possible that substitution is found so indicate success
            success = True
            for t in tokens:
                proposed_ingr_dicts.append(
                    extract_ingredient_details(t, **kwargs))
            #first_has_unit = (len(proposed_ingr_dicts[0]['unit']) > 0)
            #first_has_quantity_str = (len(proposed_ingr_dicts[0]['quantity_str']) > 0)
            if verbose:
                print(f"proposed_ingr_dicts = {proposed_ingr_dicts}")
            first_ingr_dict = proposed_ingr_dicts[0]
            first_has_unit = ('unit' in first_ingr_dict)
            first_has_quantity_str = ('quantity_str' in first_ingr_dict)
            # if the substitutions are not parsed equivalently to the main then
            # this is not successful
            for ingr_dict in proposed_ingr_dicts[1:]:
                has_unit = ('unit' in ingr_dict)
                has_quantity_str = ('quantity_str' in ingr_dict)
                #has_unit = (len(ingr_dict['unit'])>0)
                if has_unit != first_has_unit:
                    success = False
                    if verbose:
                        print(f"\tunit information doesn't match\n\t\t{proposed_ingr_dicts[0]}\n\t\t{ingr_dict}")
                    break
                #has_quantity_str = (len(ingr_dict['quantity_str']) > 0)
                if first_has_quantity_str != has_quantity_str:
                    success = False
                    if verbose:
                        print(f"\tquantity information doesn't match\n\t\t{proposed_ingr_dicts[0]}\n\t\t{ingr_dict}")
                    break
            if success:
                ingr_dict = combine_proposed_ingr_dicts(
                        ingr_text, proposed_ingr_dicts)
#                ingr_dict = {'text':ingr_text}
#                ingr_dict.update(proposed_ingr_dicts[0])
#                ingr_dict['substitutions'] = proposed_ingr_dicts[1:]
                if verbose:
                    print(f"\tsuccess {ingr_dict}")
            else:
                if verbose:
                    print(f"Failed to find outer substitution for:\n\t{ingr_text}")
    return success, ingr_dict
def combine_proposed_ingr_dicts(ingr_text, proposed_ingr_dicts):
    ingr_dict = dict(text=ingr_text)
    ingr_dict.update(proposed_ingr_dicts[0])
    ingr_dict['substitutions'] = proposed_ingr_dicts[1:]
    return ingr_dict
    
        
def is_equipment_string(text):
    return text.startswith(('equipment', 'special equipment'))

def process_equipment_string(text):
    initial_strings = ('equipment', 'special equipment')
    text = text.lower().strip()
    if text.startswith(tuple( s+':' for s in initial_strings)):
        tokens = text.split(':')
        return ':'.join(tokens[1:])
    else:
        for s in initial_strings:
            if text.startswith(s):
                return text[len(s):].strip()
    raise ValueError(f"Unrecognised initial string for equipment:\n\t{text}")
        
def expand_equipment_list(equipment):
    new_equipment = []
    for equip_dict in equipment:
        equip_text = equip_dict['text']
        for sub_equip_text in equip_text.split(';'):
            new_equipment.append(dict(text=sub_equip_text.strip()))
    return new_equipment

def is_note_string(ingr_text):
    return ingr_text.startswith(('note'))

def pop_items_from_list(original, indexes):
    indexes.sort(reverse=True)
    extracted = []
    for i in indexes:
        extracted.insert(0,original.pop(i))
    return extracted, original

def extract_parenthetic_text(text, re_paren=re_paren, **kwargs):
    match = re_paren.search(text)
    if match:
        span = match.span()
        new_text = text[:span[0]] + text[span[1]:]
        final_text, extracted = extract_parenthetic_text(
            new_text, re_paren=re_paren)
        extracted.insert(0,(match.group().strip('()'),span[0], span[1]))
        return final_text, extracted
    return text, []

delimiter_re = re.compile(r',|:|;|- | -')
def split_at_first_noun_phrase(text):
    for m in delimiter_re.finditer(text):
        l = m.span()[0]
        to_try = text[:l]
        remains = text[l+1:]
        #print(f"trying: {to_try}")
        doc = nlp(to_try)
        try:
            sent = next(doc.sents)
        except:
            print(f"text = {text}")
            raise
        #print(f"sent = {sent}")
        #print(f"sent.root.pos_ = {sent.root.pos_}")
        if sent.root.pos_ == 'NOUN':
            return to_try, remains.strip()
    return text.strip(), ""


# juice of special case


def handle_failed_extract_ingredient_details(ingr_text, **kwargs):
#    print(f"Handling failed extraction with\n\t{ingr_text}")
    if 'juice of' in ingr_text:
        #print("Attempting to parse as juice of")
        ingr_dict = parse_as_juice_of_ingredient(ingr_text, **kwargs)
        if not ingr_dict is None:
            return ingr_dict
#    name, modifier, parenthetic = split_extended_name(ingr_text)
#    name, modifier = split_at_first_noun_phrase(ingr_text)
#    updated_ingr = dict(name=name)
#    if len(parenthetic) > 0:
#        updated_ingr['parenthetic'] = parenthetic
#    if not modifier == '':
#        updated_ingr['modifier'] = modifier
    tokens = ingr_text.split(',')
    updated_ingr = dict(name=tokens[0])
    if len(tokens) > 1:
        updated_ingr['modifier'] = ','.join(tokens[1:])
    return updated_ingr

def parse_as_juice_of_ingredient(
        ingr_text, re_juice_of=re_juice_of, re_juicy_thing=re_juicy_thing,
        **kwargs):
    res = re_juice_of.search(ingr_text)
    if not res is None:
        ingr_dict = {}
        ingr_dict['matched'] = res.group(0)
        ingr_dict['quantity_str'] = res.group(2)
        part = res.group(1).strip()
        name = res.group(3).strip()
        name_toks = name.split(' ')
        if not inflect_engine.singular_noun(name_toks[-1]):
            name_toks[-1] = inflect_engine.plural(name_toks[-1])
            name = ' '.join(name_toks)
        ingr_dict['name'] = name + ', ' + part
        ingr_dict['name'] = ingr_dict['name'].strip()
        return ingr_dict
        #print(f"res = {res}")
        #print(f"res.group(0) = {res.group(0)}")
        #print(f"res.group(1) = {res.group(1)}")
        #print(f"res.group(2) = {res.group(2)}")
        #print(f"res.group(3) = {res.group(3)}")
        #print()
    else:
        return None

def process_ingredient(json_ingr, **kwargs):
    """
    Processes an ingredient based on its text. If it finds it is 
    more likely an equipment string, it returns true in the second output
    variable. Otherwise the updated ingredient dictionary is returned with false.
    """
    ingr_text = json_ingr['text'].lower()
    ingr_text = ingr_text.replace('possibly ','') 
#    print(f"ingr_text = {ingr_text}")
    if is_equipment_string(ingr_text):
        is_equipment = True
        return dict(), True
    # parse for substitutions
    try:
        success, ingr_dict = parse_for_outer_substitutions(ingr_text, **kwargs)
    except:
#        print("\tthrows error on parse_for_outer_substitutions")
        success = False
    if not success:
        try:
            ingr_dict = extract_ingredient_details(ingr_text, **kwargs)
        except:
            #ingr_dict = {'text': ingr_text}
            ingr_dict = {} # empty dictionary will not update original
    is_equipment = False
    return ingr_dict, is_equipment

def process_recipe_ingredients(json_recipe, **kwargs):
    equipment_idxs = []
    spotted_equipment = False
    for j, json_ingr in enumerate(json_recipe['ingredients']): 
#        ingr_text = json_ingr['text'].lower()
#        ingr_text = ingr_text.replace('possibly ','') 
#        if is_equipment_string(ingr_text):
#            # store position of any string that looks like
#            # equipment. We'll move to a different list later
#            equipment_idxs.append(j)
#            spotted_equipment = True
#            continue
#        # parse for substitutions
#        try:
#            success, ingr_dict = parse_for_outer_substitutions(ingr_text, **kwargs)
#            num_substitutions += len(ingr_dict['substitutions'])
#        except:
#            #print("\tthrows error on parse_for_outer_substitutions")
#            success = False
#        if not success:
#            try:
#                ingr_dict = extract_ingredient_details(ingr_text, **kwargs)
#            except:
#                #ingr_dict = {'text': ingr_text}
#                ingr_dict = {} # empty dictionary will not update original
#                # if we have previously spotted equipment in ingredient list
#                # and subsequent ingredient lines do not parse as ingredients
#                # it may well also be an equipment description
#                if spotted_equipment:
#                    equipment_idxs.append(j)
        updated_ingr, is_equipment = process_ingredient(json_ingr,**kwargs)
        if is_equipment:
            # if it is recognisd as an equipment string then queue it to be
            # added to the equipment list
            equipment_idxs.append(j)
        else:
            json_ingr.update(updated_ingr)
            ## removed as seems superfluous
#        if not 'text' in json_ingr:
#            raise ValueError('Why no text element in {json_ingr}')
    if len(equipment_idxs) > 0:
        # we have previously identified some ingredients as equipment
        # these are removed from the ingredients list and
        # inserted into their own lists
        equipment, ingredients = pop_items_from_list(
            json_recipe['ingredients'], equipment_idxs)
        for equip_dict in equipment:
            equip_dict['text'] = process_equipment_string(
                equip_dict['text'])
        # it is relatively common to list all equipment with semi-colon
        # separation so we expand such lines to multiple equipment lines
        equipment = expand_equipment_list(equipment)
        json_recipe['equipment'] = equipment
    return json_recipe
    
def process_recipes(recipe_data, **kwargs):
    for json_recipe in recipe_data:
        try:
            process_recipe_ingredients(json_recipe, **kwargs)
        except Exception as e:
            print(f"Failed to process recipe:\n\t{json_recipe}")
            print(f"\t{str(e)}")
        

