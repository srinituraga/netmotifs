import numpy as np
import util

# GIBBS SAMPLING


def gibbs_sample_type(domain_inf, rng, impotent=False):

    T_N = domain_inf.entity_count()

    if impotent:
        print "gibbs_sample_type: IMPOTENT"

    for entity_pos in np.random.permutation(T_N):
        g = domain_inf.remove_entity_from_group(entity_pos)
        if domain_inf.group_size(g) == 0:
            temp_group = g
        else:
            temp_group = domain_inf.create_group(rng)


        groups = domain_inf.get_groups()
        scores = domain_inf.post_pred_map(groups, entity_pos)
        #print entity_pos, scores
        sample_i = util.sample_from_scores(scores)
        new_group = groups[sample_i]

        if impotent:
            new_group = g

        domain_inf.add_entity_to_group(new_group, entity_pos)
        if new_group != temp_group:
            assert domain_inf.group_size(temp_group) == 0
            domain_inf.delete_group(temp_group)

def gibbs_sample_type_nonconj(domain_inf, M, rng, impotent=False, 
                              threadpool = None):
    """
    Radford neal Algo 8 for non-conj models
    
    M is the number of ephemeral clusters
    
    We assume that every cluster in the model is currently used
    
    impotent: if true, we always assign the object back to its original
    cluster. Useful for benchmarking
    
    """
    T_N = domain_inf.entity_count()

    if impotent:
        print "gibbs_sample_type_nonconj IMPOTENT"

    if T_N == 1:
        return # nothing to do 

    for entity_pos in range(T_N):
        g = domain_inf.remove_entity_from_group(entity_pos)
        extra_groups = []
        if domain_inf.group_size(g) == 0:
            extra_groups.append(g)
        while len(extra_groups) < M:
            extra_groups.append(domain_inf.create_group(rng))

        groups = domain_inf.get_groups()
        scores = domain_inf.post_pred_map(groups, entity_pos, 
                                          threadpool)

            # correct the score for the empty groups
        for gi, group_id in enumerate(groups):
            if group_id in extra_groups:
                scores[gi] -= np.log(M)
        #print entity_pos, scores
        sample_i = util.sample_from_scores(scores)
        if impotent: 
            new_group = g
        else:
            new_group = groups[sample_i]

        domain_inf.add_entity_to_group(new_group, entity_pos)
        for eg in extra_groups:
            if domain_inf.group_size(eg) == 0:
                domain_inf.delete_group(eg)

        # for r in domain_inf.relations:
        #     r.assert_assigned()

def gibbs_sample_fixed_k(domain_inf, rng, impotent=False):

    T_N = domain_inf.entity_count()

    if impotent:
        print "gibbs_sample_type: IMPOTENT"

    for entity_pos in np.random.permutation(T_N):
        g = domain_inf.remove_entity_from_group(entity_pos)
        # if domain_inf.group_size(g) == 0:
        #     temp_group = g
        # else:
        #     temp_group = domain_inf.create_group(rng)


        groups = domain_inf.get_groups()
        scores = np.zeros(len(groups))
        for gi, group_id in enumerate(groups):
            scores[gi] = domain_inf.post_pred(group_id, entity_pos)
        #print entity_pos, scores
        sample_i = util.sample_from_scores(scores)
        new_group = groups[sample_i]

        if impotent:
            new_group = g

        domain_inf.add_entity_to_group(new_group, entity_pos)
        # if new_group != temp_group:
        #     assert domain_inf.group_size(temp_group) == 0
        #     domain_inf.delete_group(temp_group)
