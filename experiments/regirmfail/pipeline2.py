from ruffus import *
import cPickle as pickle
import numpy as np
import copy
import os, glob
import time
from matplotlib import pylab
import pandas
import rand
from sklearn import metrics

import irm
import irm.data

def dist(a, b):
    return np.sqrt(np.sum((b-a)**2))



BUCKET_BASE="srm/experiments/regirmfail"


EXPERIMENTS = [('trivial', 'fixed_4_10', 'default50'), 
               ('trivial', 'fixed_4_10', 'default_anneal_400'), 
               ('class_compare', 'fixed_10_40', 'default_anneal_400'),
               #('class_compare_gen', 'fixed_10_40', 'default_anneal_400'),
               #('class_compare_frac', 'fixed_10_40', 'default_anneal_400'),
               #('class_compare_big', 'fixed_10_40', 'default_anneal_400')
           ]

INIT_CONFIGS = {'fixed_4_10' : {'N' : 4, 
                             'config' : {'type' : 'fixed', 
                                         'group_num' : 10}}, 
                'fixed_10_40' : {'N' : 10, 
                                'config' : {'type' : 'fixed', 
                                            'group_num' : 40}}, 
                'fixed_10_100' : {'N' : 10, 
                                'config' : {'type' : 'fixed', 
                                            'group_num' : 100}}}
                

default_nonconj = irm.runner.default_kernel_nonconj_config()
default_anneal = irm.runner.default_kernel_anneal()


KERNEL_CONFIGS = {'default50' : {'ITERS' : 50, 
                                 'kernels' : default_nonconj}, 
                  'default_anneal_400' : {'ITERS' : 400, 
                                          'kernels' : default_anneal}, 
              }

pickle.dump(default_nonconj, open('kernel.config', 'w'))

def dataset_connectivity_matrix_params():
    datasets = {
                'trivial' : {'seeds' : range(1), 
                             'side_n' : [4], 
                             'class_n' : [2], 
                             'nonzero_frac' : [1.0], 
                             'jitter' : [0.001], 
                             'models' : ['bb', 'ld'], 
                             'truth': ['distblock']},
                'class_compare' : {'seeds' : range(5), 
                                   'side_n' : [8], 
                                   'class_n' : [1, 2, 4, 8, 16], 
                                   'nonzero_frac' : [1.0], 
                                   'jitter' : [0.001], 
                                   'models' : ['bb', 'ld'], 
                                   'truth': ['distblock']}, 
                'class_compare_frac' : {'seeds' : range(5), 
                                   'side_n' : [8], 
                                   'class_n' : [1, 2, 4, 8, 16], 
                                   'nonzero_frac' : [0.1, 0.2, 0.5, 1.0], 
                                   'jitter' : [0.001], 
                                   'models' : ['bb', 'ld'], 
                                   'truth': ['distblock']}, 
                'class_compare_gen' : {'seeds' : range(5), 
                                       'side_n' : [8], 
                                       'class_n' : [1, 2, 4, 8, 16], 
                                       'nonzero_frac' : [1.0], 
                                       'jitter' : [0.001], 
                                       'models' : ['bb', 'ld'], 
                                       'truth': ['distblock', 'mixedblock', 'bumpblock']}, 
                'class_compare_big' : {'seeds' : range(5), 
                                       'side_n' : [16], 
                                       'class_n' : [1, 2, 4, 8], 
                                       'nonzero_frac' : [1.0], 
                                       'jitter' : [0.001], 
                                       'models' : ['bb', 'ld'], 
                                       'truth': ['distblock']}

    }
    
    for dataset_name, ds in datasets.iteritems():
        for side_n in ds['side_n']:
            for class_n in ds['class_n']:
                for nonzero_frac in ds['nonzero_frac']:
                    for jitter in ds['jitter']:

                        for seed in ds['seeds']:
                            for model in ds['models']:
                                for truth in ds['truth']:

                                    filename_base = "data.%s.%s.%s.%d.%d.%3.3f.%3.3f.%s" % (dataset_name, model, truth, side_n, class_n, nonzero_frac, jitter, seed)

                                    yield None, [filename_base + ".data", 
                                                 filename_base + ".latent", 
                                                 filename_base + ".meta"], model, truth,  seed, side_n, class_n, nonzero_frac, jitter

def generate_block_config(class_n, nonzero_frac):
    conn_config = {}

    for c1 in range(class_n):
        for c2 in range(class_n):
            if np.random.rand() < nonzero_frac:
                conn_config[(c1, c2)] = (np.random.uniform(1.0, 4.0), 
                                         np.random.uniform(0.1, 0.9))
    if len(conn_config) == 0:
        conn_config[(0, 0)] = (np.random.uniform(1.0, 4.0), 
                               np.random.uniform(0.4, 0.9))
    return conn_config

def generate_block_config_poisson(class_n, nonzero_frac):
    conn_config = {}

    for c1 in range(class_n):
        for c2 in range(class_n):
            if np.random.rand() < nonzero_frac:
                conn_config[(c1, c2)] = (np.random.uniform(1.0, 4.0),  # threshold
                                         np.random.exponential(20))
    if len(conn_config) == 0:
        conn_config[(0, 0)] = (np.random.uniform(1.0, 4.0), 
                               np.random.exponential(20))
    return conn_config

def generate_mixed_block_config(class_n, nonzero_frac):
    conn_config = {}

    BLOCK_SWITCH = 0.5
    for c1 in range(class_n):
        for c2 in range(class_n):
            if np.random.rand() < nonzero_frac:
                if np.random.rand() < BLOCK_SWITCH:
                    conn_config[(c1, c2)] = ('p', np.random.uniform(0.1, 0.9))
                else:
                    conn_config[(c1, c2)] = ('d', 
                                             np.random.uniform(1.0, 4.0), 
                                             np.random.uniform(0.1, 0.9))
                    
                                             
    if len(conn_config) == 0:
        conn_config[(0, 0)] = ('d', np.random.uniform(1.0, 4.0), 
                               np.random.uniform(0.4, 0.9))
    return conn_config
    
def generate_bump_block_config(class_n, nonzero_frac):
    conn_config = {}

    for c1 in range(class_n):
        for c2 in range(class_n):
            if np.random.rand() < nonzero_frac:
                conn_config[(c1, c2)] = (np.random.uniform(1.0, 4.0), 
                                         np.random.uniform(0.5, 0.9), 
                                         np.random.uniform(0.2, 0.3))
    if len(conn_config) == 0:
        conn_config[(0, 0)] = (np.random.uniform(1.0, 4.0), 
                               np.random.uniform(0.4, 0.9), 
                               np.random.uniform(0.2, 0.3))
    return conn_config


@files(dataset_connectivity_matrix_params)
def dataset_connectivity_matrix(infile, (data_filename, latent_filename, 
                                         meta_filename), 
                                model, truth_gen, seed, side_n, class_n, nonzero_frac, jitter):

    import irm.data.generate as generate

    np.random.seed(seed)
    if truth_gen == 'distblock':
        conn_config = generate_block_config(class_n, nonzero_frac)
        obsmodel = irm.observations.Bernoulli()

        nodes_with_class, connectivity = generate.c_class_neighbors(side_n, 
                                                                    conn_config,
                                                                    JITTER=jitter, 
                                                                    obsmodel=obsmodel)
    elif truth_gen == 'mixedblock':
        conn_config = generate_mixed_block_config(class_n, nonzero_frac)
        obsmodel = irm.observations.Bernoulli()

        nodes_with_class, connectivity = generate.c_mixed_dist_block(side_n, 
                                                                     conn_config,
                                                                     JITTER=jitter, 
                                                                     obsmodel=obsmodel)
    elif truth_gen == 'bumpblock':
        conn_config = generate_bump_block_config(class_n, nonzero_frac)
        obsmodel = irm.observations.Bernoulli()

        nodes_with_class, connectivity = irm.data.generate.c_bump_dist_block(side_n, 
                                                                             conn_config,
                                                                             JITTER=jitter, 
                                                                             obsmodel=obsmodel)
    elif truth_gen == 'distblock_count':
        conn_config = generate_block_config_poisson(class_n, nonzero_frac)
        obsmodel = irm.observations.Poisson()

        nodes_with_class, connectivity = irm.data.generate.c_class_neighbors(side_n, 
                                                                             conn_config,
                                                                             JITTER=jitter, 
                                                                             obsmodel=obsmodel)
    
        
    print "The obsmodel dtype is", obsmodel.dtype
    conn_and_dist = np.zeros(connectivity.shape, 
                             dtype=[('link', obsmodel.dtype), 
                                    ('distance', np.float32)])
    print "conn_and_dist.dtype", conn_and_dist.dtype
    for ni, (ci, posi) in enumerate(nodes_with_class):
        for nj, (cj, posj) in enumerate(nodes_with_class):
            conn_and_dist[ni, nj]['link'] = connectivity[ni, nj]
            conn_and_dist[ni, nj]['distance'] = dist(posi, posj)

            
    meta = {'SIDE_N' : side_n,
            'seed' : seed, 
            'class_n' : class_n, 
            'conn_config' : conn_config, 
            'nodes' : nodes_with_class, 
            'connectivity' : connectivity, 
            'conn_and_dist' : conn_and_dist}

    # now create the latents

    if model == 'ld':
        model_name= "LogisticDistance" 

        HPS = {'mu_hp' : 1.0, 
               'lambda_hp' : 1.0, 
               'p_min' : 0.1, 
               'p_max' : 0.9}

    elif model == 'bb':
        model_name= "BetaBernoulli"
        conn_and_dist = conn_and_dist['link'] # we should prob do this smarter
        HPS = {'alpha' : 1.0, 
               'beta' : 1.0}

    elif model == 'lind':
        model_name= "LinearDistance"

        HPS = {'mu_hp' : 1.0, 
               'p_alpha' : 1.0, 
               'p_beta': 1.0, 
               'p_min' : 0.01}

    elif model == 'sd':
        model_name= "SigmoidDistance"

        HPS = {'lambda_hp' : 1.0, 
               'mu_hp' : 1.0, 
               'p_max': 0.9, 
               'p_min' : 0.1}

    elif model == 'ndfw':
        model_name= "NormalDistanceFixedWidth"

        HPS = {'p_alpha' : 1.0, 
               'p_beta' : 1.0, 
               'mu_hp' : 1.0, 
               'p_min' : 0.01, 
               'width' : 0.2}

    elif model == 'sdb':
        model_name= "SquareDistanceBump"

        HPS = {'p_alpha' : 1.0, 
               'p_beta' : 1.0, 
               'mu_hp' : 1.0, 
               'p_min' : 0.01, 
               'param_weight' : 0.5, 
               'param_max_distance' : 4.0}
    elif model == 'expdp':
        model_name= "ExponentialDistancePoisson"

        HPS = {'mu_hp' : 1.0, 
               'rate_scale_hp' : 1.0}

    irm_latent, irm_data = irm.irmio.default_graph_init(conn_and_dist, model_name)
    irm_latent['domains']['d1']['assignment'] = nodes_with_class['class']

    # FIXME is the assignment vector ground-truth here? 

    irm_latent['relations']['R1']['hps'] = HPS

    pickle.dump(irm_latent, open(latent_filename, 'w'))
    pickle.dump(irm_data, open(data_filename, 'w'))
    pickle.dump(meta, open(meta_filename, 'w'))




def create_init(latent_filename, out_filenames, 
                init= None):
    """ 
    CONVENTION: when we create N inits, the first is actually 
    initialized from the "ground truth" of the intial init (whatever
    that happened to be)
    """
    irm_latent = pickle.load(open(latent_filename, 'r'))
    
    irm_latents = []

    for c, out_f in enumerate(out_filenames):
        np.random.seed(c)

        latent = copy.deepcopy(irm_latent)

        if init['type'] == 'fixed':
            group_num = init['group_num']

            a = np.arange(len(latent['domains']['d1']['assignment'])) % group_num
            a = np.random.permutation(a)

        elif init['type'] == 'crp':
            alpha = init['alpha']
        else:
            raise NotImplementedError("Unknown init type")
            
        if c > 0: # first one stays the same
            latent['domains']['d1']['assignment'] = a

        # delete the suffstats
        if 'ss' in latent['relations']['R1']:
            del latent['relations']['R1']['ss']

        pickle.dump(latent, open(out_f, 'w'))



# def create_inference_ld():
#     INITS = SAMPLER_INITS
#     for x in data_generator():
#         filename = x[1]
#         otherargs = x[2:]
#         for seed in range(INITS):
#             outfilename = "%s.ld.%d.pickle" % (filename, init)
#             yield filename, outfilename, init


def get_dataset(data_name):
    return glob.glob("data.%s.*.data" %  data_name)

def init_generator():
    for data_name, init_config_name, kernel_config_name in EXPERIMENTS:
        for data_filename in get_dataset(data_name):
            name, _ = os.path.splitext(data_filename)

            yield data_filename, ["%s.%d.init" % (name, i) for i in range(INIT_CONFIGS[init_config_name]['N'])], init_config_name, INIT_CONFIGS[init_config_name]


            
            # inits  = get_init(data_name, init_config_name)
            # kernel = get_kernel_conf(kernel_config_name)

            # experiment_filename = "%s-%s-%s.experiment" % (data_filename, init_config_name, kernel_config_name)

            # exp = {'data' : data_filename, 
            #        'inits' : inits, 
            #        'kernel' : kernel}

            #pickle.dump(exp, open(experiment_filename, 'w'))

@follows(dataset_connectivity_matrix)
@files(init_generator)
def create_inits(data_filename, out_filenames, init_config_name, init_config):
    basename, _ = os.path.splitext(data_filename)
    latent_filename = basename + ".latent"

    create_init(latent_filename, out_filenames, 
                init= init_config['config'])

def experiment_generator():
    for data_name, init_config_name, kernel_config_name in EXPERIMENTS:
        for data_filename in get_dataset(data_name):
            name, _ = os.path.splitext(data_filename)

            inits = ["%s.%d.init" % (name, i) for i in range(INIT_CONFIGS[init_config_name]['N'])]
            
            exp_name = "%s-%s-%s.wait" % (data_filename, init_config_name, kernel_config_name)
            yield [data_filename, inits], exp_name, kernel_config_name

@follows(create_inits)
@files(experiment_generator)
def run_exp((data_filename, inits), wait_file, kernel_config_name):
    # put the filenames in the data
    irm.experiments.to_bucket(data_filename, BUCKET_BASE)
    [irm.experiments.to_bucket(init_f, BUCKET_BASE) for init_f in inits]

    kc = KERNEL_CONFIGS[kernel_config_name]
    CHAINS_TO_RUN = len(inits)
    ITERS = kc['ITERS']
    kernel_config = kc['kernels']
    init_type = kc.get('init', None)
    
    jids = cloud.map(irm.experiments.inference_run, inits, 
                     [data_filename]*CHAINS_TO_RUN, 
                     [kernel_config]*CHAINS_TO_RUN,
                     [ITERS] * CHAINS_TO_RUN, 
                     range(CHAINS_TO_RUN), 
                     [BUCKET_BASE]*CHAINS_TO_RUN, 
                     [init_type]*CHAINS_TO_RUN, 
                     _env='connectivitymotif', 
                     _type='f2')

    pickle.dump({'jids' : jids, 
                'data_filename' : data_filename, 
                'inits' : inits, 
                'kernel_config_name' : kernel_config_name}, 
                open(wait_file, 'w'))


@transform(run_exp, suffix('.wait'), '.samples')
def get_results(exp_wait, exp_results):
    
    d = pickle.load(open(exp_wait, 'r'))
    
    chains = []
    # reorg on a per-seed basis
    for chain_data in cloud.iresult(d['jids'], ignore_errors=True):
        
        chains.append({'scores' : chain_data[0], 
                       'state' : chain_data[1], 
                       'times' : chain_data[2], 
                       'latents' : chain_data[3]})
        
        
    pickle.dump({'chains' : chains, 
                 'exp' : d}, 
                open(exp_results, 'w'))

def parse_filename(fn):
     data_part = fn.split('-')[0]
     s = data_part.split(".")
     print "S=", s
     s.pop(0)
     dataset_name = s[0]
     model = s[1]
     truth = s[2]
     side_n = int(s[3])
     class_n = int(s[4])
     nonzero_frac = float(s[5] + '.' + s[6])
     jitter = float(s[7] + '.' + s[8])
     seed = int(s[9])
     return {'dataset_name' : dataset_name, 
             'model' : model, 
             'truth' : truth, 
             'side_n' : side_n, 
             'class_n' : class_n, 
             'nonzero_frac' : nonzero_frac, 
             'jitter' : jitter, 
             'seed' : seed}


@transform(get_results, suffix(".samples"), [".latent.pdf"])
def plot_latent(exp_results, (plot_latent_filename, )):
    sample_d = pickle.load(open(exp_results))
    chains = sample_d['chains']
    
    exp = sample_d['exp']
    data_filename = exp['data_filename']
    data = pickle.load(open(data_filename))
    data_basename, _ = os.path.splitext(data_filename)
    meta = pickle.load(open(data_basename + ".meta"))


    nodes_with_class = meta['nodes']
    conn_and_dist = meta['conn_and_dist']

    true_assignvect = nodes_with_class['class']

    chains = [c for c in chains if type(c['scores']) != int]
    CHAINN = len(chains)
    print "CHAINN =", CHAINN
    f = pylab.figure(figsize= (12, 8))
    ax_purity_control = f.add_subplot(2, 2, 1)
    ax_z = f.add_subplot(2, 2, 2)
    ax_score = f.add_subplot(2, 2, 3)
    
    ###### plot purity #######################
    ###
    tv = true_assignvect.argsort()
    tv_i = true_assignvect[tv]
    vals = [tv_i]
    # get the chain order 
    chains_sorted_order = np.argsort([d['scores'][-1] for d in chains])[::-1]
    sorted_assign_matrix = []
    for di in chains_sorted_order: 
        d = chains[di] 
        sample_latent = d['state']
        a = np.array(sample_latent['domains']['d1']['assignment'])
        print "di=%d unique classes:"  % di, np.unique(a)
        sorted_assign_matrix.append(a)
    irm.plot.plot_purity(ax_purity_control, true_assignvect, sorted_assign_matrix)

    ###### zmatrix
    av = [np.array(d['state']['domains']['d1']['assignment']) for d in chains]
    z = irm.util.compute_zmatrix(av)    

    irm.plot.plot_zmatrix(ax_z, z)

    ### Plot scores
    for di, d in enumerate(chains):
        subsamp = 4
        s = np.array(d['scores'])[::subsamp]
        print "SCORES ARE", s
        t = np.array(d['times'])[::subsamp] - d['times'][0]
        if di == 0:
            ax_score.plot(t, s, alpha=0.7, c='r', linewidth=3)
        else:
            ax_score.plot(t, s, alpha=0.7, c='k')

    ax_score.tick_params(axis='both', which='major', labelsize=6)
    ax_score.tick_params(axis='both', which='minor', labelsize=6)
    ax_score.set_xlabel('time (s)')
    ax_score.grid(1)
    
    file_params = parse_filename(exp_results)
    f.suptitle(str(file_params))

    f.savefig(plot_latent_filename)
    
@merge(get_results, "merge.pickle")
def merge_results(exp_results, merge_filename):
    results = []
    for exp_result in exp_results:
        sample_d = pickle.load(open(exp_result))
        chains = sample_d['chains']
        chains = [c for c in chains if type(c['scores']) != int]

        exp = sample_d['exp']
        data_filename = exp['data_filename']
        data = pickle.load(open(data_filename))
        data_basename, _ = os.path.splitext(data_filename)
        meta = pickle.load(open(data_basename + ".meta"))


        nodes_with_class = meta['nodes']
        conn_and_dist = meta['conn_and_dist']

        true_assignvect = nodes_with_class['class']
        params = parse_filename(exp_result)
        scores = [d['scores'][-1] for d in chains]
        chains_sorted_order = np.argsort(scores)[::-1]

        for ci, di in enumerate(chains_sorted_order): 
            d = chains[di] 
            sample_latent = d['state']

            a = np.array(sample_latent['domains']['d1']['assignment'])

            result = {'chain_pos' : ci, 
                      'chain_id' : di, 
                      'assign' : a, 
                      'score' : d['scores'][-1], 
                      'true_assign' : true_assignvect, 
                      'node_pos' : nodes_with_class['pos']}
            result.update(params)
            results.append(result)
    df = pandas.DataFrame(results)
    pickle.dump(df, open(merge_filename, 'w'))

PLOT_DATASETS = ['class_compare', 'class_compare_big']
#@follows(merge_results) # messing with this to just debug plotting
# without running all experiments

@files("merge.pickle", [('%s.rand.pdf' % c, '%s.ari.pdf' % c, 
                        '%s.spatial_variance.pdf' % c) for c in PLOT_DATASETS])
def plot_results(infile, outfiles):
    df = pickle.load(open(infile, 'r'))
    
    df['ari'] = df.apply(lambda row: rand.compute_adj_rand_index(row['true_assign'], 
                                                                 irm.util.canonicalize_assignment(row['assign'])), axis=1)
    df['empirical_class_n'] = df.apply(lambda row : len(np.unique(row['assign'])), axis=1)

    for plot_files, dataset_name in zip(outfiles, PLOT_DATASETS):
        
        df_cc = df[df['dataset_name'] == dataset_name]

        a = df_cc.groupby(['dataset_name', 'jitter', 'model', 'nonzero_frac', 'class_n', 
                           'side_n', 'seed', 'truth']).apply(lambda group: group.sort_index(by='score', ascending=False).head(1))
        colors = {'bb' : 'b', 
                   'ld' : 'r'}
        f = pylab.figure(figsize=(4, 3))
        ax = f.add_subplot(1, 1, 1)
        labels = {'bb' : "conn only", 
                  'ld' : "conn + dist"}
        for g_idx, g in a.groupby(['model']):
            ax.scatter(g.index.get_level_values('class_n'), g['empirical_class_n'], c=colors[g_idx],
                          edgecolor='none', label= labels[g_idx])
        ax.plot([1, 16], [1, 16], c='k', label="ground truth")
        ax.set_xlabel("true type number")
        ax.set_ylabel("estimated type number")
        ax.set_xticks([1, 2, 4, 8, 16])
        ax.legend(loc="upper left", fontsize=10)
        ax.set_yticks([0, 70])
        ax.set_ylim([-2, 70])
        for tic in ax.yaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False

        f.tight_layout()
        for tic in ax.xaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
        spines_to_remove = ['top', 'right']
        for spine in spines_to_remove:
            ax.spines[spine].set_visible(False)

        f.savefig(plot_files[0])


        colors = {'bb' : 'b', 
                   'ld' : 'r'}
        offsets = {'bb' : 0.0, 
                   'ld' : 1.0}
        f = pylab.figure(figsize=(4, 3))
        ax = f.add_subplot(1, 1, 1)
        CLASS_SPACE = 2.5
        WIDTH = 0.8

        N = 0
        for g_idx, g in a.groupby(['model']):
            h =  g.groupby(['class_n']).mean()
            herr = g.groupby(['class_n']).std()
            N= len(h)
            ax.bar(np.arange(N)*CLASS_SPACE + offsets[g_idx], h['ari'], width=WIDTH, 
                    color=colors[g_idx])
            ax.errorbar(np.arange(N)*CLASS_SPACE + offsets[g_idx] + WIDTH/2, 
                        h['ari'], yerr= herr['ari'], capsize=0,elinewidth=2, linewidth=0, ecolor='black')
        #ax.plot([1, 16], [1, 1], c='k')
        ax.set_xlabel("true type number")
        ax.set_ylabel("Cluster accuracy (ARI)")
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0.0, 1.0])
        ax.set_xticks(np.arange(N)*CLASS_SPACE + 1)
        ax.set_xticklabels([1, 2, 4, 8, 16])
        for tic in ax.xaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
        spines_to_remove = ['top', 'right']
        for spine in spines_to_remove:
            ax.spines[spine].set_visible(False)

        f.tight_layout()
        f.savefig(plot_files[1])


        ## The future 

        def cluster_var(row):
            assign = row['assign']
            true_assign = row['true_assign']
            print type(row['node_pos'])
            node_pos = row['node_pos']
            def node_to_df(assign, nodes):
                return pandas.DataFrame({'cluster' : assign, 'x' : node_pos[:, 0], 
                                    'y' : node_pos[:, 1], 'z' : node_pos[:, 2]})

            rdf1 = node_to_df(assign, node_pos)
            rdf1['truth'] = False

            rdf2 = node_to_df(true_assign, node_pos)
            rdf2['truth'] = True

            rdf = pandas.concat([rdf1, rdf2])
            rdf[['x', 'y', 'z']] = rdf[['x', 'y', 'z']].astype(float)


            return rdf.groupby(['truth', 'cluster']).var()

        #a = df_cc.groupby(['dataset_name', 'jitter', 'model', 'nonzero_frac', 'class_n', 
        #                    'side_n', 'seed', 'truth']).apply(lambda group: group.sort_index(by='score', ascending=False).head(1))
        df_vars = []
        for rid, r in a.iterrows():
            cv = cluster_var(r.to_dict())
            cv['model'] = r['model']
            cv['seed'] = r['seed']
            cv['class_n'] = r['class_n']
            df_vars.append(cv)
        df_vars = pandas.concat(df_vars)
        df_vars['truth'] = df_vars.index.get_level_values('truth')
        df_vars['std'] = np.sqrt(df_vars['x'] + df_vars['y'])

        f = pylab.figure(figsize=(4.0, 6.5))
        bins = np.linspace(0, 3.5, 20)
        
        bin_width = (bins[1] - bins[0])
        bar_width = bin_width/4.0
        bar_space = bin_width/3.

        for i, class_n in enumerate([4, 8, 16]):
            ax = f.add_subplot(3, 1, i + 1)

            for model_i, (model, color) in enumerate([('bb', 'b'), 
                                                      ('ld', 'r'),]):
                df2 = df_vars[(df_vars['model'] == model) & (df_vars['class_n']==class_n) & (df_vars['truth']==False)]
                hist, _ = np.histogram(df2.dropna()['std'], bins=bins, density=True)
                ax.bar(bins[:-1] + model_i * bar_space, hist*bin_width, width=bar_width, color=color, 
                       label=model, linewidth=0.0)
                       

            df2 = df_vars[(df_vars['model'] == model) & (df_vars['class_n']==class_n) & (df_vars['truth']==True)]
            hist, _ = np.histogram(df2.dropna()['std'], bins=bins, density=True)
            print "Histogram=", hist
            ax.bar(bins[:-1] + 2*bar_space, hist*bin_width,
                   width=bar_width, color='k', 
                   label='truth',  linewidth=0.0)
            ax.set_yticks([0.0, 1.0])
            ax.set_ylim(0.0, 1.05)
            ax.set_ylabel("frac (class=%d)" % class_n)
            ax.set_xticks([0.0, 3.5])
            if i == 0:
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, [   
                    'conn only', 
                    'conn + dist', 
                    'Ground Truth', 
                                    ], 
                          loc='upper left', 
                          fontsize=12)
            if i < 2:
                ax.set_xticklabels([])

            for tic in ax.xaxis.get_major_ticks():
                tic.tick1On = tic.tick2On = False
            for tic in ax.yaxis.get_major_ticks():
                tic.tick1On = tic.tick2On = False
            spines_to_remove = ['top', 'right']
            for spine in spines_to_remove:
                ax.spines[spine].set_visible(False)


        ax.set_xlabel("size of clusters (2D std dev)")
        f.tight_layout()
        f.savefig(plot_files[2])


@files(merge_results, ['manygen.rand.pdf', 'manygen.ari.pdf'])
def plot_results_many_gen(infile, outfiles):
    df = pickle.load(open(infile, 'r'))
    
    df['ari'] = df.apply(lambda row: rand.compute_adj_rand_index(row['true_assign'], 
                                                                 irm.util.canonicalize_assignment(row['assign'])), axis=1)
    df['empirical_class_n'] = df.apply(lambda row : len(np.unique(row['assign'])), axis=1)

    df_cc = df[(df['dataset_name'] == 'class_compare_gen') & (df['model'] == 'ld')]

    a = df_cc.groupby(['dataset_name', 'jitter', 'nonzero_frac', 'class_n', 
                       'side_n', 'seed', 'truth']).apply(lambda group: group.sort_index(by='score', ascending=False).head(1))

    colors = {'distblock' : 'b', 
              'mixedblock' : 'r', 
              'bumpblock' : 'g'}
    f = pylab.figure(figsize=(4, 3))
    ax = f.add_subplot(1, 1, 1)

    for g_i, (g_idx, g) in enumerate(a.groupby(['truth'])):
        ax.scatter(g.index.get_level_values('class_n') + 0.3*g_i, 
                   g['empirical_class_n'], c=colors[g_idx],
                   edgecolor='none')
    ax.plot([1, 16], [1, 16], c='k')
    ax.set_xlabel("true class number")
    ax.set_ylabel("estimated class number")
    ax.set_xticks([1, 2, 4, 8, 16])
    f.tight_layout()
    f.savefig(outfiles[0])


    colors = {'distblock' : 'b', 
              'mixedblock' : 'r', 
              'bumpblock' : 'g'}

    offsets = {'distblock' : 0.0,
               'mixedblock' : 1.0, 
               'bumpblock' : 2.0}

    f = pylab.figure(figsize=(4, 3))
    ax = f.add_subplot(1, 1, 1)
    CLASS_SPACE = 3.5
    WIDTH = 0.8

    N = 0
    for g_idx, g in a.groupby(['truth']):
        h =  g.groupby(['class_n']).mean()
        herr = g.groupby(['class_n']).std()
        N= len(h)
        print "g_idx", g_idx, h['ari']
        ax.bar(np.arange(N)*CLASS_SPACE + offsets[g_idx], h['ari'], width=WIDTH, 
               color=colors[g_idx])
        ax.errorbar(np.arange(N)*CLASS_SPACE + offsets[g_idx] + WIDTH/2, 
                    h['ari'], yerr= herr['ari'], 
                    capsize=0,elinewidth=4,ecolor='k', linewidth=0)

    ax.set_xlabel("true class number")
    ax.set_ylabel("adjusted rand index")
    ax.set_ylim(0, 1.0)
    ax.set_xticks(np.arange(N)*CLASS_SPACE + 1)
    ax.set_xticklabels([1, 2, 4, 8, 16])
    f.tight_layout()
    f.savefig(outfiles[1])

if __name__ == "__main__":
    pipeline_run([#dataset_connectivity_matrix, create_inits, run_exp, 
                  #get_results, plot_latent,
        #merge_results, 
        plot_results, 
        #plot_results_many_gen
              ], multiprocess=3)

