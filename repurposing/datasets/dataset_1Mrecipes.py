import os

INSUBDIR = 'data/1M+recipes'
fstem_template = 'layer1'
sfx_template = '_%.2d'
extension = '.json'
procstem_template = 'proc%d'

## to move to generic module
def date_to_datestr(date):
    return date.strftime("%y%m%d")

def get_outsubdir(datestr):
    """
    date - in format 
    """
    outsubdir = 'data/repurposing/%s' % datestr
    os.makedirs(outsubdir, exist_ok=True)
    return outsubdir


def get_filenames(fname_template, N):
    fnames = []
    for i in range(1,N+1):
        fstem = fstem_template % (i,) 
        fname = fname_template % (fstem,)
        fnames.append(fname)
    return fnames

def get_rawnames(N=15):
    rawname_template = fstem + sfx_template + extension
    return get_filenames(rawname_template, N)

def get_procnames(N=15, processing_step=1):
    procname_template = fstem + procstem_template % (processing_step,)
    procname_template += sfx_template + extension
    return get_filenames(procname_template, N)


def expand_fnames(subdir, fnames):
    paths = []
    for fname in fnames:
        paths.append(os.path.join(subdir, fname))
    return paths

def get_rawpaths(N=15):
    fnames = get_rawnames(N)
    paths = expand_fnames(INSUBDIR, fnames)
    return paths
    
def get_procpaths(N=15, datestr=None):
    if datestr is None:
        datestr = "220718"
    subdir = get_outsubdir(datestr)
    fnames = get_procnames(N)
    paths = expand_fnames(subdir, fnames)
    return paths


# 
#def load_data
#    with open(ifpath,'r') as ifile:
#        recipe_data = json.load(ifile)
#    process_recipes(recipe_data)
#    with open(ofpath,'w') as ofile:
#        json.dump(recipe_data, ofile, indent=4)

