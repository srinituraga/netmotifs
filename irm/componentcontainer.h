#ifndef __IRM_COMPONENTCONTAINER_H__
#define __IRM_COMPONENTCONTAINER_H__

#include <iostream>
#include <map>
#include <vector>
#include <inttypes.h>
#include <boost/utility.hpp>
#include <boost/python.hpp>
#include <future> 

#include "util.h"

#include "componentslice.h"
#include "componentmh.h"
#include "threadpool.hpp"

namespace bp=boost::python; 


namespace irm { 

// we could use a multimap
typedef std::map<group_coords_t, std::vector<dppos_t> > group_dp_map_t; 

class IComponentContainer {
public:
    virtual size_t dpcount() = 0; 
    virtual float total_score(const group_dp_map_t & gm)  = 0; 

    virtual bp::list total_score_hps_list(const group_dp_map_t & gm, 
                                          bp::list hps, 
                                          boost::threadpool::pool * p) = 0; 

    virtual void create_component(const group_coords_t &  group_coords, 
                                  rng_t & rng) = 0; 
    virtual void delete_component(const group_coords_t &  group_coords) = 0; 

    virtual float post_pred(const group_coords_t &  group_coords, dppos_t dp_pos) = 0;  
    virtual void add_dp(const group_coords_t &  group_coords, dppos_t dp_pos) = 0; 
    virtual float add_dp_post_pred(const group_coords_t &  group_coords, dppos_t dp_pos) = 0; 
    virtual void rem_dp(const group_coords_t &  group_coords, dppos_t dp_pos) = 0; 
    virtual void set_hps(bp::dict & hps) = 0; 
    virtual bp::dict get_hps() = 0; 
    virtual void apply_kernel(std::string name, rng_t & rng, 
                              bp::dict params, 
                              const group_dp_map_t & dppos) = 0; 

    virtual bp::dict get_component(const group_coords_t &  gc) = 0; 
    virtual void set_component(const group_coords_t &  gc, bp::dict val) = 0; 
    virtual void set_temp(float ) = 0; 
    virtual bool is_addrem_mutating() const = 0; 
}; 
   
template<typename CM>
class  ComponentContainer : public IComponentContainer, boost::noncopyable
{ 
    
    struct sswrapper_t { 
        size_t count; 
        typename CM::suffstats_t ss; 
    }; 

    typedef uint64_t group_hash_t; 

public:
    ComponentContainer(const std::string & data, 
                       std::vector<size_t> data_shape, 
                       const std::string & observed ) :
        NDIM_(data_shape.size()), 
        data_shape_(data_shape) ,
        temp_(1.0)
    {
        
        int s = 1; 
        for(int i = 0; i < NDIM_; ++i) { 
            s = s * MAX_GROUPS_PER_DOMAIN; 
        }

        components_.resize(s); 
        // for(int i = 0; i < s; i++) { 
        //     components_[i] = 0; 
        // }

        size_t data_size = 1; 
        for(int i = 0; i < NDIM_; i++) { 
            data_size *= data_shape_[i]; 
        }
        data_.resize(data_size); 
        observed_.resize(data_size); 
        
        memcpy(&(data_[0]), data.c_str(), 
               sizeof(typename CM::value_t)*data_size); 
        memcpy(&(observed_[0]), observed.c_str(), 
               data_size); 
        
    }
    
    ~ComponentContainer() { 
        // for(auto a : components_) { 
        //     delete a.second; 
        // }
        
    }

    bool is_addrem_mutating() const { 
        return CM::is_addrem_mutating; 
    }

    void create_component(const group_coords_t &  group_coords, 
                          rng_t & rng) { 
        group_hash_t gp = hash_coords(group_coords); 

        
        CM::ss_sample_new(&(components_[gp].ss), &hps_, rng); 
        components_[gp].count = 0; 
    }

    void delete_component(const group_coords_t &  group_coords) {
        group_hash_t gp = hash_coords(group_coords); 
        
        // delete components_[gp]; 
        // components_[gp] = 0; 
    }
    

    float total_score_at_hps(const group_dp_map_t & dpmap, 
                             typename CM::hypers_t * hps_t) {
        typename group_dp_map_t::const_iterator i = dpmap.begin(); 


        float score = 0.0; 
        for(; i != dpmap.end(); ++i) { 
            auto gp = hash_coords(i->first); 
            if(components_[gp].count > 0) { 
                score += CM::score(&(components_[gp].ss), hps_t, 
                                   data_.begin(), observed_.begin(), 
                                   i->second); 
            }
        }
        return score/temp_; 
           
    }

    float total_score(const group_dp_map_t & dpmap)  {
        return total_score_at_hps(dpmap, & hps_); 
    }

    bp::list total_score_hps_list(const group_dp_map_t & dpmap, 
                                  bp::list hps, 
                                  boost::threadpool::pool * tp)  { 
        /* 
           For a list of HPs, evaluate the score and return the result
           as a vector

           this takes in a python list and does the conversion 
           internally because of where we cut the static/dynamic typing
           boundary. I'm sorry. 
        */
        bp::list scores; 
        int N = bp::len(hps); 
        std::vector<typename CM::hypers_t> hps_vect(N); 
        for(int i = 0; i < N; ++i) { 
            bp::dict hp_dict = bp::extract<bp::dict>(hps[i]); 
            hps_vect[i] = CM::bp_dict_to_hps(hp_dict); 
        }


        std::vector<float> out(N); 

        
        // We should be more granular here
        for(int i = 0; i < N; ++i) { 
            if(tp) { 
                tp->schedule([&out, i, &dpmap, &hps_vect, this]() {
                        out[i] = this->total_score_at_hps(dpmap, &(hps_vect[i])); 
                    }); 
            } else { 

                out[i] = total_score_at_hps(dpmap, &(hps_vect[i])); 
            }
        }
        if(tp) { 
            tp->wait(); 
        }

        for(int i = 0; i < N; ++i) { 
            scores.append(out[i]); 
        }
            
        return scores; 



    }
    

    float post_pred(const group_coords_t &  group_coords, dppos_t dp_pos) 
    {

        if(observed_[dp_pos] == 0 ) { 
            return 0.0; 
        }

        group_hash_t gp = hash_coords(group_coords); 

        typename CM::value_t val = data_[dp_pos]; 

        return CM::post_pred(&(components_[gp].ss), &hps_, val) / temp_; 

    }

    float add_dp_post_pred(const group_coords_t &  group_coords, dppos_t dp_pos) {

        if(observed_[dp_pos] == 0 ) { 
            return 0.0; 
        }

        group_hash_t gp = hash_coords(group_coords); 
        typename CM::value_t val = data_[dp_pos]; 

        float score = CM::post_pred(&(components_[gp].ss), &hps_, val); 

        CM::ss_add(&(components_[gp].ss), &hps_, val, dp_pos); 
        components_[gp].count++; 
        return score/temp_; 
    }
    
    void add_dp(const group_coords_t &  group_coords, dppos_t dp_pos) {

        if(observed_[dp_pos] == 0 ) { 
            return; 
        }


        group_hash_t gp = hash_coords(group_coords); 
        typename CM::value_t val = data_[dp_pos]; 


        CM::ss_add(&(components_[gp].ss), &hps_, val, dp_pos); 
        components_[gp].count++; 
        
    }


    void rem_dp(const group_coords_t &  group_coords, dppos_t dp_pos) {
        if(observed_[dp_pos] == 0 ) { 
            return; 
        }

        group_hash_t gp = hash_coords(group_coords); 

        typename CM::value_t val = data_[dp_pos]; 

        CM::ss_rem(&(components_[gp].ss), &hps_, val, dp_pos); 
        components_[gp].count--; 
        
    }

    size_t dpcount() { 
        return data_.size(); 
    }

    void set_hps(bp::dict & hps) { 
        hps_ = CM::bp_dict_to_hps(hps); 

    }

    bp::dict get_hps() { 
        return CM::hps_to_bp_dict(hps_); 

    }

    void apply_kernel(std::string name, rng_t & rng, bp::dict config, 
                      const group_dp_map_t & dppos) { 
        if(name == "slice_sample") { 
            float width = bp::extract<float>(config["width"]); 
            for(auto c : dppos) { 
                group_hash_t gh = hash_coords(c.first); 
                slice_sample_exec<CM>(rng, width, 
                                      &(components_[gh].ss), 
                                      &hps_, data_.begin(), observed_.begin(), 
                                      c.second, temp_); 
            }
        } else if(name == "continuous_mh") { 
            int iters = bp::extract<int>(config["iters"]); 
            float min = bp::extract<float>(config["log_scale_min"]); 
            float max = bp::extract<float>(config["log_scale_max"]); 
            for(auto c : dppos) { 
                group_hash_t gh = hash_coords(c.first); 

                continuous_mh_sample_exec<CM>(rng, iters, min, max, 
                                              &(components_[gh].ss), 
                                              &hps_, data_.begin(), 
                                              observed_.begin(), 
                                              c.second, temp_); 
            }
        } else { 
            throw std::runtime_error("unknown kernel name"); 
        }


    }

    bp::dict get_component(const group_coords_t &  gc) { 
        group_hash_t gh = hash_coords(gc); 

        return CM::ss_to_dict(&( components_[gh].ss)); 
    }

    void set_component(const group_coords_t &  gc, bp::dict val) {
        group_hash_t gh = hash_coords(gc); 

        CM::ss_from_dict(&( components_[gh].ss), val); 
        
    }

    void set_temp(float t)  {
        temp_ = t; 
    }

private:
    typedef std::vector<sswrapper_t> components_t; 

    const int NDIM_;
    std::vector<size_t> data_shape_; 

    std::vector< typename CM::value_t> data_; 
    std::vector<char> observed_; 
    components_t components_; 


    group_hash_t hash_coords(const group_coords_t &  group_coords) const { 
        size_t hash = 0; 
        size_t multiplier = 1; 
        for (int i = 0; i < NDIM_; ++i) { 
            // if(group_coords[i] > (MAX_GROUPS_PER_AXIS-1)) { 
            //     throw std::runtime_error("Too many groups"); 
            // }
            hash += multiplier * (group_coords[i]); 
            multiplier = multiplier * (MAX_GROUPS_PER_DOMAIN);
        }
        return hash; 

    }
    float temp_; 
    typename CM::hypers_t hps_; 
    
}; 

}

#endif
