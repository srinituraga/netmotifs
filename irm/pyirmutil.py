import numpy as np
import pyirm
import models

class Relation(object):
    def __init__(self, relation_def, data, modeltype = None):

        if isinstance(modeltype, models.BetaBernoulli):
            modeltypestr = "BetaBernoulli"
        elif isinstance(modeltype, models.AccumModel):
            modeltypestr = "AccumModel"
        self.compcontainer = pyirm.create_component_container(data.tostring(), 
                                                              data.shape, 
                                                              modeltypestr)
        self.domain_mapper = {}
        self.domain_sizes = []
        self.axes_domain_num = []
        for axispos, (domain_name, domain_size) in enumerate(relation_def):
            if domain_name not in self.domain_mapper:
                self.domain_mapper[domain_name] = len(self.domain_mapper)
                self.domain_sizes.append(domain_size)
            self.axes_domain_num.append(self.domain_mapper[domain_name])

        self.relation = pyirm.PyRelation(self.axes_domain_num, 
                                         self.domain_sizes, 
                                         self.compcontainer)
        
    # simple wrappers
    
    def create_group(self, domainname):
        return self.relation.create_group(self.domain_mapper[domainname])

    def delete_group(self, domainname, gid):
        return self.relation.delete_group(self.domain_mapper[domainname], 
                                          gid)
    def add_entity_to_group(self, domainname, gid, ep):
        return self.relation.add_entity_to_group(self.domain_mapper[domainname], 
                                                 gid, ep)

    def remove_entity_from_group(self, domainname, gid, ep):
        return self.relation.remove_entity_from_group(self.domain_mapper[domainname],
                                                      gid, ep)
    def post_pred(self, domainname, gid, ep):
        return self.relation.post_pred(self.domain_mapper[domainname],
                                    gid, ep)
        
    def total_score(self):
        return self.relation.total_score()
        
    def set_hps(self, hps):
        self.compcontainer.set_hps(hps)
