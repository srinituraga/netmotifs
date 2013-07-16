from ruffus import *
import cPickle as pickle
import numpy as np
import copy
import os
import time

import irm
import irm.data
from matplotlib import pylab
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import Grid

import cloud
import rand

BUCKET_BASE="srm/experiments/testinf/"

#cloud.start_simulator()

def d(x, y):
    return np.sqrt(np.sum((x - y)**2))

"""
for N connection classes 
for M seeds
    generate the data
    run the regular IRM on it
    run our iIRM on it with 10 different rng inits, 10 different seeds

"""

def to_bucket(filename):
    cloud.bucket.sync_to_cloud(filename, os.path.join(BUCKET_BASE, filename))

def from_bucket(filename):
    return pickle.load(cloud.bucket.getf(os.path.join(BUCKET_BASE, filename)))

CHAINS_TO_RUN = 10
SAMPLER_ITERS = 2000
SEEDS = np.arange(6)

#SKIP = 100
#BURN = 700
def data_generator():

    POSSIBLE_SIDE_N = [10]
    
    conn = {
        'twoclass': {(0, 1) : (2.0, 0.7), 
                         (1, 0) : (3.0, 0.8)},
            'oneclass': {(0, 0) : (2.0, 0.8)}, 
            '3c0' : {(0, 1) : (1.5, 0.5), 
                    (1, 2) : (2.0, 0.3), 
                    (2, 0) : (3.0, 0.8)}, 
            '3c1' : {(0, 1) : (2.0, 0.5), 
                     (1, 2) : (2.0, 0.3), 
                     (0, 2) : (2.0, 0.7),                      
                     (2, 0) : (2.0, 0.8),
                 },
            # much lower probs
            '3c2' : {(0, 1) : (2.0, 0.2), 
                     (1, 2) : (2.0, 0.1), 
                     (0, 2) : (2.0, 0.4),                      
                     (2, 0) : (2.0, 0.2),
                 },
            # change the radius
            '3c3' : {(0, 1) : (1.0, 0.5), 
                     (1, 2) : (1.5, 0.3), 
                     (0, 2) : (2.0, 0.7),                      
                     (2, 0) : (2.5, 0.8),
                 },
            '5c0' : {(0, 1) : (1.0, 0.5), 
                     (1, 2) : (1.5, 0.3), 
                     (0, 2) : (2.0, 0.7),                      
                     (2, 0) : (2.5, 0.8),
                     (2, 3) : (2.5, 0.8),
                     (3, 4) : (2.5, 0.8),
                     (1, 4) : (1.5, 0.4),
                 },
            '10c1' : {(0, 1) : (1.0, 0.5), 
                      (0, 2) : (2.0, 0.7),                      
                      (0, 8) : (2.0, 0.7), 
                      (0, 3) : (1.0, 0.7),                      
                      (1, 4) : (1.5, 0.4),
                      (1, 2) : (1.5, 0.3), 
                      (1, 4) : (1.5, 0.4),
                      (2, 0) : (2.5, 0.6),
                      (2, 3) : (2.1, 0.8),
                      (2, 0) : (2.5, 0.6),
                      (2, 7) : (3.0, 0.7),
                      (3, 4) : (2.5, 0.8),
                      (3, 8) : (2.5, 0.8),
                      (4, 2) : (1.5, 0.3), 
                      (4, 0) : (2.0, 0.8), 
                      (4, 9) : (2.5, 0.7), 
                      (5, 1) : (1.5, 0.3),
                      (5, 6) : (2.0, 0.7), 
                      (5, 5) : (1.0, 0.5), 
                      (6, 2) : (1.5, 0.8), 
                      (6, 7) : (2.1, 0.6), 
                      (7, 0) : (1.5, 0.3), 
                      (7, 4) : (1.2, 0.9), 
                      (8, 2) : (3.0, 0.6), 
                      (8, 5) : (2.0, 0.4), 
                      (9, 8) : (1.0, 0.7), 
                      (9, 1) : (2.3, 0.3),
                      (9, 3) : (1.6, 0.6)
                  },    
            
            
    }

    
    for SIDE_N in POSSIBLE_SIDE_N:
        for seed in SEEDS:
            for conn_name, conn_config in conn.iteritems():
                filename = "data.%d.%d.%s.pickle" % (SIDE_N, seed, conn_name)
                yield None, filename, SIDE_N, seed, conn_name, conn_config

@files(data_generator)
def create_data(inputfile, outputfile, SIDE_N, seed, conn_name, conn_config):
    
    np.random.seed(seed)
    nodes_with_class, connectivity = irm.data.generate.c_class_neighbors(SIDE_N, conn_config)
    
                
    conn_and_dist = np.zeros(connectivity.shape, 
                    dtype=[('link', np.uint8), 
                           ('distance', np.float32)])

    for ni, (ci, posi) in enumerate(nodes_with_class):
        for nj, (cj, posj) in enumerate(nodes_with_class):
            conn_and_dist[ni, nj]['link'] = connectivity[ni, nj]
            conn_and_dist[ni, nj]['distance'] = d(posi, posj)
    pickle.dump({'SIDE_N' : SIDE_N, 
                 'seed' : seed, 
                 'conn_name' : conn_name, 
                 'conn_config' : conn_config, 
                 'nodes' : nodes_with_class, 
                 'connectivity' : connectivity, 
                 'conn_and_dist' : conn_and_dist}, 
                open(outputfile, 'w'))

# def create_inference_ld():
#     INITS = SAMPLER_INITS
#     for x in data_generator():
#         filename = x[1]
#         otherargs = x[2:]
#         for seed in range(INITS):
#             outfilename = "%s.ld.%d.pickle" % (filename, init)
#             yield filename, outfilename, init


def inference_run_ld(latent_filename, 
                     data_filename, 
                     config_filename,  ITERS, seed):

    latent = from_bucket(latent_filename)
    data = from_bucket(data_filename)
    config = from_bucket(config_filename)

    SAVE_EVERY = 100
    chain_runner = irm.runner.Runner(latent, data, config, seed)

    scores = []
    times = []
    def logger(iter, model):
        print "Iter", iter
        scores.append(model.total_score())
        times.append(time.time())
    chain_runner.run_iters(ITERS, logger)
        
    return scores, chain_runner.get_state(), times


@transform(create_data, regex(r"(.+).pickle$"), 
            r"\1.samples." + ("%d" %(SAMPLER_ITERS)) + ".exp")
def create_rundata(infilename, outfilename):
    """
    Create the data to run the experiments
    """

    ITERS = SAMPLER_ITERS

    indata = pickle.load(open(infilename, 'r'))

    model_name= "LogisticDistance" 
    kernel_config = irm.runner.default_kernel_nonconj_config()
    kernel_config[0][1]['M'] = 30

    data = indata['conn_and_dist']
    nodes = indata['nodes']


    irm_latent, irm_data = irm.irmio.default_graph_init(data, model_name)

    HPS = {'mu_hp' : 1.0, 
           'lambda_hp' : 1.0, 
           'p_min' : 0.1, 
           'p_max' : 0.9}
    irm_latent['relations']['R1']['hps'] = HPS
    irm_latents = []
    kernel_configs = []
    for c in range(CHAINS_TO_RUN):
        np.random.seed(c)

        latent = copy.deepcopy(irm_latent)

        GRP = 10
        a = np.arange(latent['domains']['d1']['N']) % GRP
        a = np.random.permutation(a)
    
        latent['domains']['d1']['assignment'] = a
        irm_latents.append(latent)
        kernel_configs.append(kernel_config)

    # the ground truth one
    irm_latent_true = copy.deepcopy(irm_latent)
    irm_latent_true['domains']['d1']['assignment'] = nodes['class']
    irm_latents[0] = irm_latent_true
    
    filenames = {}
    data_filename = outfilename + ".data"

    pickle.dump(irm_data, open(data_filename, 'w'))
    to_bucket(data_filename)
    filenames['data'] = data_filename
    filenames['chains'] = {}
    # filenames
    for c in range(CHAINS_TO_RUN):
        s = outfilename + (".%d" % c)
        latent_filename = s + ".latent"
        config_filename = s + ".config"
        pickle.dump(irm_latents[c], open(latent_filename, 'w'))
        to_bucket(latent_filename)
        pickle.dump(kernel_configs[c], open(config_filename, 'w'))
        to_bucket(config_filename)

        filenames['chains'][c] = {'latent' : latent_filename, 
                                  'config' : config_filename}


    # jids = cloud.map(inference_run_ld, irm_latents,
    #                  [irm_data]*CHAINS_TO_RUN, 
    #                  kernel_configs,
    #                  [ITERS] * CHAINS_TO_RUN, 
    #                  range(CHAINS_TO_RUN), 
    #                  _env='connectivitymotif', 
    #                  _type='f2')

    # fixme save all inputs
    pickle.dump({'infile' : infilename, 
                 'hps' : HPS, 
                 'filenames' : filenames}, 
                open(outfilename, 'w'))

@transform(create_rundata, suffix(".exp"), ".exp.wait")
def start_inference(infilename, outfilename):

    ITERS = SAMPLER_ITERS

    indata = pickle.load(open(infilename, 'r'))
    filenames = indata['filenames']
    data_filename = filenames['data']
    latent_filenames = []
    config_filenames = []
    for chain, v in filenames['chains'].iteritems():
        latent_filenames.append(v['latent'])
        config_filenames.append(v['config'])
    
    jids = cloud.map(inference_run_ld, latent_filenames,
                     [data_filename]*CHAINS_TO_RUN, 
                     config_filenames,
                     [ITERS] * CHAINS_TO_RUN, 
                     range(CHAINS_TO_RUN), 
                     _env='connectivitymotif', 
                     _type='f2')

    # fixme save all inputs
    pickle.dump({'infile' : indata['infile'],
                 'filenames' : filenames,
                 'jids' : jids}, 
                open(outfilename, 'w'))

@transform(start_inference, regex(r"(.+).wait$"), 
            r"\1.pickle")
def get_inference(infilename, outfilename):
    d= pickle.load(open(infilename))
    
    chains = []
    # reorg on a per-seed basis
    for chain_data in cloud.iresult(d['jids'], ignore_errors=True):
        
        chains.append({'scores' : chain_data[0], 
                       'state' : chain_data[1], 
                       'times' : chain_data[2]})
        
        
    pickle.dump({'chains' : chains, 
                 'infile' : infilename}, 
                open(outfilename, 'w'))

GROUP_SIZE_THOLD = 0.85

def group_mass(group_sizes, thold):
    """
    What fraction of the groups account for thold of 
    the data? 

    1. sort the groups by size
    2. add until > thold
    """
    gs_a = np.sort(np.array(group_sizes))[::-1]
    gs_n = gs_a.astype(float) / np.sum(gs_a)
    
    tot = 0
    for i in range(len(gs_n)):
        tot += gs_n[i]
        if tot > thold:
            return i + 1
    return len(gs_n)
    



@transform(get_inference, regex(r"(.+).pickle$"),  
         [r"\1.scores.png", 
          r"\1.counts.pickle", 
          r"\1.params.png"])
def plot_collate(inputfile, (plot_outfile, counts_outfile, 
                             params_outfile)):
    filedata = pickle.load(open(inputfile))
    chains = filedata['chains']
    chains = [c for c in chains if type(c['scores']) != int]
    CHAINN = len(chains)
    
    print "INPUTFILE=", inputfile
    f = pylab.figure()
    ax_score = f.add_subplot(2, 2, 1)
    ax_groups =f.add_subplot(2, 2, 2) 
    ax_params = f.add_subplot(2, 2, 3)
    ax_score_groupcount = f.add_subplot(2, 2, 4)

    param_fig = pylab.figure(figsize=(2, CHAINN))
    #ax_each_chain = [param_fig.add_subplot(CHAINN, 1, i) for i in range(CHAINN)]
    ax_each_chain =  Grid(param_fig, 111, # similar to subplot(111)
                          nrows_ncols = (CHAINN, 1), 
                          axes_pad=0.1, # pad between axes in inch.
                           )

    groupcounts = []
    bins = np.arange(1, 7)

    allscores = []
    meancounts = []
    params_mu = []
    params_lambda = []
    params_comp_size = []
    for di, d in enumerate(chains):
        this_iter_gc = []
        sample_latent = d['state']
        chain_params = {'size' : [], 
                        'lambda' : [], 
                        'mu' : []} 

        a = sample_latent['domains']['d1']['assignment']
        group_sizes = irm.util.count(a)
        gs = group_sizes.values()
        this_iter_gc.append(group_mass(gs, GROUP_SIZE_THOLD))
        components = sample_latent['ss']['R1']

        # this is fun and complex
        unique_gids = np.unique(a)
        for g1 in unique_gids:
            for g2 in  unique_gids:
                c = components[(g1, g2)]
                comp_size = group_sizes[g1] * group_sizes[g2]
                chain_params['lambda'].append(c['lambda'])
                chain_params['mu'].append(c['mu'])
                chain_params['size'].append(comp_size)
        params_mu += chain_params['mu']
        params_lambda += chain_params['lambda']
        params_comp_size += chain_params['size']
        meancounts.append(np.mean(this_iter_gc))
        groupcounts += this_iter_gc

        ax_each_chain[di].scatter(chain_params['mu'], 
                                  chain_params['lambda'], 
                                  alpha = 0.5, s = np.array(chain_params['size'])/200., 
                                  edgecolor='none')
        ax_each_chain[di].set_ylim(0, 0.4)
        ax_each_chain[di].tick_params(axis='both', which='minor',
                                      labelsize=6.0)
        ax_each_chain[di].tick_params(axis='both', which='major',
                                      labelsize=6.0)

    ax_params.scatter(params_mu, params_lambda, alpha=0.5, 
                      s= np.array(params_comp_size)/200., 
                      edgecolor='none')
    ax_params.grid(1)
    ax_params.set_xlabel('mu')
    ax_params.set_ylabel('lambda')

    mymap = mpl.colors.LinearSegmentedColormap.from_list('mycolors',['blue','red'])

    for di, d in enumerate(chains):
        gc_mean = meancounts[di]
        gc_min = np.min(groupcounts)
        gc_max = np.max(groupcounts)
        subsamp = 4
        s = np.array(d['scores'])[::subsamp]
        t = np.array(d['times'])[::subsamp] - d['times'][0]
        ax_score.plot(t, s, alpha=0.7, c='k')
        print d['scores']
        allscores.append(d['scores'])
    sm = pylab.cm.ScalarMappable(cmap=mymap, 
                                 norm=pylab.normalize(vmin=1, vmax=5.0))
    sm._A = []

    f.colorbar(sm)
    all_s = np.hstack(allscores).flatten()
    #r = np.max(all_s) - np.min(all_s)
    #ax_score.set_ylim(np.min(all_s) + r*0.95, np.max(all_s)+r*0.05)
    
    hist, _ = np.histogram(groupcounts, bins)
    print bins, hist
    ax_groups.bar(bins[:-1], hist)
    ax_groups.set_xlim(bins[0], bins[-1])

    scoregroup = []
    for di, d in enumerate(chains):
        assignment = d['state']['domains']['d1']['assignment']
        scores = d['scores']
        a = assignment
        group_sizes = irm.util.count(a)
        scoregroup.append((len(group_sizes), scores[-1]))

    scoregroup = np.array(scoregroup)
    print scoregroup[:, 0].shape, scoregroup[:, 0].dtype
    jitter_counts = scoregroup[:, 0] + np.random.rand(len(scoregroup[:, 0])) * 0.2 -0.1
    ax_score_groupcount.scatter(jitter_counts, 
                                scoregroup[:, 1])

    
    f.tight_layout()

    f.savefig(plot_outfile, dpi=300)

    param_fig.tight_layout()
    param_fig.savefig(params_outfile, dpi=300)
    

    pickle.dump({'counts' : groupcounts}, 
                open(counts_outfile, 'w'))

# @collate(get_inference, regex(r"(.+)\.\d+\.(.+)\.sampleas.+.pickle$"),  
#          r"\1.\2.rand.pdf")
# def rand_collate(inputfiles, rand_plot_filename):

#     all_aris = []
#     f = pylab.figure()
#     for inputfile in  inputfiles:
#         filedata = pickle.load(open(inputfile))
#         start_inference_file =  filedata['infile']
#         start_inference_data = pickle.load(open(start_inference_file))
#         orig_data = pickle.load(open(start_inference_data['infile'], 'r'))

#         nodes = orig_data['nodes']
#         orig_class = nodes['class']

#         chains = filedata['chains']
#         aris = []
#         for di, d in enumerate(chains):
#             assignments = d['states']
#             for S in np.arange(BURN, len(assignments), SKIP):
#                 a = assignments[S]
#                 c_a = rand.canonicalize_assignment_vector(a)
#                 c_orig_class = rand.canonicalize_assignment_vector(orig_class)
#                 ari = rand.compute_adj_rand_index(c_a, c_orig_class)
#                 aris.append(ari)
#         all_aris.append(aris)
#     pylab.boxplot(all_aris)
#     pylab.savefig(rand_plot_filename)

pipeline_run([create_data, start_inference, get_inference, 
              plot_collate, 
              #rand_collate
          ],
             multiprocess=4)
