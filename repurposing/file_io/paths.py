import os

FSTEM = 'layer1'
SFX_TEMPLATE = '_%.2d'
EXTENSION = '.json'
PROCSTEM_TEMPLATE = '_proc%d'
DATADIR = 'data'
RECIPE1MDIR = os.path.join(DATADIR,'1M+recipes')
OUTDATADIR = os.path.join(DATADIR, 'repurposing')

## to move to generic module
def date_to_datestr(date):
    return date.strftime("%y%m%d")

def get_outdir(subdir, outparentdir=OUTDATADIR):
    """
    date - in format 
    """
    outsubdir = os.path.join(outparentdir, subdir)
    os.makedirs(outsubdir, exist_ok=True)
    return outsubdir
# ensure there is an export dir
EXPORTDIR = get_outdir('export')

def get_filenames(
        fname_template, maxid, minid=1):
    fnames = []
    for i in range(minid,maxid+1):
        fname = fname_template % (i,)
        fnames.append(fname)
    return fnames

def get_rawnames(
        maxid, minid=1, fstem=FSTEM, sfx_template=SFX_TEMPLATE,
        extension=EXTENSION):
    rawname_template = fstem + sfx_template + extension
    return get_filenames(rawname_template, maxid=maxid, minid=minid)

def get_procnames(
        maxid, minid=1, processing_step=1, fstem=FSTEM,
        sfx_template=SFX_TEMPLATE, extension=EXTENSION,
        procstem_template=PROCSTEM_TEMPLATE):
    procname_template = fstem + procstem_template % (processing_step,)
    procname_template += sfx_template + extension
    return get_filenames(procname_template, maxid=maxid, minid=minid)


def expand_fnames(dir_, fnames):
    paths = []
    for fname in fnames:
        paths.append(os.path.join(dir_, fname))
    return paths

def get_rawpaths(maxid, dir_=RECIPE1MDIR, **kwargs):
    fnames = get_rawnames(maxid, **kwargs)
    paths = expand_fnames(dir_, fnames)
    return paths


def get_jsonpath(fname, dir_=None):
    if dir_ is None:
        dir_=EXPORTDIR
    paths = expand_fnames(dir_, [fname])
    return paths[0]
    
def get_procpaths(subdir, maxid, minid=1, processing_step=1, **kwargs):
    fnames = get_procnames(maxid, processing_step=processing_step, **kwargs)
    dir_ = get_outdir(subdir)
    paths = expand_fnames(dir_, fnames)
    return paths


# 
#def load_data
#    with open(ifpath,'r') as ifile:
#        recipe_data = json.load(ifile)
#    process_recipes(recipe_data)
#    with open(ofpath,'w') as ofile:
#        json.dump(recipe_data, ofile, indent=4)

