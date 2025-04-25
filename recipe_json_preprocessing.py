from datetime import date
import os
import json

from repurposing.text.ingredients import process_recipes

## TODO: use some of the general functionality for filenames
## and the like from this module
#import repurposing.datasets.dataset_1Mrecipes
from repurposing.file_io.paths import get_rawpaths
from repurposing.file_io.paths import get_procpaths


def singlefile_process(ifpath, ofpath):
    print(f"Processing json recipes from {ifpath} and saving to {ofpath}")
    with open(ifpath,'r') as ifile:
        recipe_data = json.load(ifile)
    process_recipes(recipe_data)
    with open(ofpath,'w') as ofile:
        json.dump(recipe_data, ofile, indent=4)
    print()

def multifile_process(
        input_subdir=None, output_subdir=None,
        max_ifile_id=15, min_ifile_id=1):
    # TODO: currently hardcoded for 1Mdatasets
    if output_subdir is None:
        today = date.today()
        output_subdir = today.strftime("%y%m%d")
    print(f"Saving to subdir {output_subdir}")
#    insubdir = 'data/1M+recipes'
#    output_subdir = 'data/repurposing/%s' % today.strftime("%y%m%d")
#    os.makedirs(output_subdir, exist_ok=True)
    ifpaths = get_rawpaths(
        maxid=max_ifile_id, minid=min_ifile_id)
    ofpaths = get_procpaths(
        output_subdir, maxid=max_ifile_id, minid=min_ifile_id)
    for ifpath, ofpath in zip(ifpaths, ofpaths):
        singlefile_process(ifpath, ofpath)        
#    fstem_template = 'layer1_%.2d'
#    ifname_template = '%s.json'
#    ofname_template = '%s_proc%d.json'
#    processing_step = 1
#    for i in range(1,16):
#        fstem = fstem_template % (i,) 
#        ifname = ifname_template % (fstem,)
#        ofname = ofname_template % (fstem,processing_step)
#        ifpath = os.path.join(input_subdir, ifname)
#        ofpath = os.path.join(output_subdir, ofname)
#        print(f"fstem = {fstem}")
#        print(f"ifname = {ifname}")
#        print(f"ofname = {ofname}")
#        singlefile_process(ifpath, ofpath)        
#        with open(ifpath,'r') as ifile:
#            recipe_data = json.load(ifile)
#        process_recipes(recipe_data)
#        with open(ofpath,'w') as ofile:
#            json.dump(recipe_data, ofile, indent=4)
    print("Done")

def create_parser():
    description= """
        Parses recipe database 1M+recipes to converge ingredient
        strings (and possibly other parts) to be more informative"""
    parser = argparse.ArgumentParser(
        description=description,
        epilog='See git repository readme for more details.')
    parser.add_argument('--ifpath', '-i', type=str,
        help='Path of input (json) file (single file only)')
    parser.add_argument('--ofpath', '-o', type=str,
        help='Path of input (json) file (single file only)')
    # multifile option
    parser.add_argument('--input-subdir', type=str, default='1M+recipes',
        help='Input subdirectory for data')
    parser.add_argument('--output-subdir', type=str,
        help='Input subdirectory for data')
    parser.add_argument('--max-ifile-id', type=int, default=15,
        help='Maximum input file id for processing')
    parser.add_argument('--min-ifile-id', type=int, default=1,
        help='Minimum input file id for processing')

    return parser

def main(ifpath=None, ofpath=None, **kwargs):
    if (not ifpath is None) and (not ofpath is None):
        singlefile_process(ifpath, ofpath)
    else:
        # assumes multifile
        multifile_process(**kwargs)

if __name__ == '__main__':
    import argparse
    args = create_parser().parse_args()
    main(**vars(args))    
    
