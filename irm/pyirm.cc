#include <unistd.h>

#include <boost/python.hpp>
#include <boost/python/class.hpp>
#include <boost/utility.hpp>
#include "util.h"
#include "relation.h"
#include "componentcontainer.h"
#include "fastmodel.h"
#include "pyirm_helpers.h"

namespace bp=boost::python; 

//class template irm::ComponentContainer<irm::BetaBernoulli>; 

using namespace irm; 

std::string helloworld() {
    return "Shot through the heart, and you're to blame -- you give love a bad name!" ; 

}

IComponentContainer * create_component_container(std::string data, bp::tuple data_dims, 
                                               std::string modeltype) 
{
    auto data_dims_v = extract_vect<size_t>(data_dims); 
    
    if(modeltype == "BetaBernoulli") { 
        IComponentContainer * cc = new ComponentContainer<BetaBernoulli>(data, data_dims_v); 
        return cc; 
    } else if(modeltype == "AccumModel") { 
        IComponentContainer * cc = new ComponentContainer<AccumModel>(data, data_dims_v); 
        return cc; 

    } else { 
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

BOOST_PYTHON_MODULE(pyirm)
{
  using namespace boost::python;
  
  class_<IComponentContainer, boost::noncopyable>("ComponentContainer", no_init)
      .def("dpcount", &IComponentContainer::dpcount)
      .def("set_hps", &IComponentContainer::set_hps); 

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
      .def("total_score", &Relation::total_score); 

}
