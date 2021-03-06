#include <unistd.h>

#include <boost/python.hpp>
#include <boost/python/class.hpp>
#include <boost/utility.hpp>
#include "util.h"
#include "relation.h"
#include "parrelation.h"
#include "componentcontainer.h"
#include "componentmodels.h"
#include "pyirm_helpers.h"

namespace bp=boost::python; 

//class template irm::ComponentContainer<irm::BetaBernoulli>; 

using namespace irm; 

std::string helloworld() {
    return "Shot through the heart, and you're to blame -- you give love a bad name!" ; 

}

IComponentContainer * create_component_container(std::string data, bp::tuple data_dims, 
                                                 std::string observed, 
                                                 std::string modeltype) 
{
    auto data_dims_v = extract_vect<size_t>(data_dims); 
    
    if(modeltype == "BetaBernoulli") { 
        IComponentContainer * cc = new ComponentContainer<BetaBernoulli>(data, data_dims_v, observed);  
        return cc; 
     } else    if(modeltype == "GammaPoisson") { 

        IComponentContainer * cc = new ComponentContainer<GammaPoisson>(data, data_dims_v, observed);  
        return cc; 
     } else    if(modeltype == "NormalInverseChiSq") { 

        IComponentContainer * cc = new ComponentContainer<NormalInverseChiSq>(data, data_dims_v, observed);  
        return cc; 
    }     else if(modeltype == "BetaBernoulliNonConj") { 
        IComponentContainer * cc = new ComponentContainer<BetaBernoulliNonConj>(data, data_dims_v, observed);  
        return cc; 
    } else if(modeltype == "AccumModel") { 
        IComponentContainer * cc = new ComponentContainer<AccumModel>(data, data_dims_v, observed);  
        return cc; 

    } else if(modeltype == "LogisticDistanceFixedLambda") { 
        IComponentContainer * cc = new ComponentContainer<LogisticDistanceFixedLambda>(data, data_dims_v, observed);  
        return cc; 

    } else if(modeltype == "LogisticDistance") { 
        IComponentContainer * cc = new ComponentContainer<LogisticDistance>(data, data_dims_v, observed);  
        return cc; 

    } else if(modeltype == "SigmoidDistance") { 
        IComponentContainer * cc = new ComponentContainer<SigmoidDistance>(data, data_dims_v, observed);  
        return cc; 
    } else if(modeltype == "LinearDistance") { 
        IComponentContainer * cc = new ComponentContainer<LinearDistance>(data, data_dims_v, observed);  
        return cc; 

    } else if(modeltype == "NormalDistanceFixedWidth") { 
        IComponentContainer * cc = new ComponentContainer<NormalDistanceFixedWidth>(data, data_dims_v, observed);  
        return cc; 
    } else if(modeltype == "SquareDistanceBump") { 
        IComponentContainer * cc = new ComponentContainer<SquareDistanceBump>(data, data_dims_v, observed);  
        return cc; 

    } else if(modeltype == "ExponentialDistancePoisson") { 
        IComponentContainer * cc = new ComponentContainer<ExponentialDistancePoisson>(data, data_dims_v, observed);  
        return cc; 

    } else if(modeltype == "LogisticDistancePoisson") { 
        IComponentContainer * cc = new ComponentContainer<LogisticDistancePoisson>(data, data_dims_v, observed);  
        return cc; 

    } else if(modeltype == "MixtureModelDistribution") { 
        IComponentContainer * cc = new ComponentContainer<MixtureModelDistribution>(data, data_dims_v, observed);  
        return cc; 

    } else { 
        std::cout << modeltype << std::endl; 
        throw std::runtime_error("unknown model type"); 
    }
    

}

Relation * create_relation(bp::list axesdef, bp::list domainsizes, 
                           IComponentContainer * cm) {

    auto ad = extract_vect<int>(axesdef); 
    auto ds = extract_vect<size_t>(domainsizes); 
    return new Relation(ad, ds, cm); 

}

bp::list get_all_groups_helper(Relation * rel, int d)
{
    bp::list out; 
    for(auto v : rel->get_all_groups(d)) { 
        out.append(v); 
    }
    return out;
}

ParRelation * pr_create_relation(bp::list axesdef, bp::list domainsizes, 
                           IComponentContainer * cm) {

    auto ad = extract_vect<int>(axesdef); 
    auto ds = extract_vect<size_t>(domainsizes); 
    return new ParRelation(ad, ds, cm); 

}

bp::list pr_get_all_groups_helper(ParRelation * rel, int d)
{
    bp::list out; 
    for(auto v : rel->get_all_groups(d)) { 
        out.append(v); 
    }
    return out;
}

void set_seed(rng_t & rng, int seed) { 
    rng.seed(seed); 
}

template<class T>
bp::list post_pred_map_helper(T * rel, domainpos_t dp, bp::list groupids, 
                              entitypos_t entitypos, 
                              boost::threadpool::pool * tp) 
{
    bp::list out; 
    std::vector<groupid_t> gids; 
    for(int i =0; i < bp::len(groupids); ++i) { 
        gids.push_back(bp::extract<groupid_t>(groupids[i])); 
    }

    std::vector<float> scores = rel->post_pred_map(dp, gids, entitypos, tp); 
    for(int i =0 ; i < scores.size(); ++i) { 
        out.append(scores[i]); 
    }
    return out; 

    
}

template bp::list
post_pred_map_helper<Relation> (Relation * rel, domainpos_t dp, 
                                         bp::list groupids, 
                                         entitypos_t entitypos, 
                                         boost::threadpool::pool * tp); 

template bp::list
post_pred_map_helper<ParRelation> (ParRelation * rel, domainpos_t dp, 
                                         bp::list groupids, 
                                         entitypos_t entitypos, 
                                         boost::threadpool::pool * tp); 

//template post_pred_map_helper<ParRelation>; 



BOOST_PYTHON_MODULE(pyirm)
{
  using namespace boost::python;
 
  class_<rng_t>("RNG"); 
  def("set_seed", &set_seed); 


  class_<IComponentContainer, boost::noncopyable>("ComponentContainer", no_init)
      .def("dpcount", &IComponentContainer::dpcount)
      .def("set_hps", &IComponentContainer::set_hps)
      .def("get_hps", &IComponentContainer::get_hps)
      .def("apply_kernel", &IComponentContainer::apply_kernel)
      .def("set_temp", &IComponentContainer::set_temp); 

  def("helloworld", &helloworld); 
  def("cart_prod", &cart_prod_helper_py); 

  def("unique_axes_pos", &unique_axes_pos_helper_py); 
  def("create_component_container", &create_component_container, 
      return_value_policy<manage_new_object>()); 

  class_<Relation, boost::noncopyable>("PyRelation", no_init)
      .def( "__init__", bp::make_constructor( &create_relation))
      .def("create_group", &Relation::create_group)
      .def("delete_group", &Relation::delete_group)
      .def("get_all_groups", &get_all_groups_helper)
      .def("add_entity_to_group", &Relation::add_entity_to_group)
      .def("remove_entity_from_group", &Relation::remove_entity_from_group)
      .def("post_pred", &Relation::post_pred)
      .def("post_pred_map", &post_pred_map_helper<Relation>)
      .def("total_score", &Relation::total_score)
      .def("get_component", &Relation::get_component) 
      .def("set_component", &Relation::set_component)
      .def("get_datapoints_per_group", &Relation::get_datapoints_per_group)
      ; 

  class_<ParRelation, boost::noncopyable>("PyParRelation", no_init)
      .def( "__init__", bp::make_constructor( &pr_create_relation))
      .def("create_group", &ParRelation::create_group)
      .def("delete_group", &ParRelation::delete_group)
      .def("get_all_groups", &pr_get_all_groups_helper)
      .def("add_entity_to_group", &ParRelation::add_entity_to_group)
      .def("remove_entity_from_group", &ParRelation::remove_entity_from_group)
      .def("post_pred", &ParRelation::post_pred)
      .def("post_pred_map", &post_pred_map_helper<ParRelation>)
      .def("score_at_hps", &ParRelation::score_at_hps)
      .def("total_score", &ParRelation::total_score)
      .def("get_component", &ParRelation::get_component) 
      .def("set_component", &ParRelation::set_component)
      .def("get_datapoints_per_group", &ParRelation::get_datapoints_per_group)
      ; 

  class_<boost::threadpool::pool>("ThreadPool", init<size_t>()); 
  
  def("slice_sample", &slice_sampler_wrapper); 
  def("continuous_mh_sample", &continuous_mh_sampler_wrapper); 
  def("uniform_01", &uniform_01); 

  def("normal_sample", &normal_sample); 
  def("log_norm_dist", &log_norm_dist); 
  def("chi2_sample", &chi2_sample); 
  def("log_chi2_dist", &log_chi2_dist); 
  // helper class
  class_<group_dp_map_t>("group_dp_map_t", no_init); 
  
}

