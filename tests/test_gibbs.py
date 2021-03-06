from nose.tools import * 
import numpy as np
from numpy.testing import assert_approx_equal, assert_array_equal

from matplotlib import pylab

from irm import models
from irm import model
from irm import relation
from irm import util
from irm import gibbs
from irm import pyirm, Relation

def test_gibbs_simple(rng=None):
    """
    Test the gibbs sampling code by treating
    it as a simple mixture model with the negative variance model
    
    Max score == all T1 rows in own groups

    """
    
    T1_N = 10
    T2_N = 20

    data = np.arange(T1_N * T2_N)
    data.shape = T1_N, T2_N

    m =  models.NegVarModel()
    r = relation.Relation([('T1', T1_N), ('T2', T2_N)], 
                     data,m)
    hps = m.create_hps()
    hps['offset'] = 0.3

    r.set_hps(hps)

    tf_1 = model.DomainInterface(T1_N, {'r': ('T1', r)})
    tf_1.set_hps({'alpha' : 1.0})
    tf_2 = model.DomainInterface(T2_N, {'r': ('T2', r)})
    tf_2.set_hps({'alpha' : 1.0})

    ### All one group for everyone
    t1_g1 = tf_1.create_group(rng)
    for i in range(T1_N):
        tf_1.add_entity_to_group(t1_g1, i)

    t2_g1 = tf_2.create_group(rng)
    for i in range(T2_N):
        tf_2.add_entity_to_group(t2_g1, i)

    
    ITERS = 10
    for i in range(ITERS):
        gibbs.gibbs_sample_type(tf_1, rng)
    assert_equal(len(np.unique(tf_1.get_assignments())), 10)

def test_gibbs_beta_bernoulli():
    gibbs_beta_bernoulli(relation.Relation)

def test_gibbs_beta_bernoulli_fast():
    gibbs_beta_bernoulli(relation.FastRelation)

def test_gibbs_beta_bernoulli_fast():
    rng = pyirm.RNG()
    gibbs_beta_bernoulli(Relation, rng)

def gibbs_beta_bernoulli(relation_class, rng=None):
    """
    Test with real beta-bernoulli data. Should find the two class x two class
    grouping

    """

    
    T1_N = 40
    T2_N = 40
    np.random.seed(0)

    data = np.zeros((T1_N, T2_N) , dtype=np.bool)
    data.shape = T1_N, T2_N
    data[:10, :10] = True
    data[10:, 10:] = True
    # add noise 
    NOISE = 0.1
    for i in range(T1_N):
        for j in range(T1_N):
            if np.random.rand() < NOISE:
                data[i, j] = not data[i, j]


    data = data[np.random.permutation(T1_N)]
    data = data[:, np.random.permutation(T2_N)]

    m =  models.BetaBernoulli()
    r = relation_class([('T1', T1_N), ('T2', T2_N)], 
                     data,m)
    hps = m.create_hps()

    r.set_hps(hps)

    tf_1 = model.DomainInterface(T1_N, {'r' : ('T1', r)})
    tf_1.set_hps({'alpha' : 1.0})
    tf_2 = model.DomainInterface(T2_N, {'r': ('T2', r)})
    tf_2.set_hps({'alpha': 1.0})


    ### All one group for everyone
    t1_g1 = tf_1.create_group(rng)
    for i in range(T1_N):
        tf_1.add_entity_to_group(t1_g1, i)

    t2_g1 = tf_2.create_group(rng)
    for i in range(T2_N):
        tf_2.add_entity_to_group(t2_g1, i)

    
    ITERS = 10
    for i in range(ITERS):
        gibbs.gibbs_sample_type(tf_1, rng)
        gibbs.gibbs_sample_type(tf_2, rng)
        print tf_1.get_assignments()
        print tf_2.get_assignments()

    assert_equal(len(np.unique(tf_1.get_assignments())), 2)
    assert_equal(len(np.unique(tf_2.get_assignments())), 2)
    # pylab.subplot(1, 2, 1)
    # pylab.imshow(data, interpolation='nearest', 
    #              cmap=pylab.cm.gray)
    # t1_idx = np.argsort(tf_1.get_assignments()).flatten()
    # t2_idx = np.argsort(tf_2.get_assignments()).flatten()
    # im_srt = data[t1_idx]
    # im_srt = im_srt[:, t2_idx]
    # pylab.subplot(1, 2, 2)
    # pylab.imshow(im_srt, interpolation='nearest', 
    #              cmap=pylab.cm.gray)
    # pylab.show()
                
if __name__ == "__main__":
    test_gibbs_beta_bernoulli()
