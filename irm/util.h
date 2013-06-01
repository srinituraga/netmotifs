#ifndef __IRM_UTIL_H__
#define __IRM_UTIL_H__

#include <list>
#include <set>
#include <vector>
#include <boost/iterator/counting_iterator.hpp>
#include <stdlib.h>

namespace irm { 

static const int MAX_AXES = 4; 

typedef std::vector<int> axesdef_t; 
typedef std::vector<size_t> domainsizes_t; 
typedef int domainpos_t; 
typedef int groupid_t; 
typedef size_t dppos_t;
typedef size_t entitypos_t; 

typedef std::set<groupid_t> group_set_t; 

typedef std::vector<groupid_t> group_coords_t; 
typedef std::vector<entitypos_t> entity_coords_t; 


#define NOT_ASSIGNED -1


template<typename T, typename ForwardIterator> 
void cart_prod_helper(std::vector<std::vector<T> > & output, 
                      std::vector<std::pair<ForwardIterator, ForwardIterator> >  axes, 
                      std::vector<T> current_element, 
                      size_t axispos); 

template<typename T>
std::vector<std::vector<T>> cart_prod(std::vector<size_t> axes)
{
    std::vector<std::vector<T>> output; 
    std::vector<T> x(axes.size()); 
    // create the iterators
    typedef boost::counting_iterator<size_t> i_t; 
    std::vector<std::pair<i_t, i_t>> axes_iters; 

    for(auto a: axes) { 
        axes_iters.push_back(std::make_pair(i_t(0), i_t(a))); 
    }
    cart_prod_helper<T>(output, axes_iters, x, 0); 
    return output; 
}


// FIXME : use output iterator
// FIXME: use boost::range

template<typename T, typename ForwardIterator> 
void cart_prod_helper(std::vector<std::vector<T> > & output, 
                      std::vector<std::pair<ForwardIterator,
                      ForwardIterator>> axes, 
                      std::vector<T> current_element, 
                      size_t axispos) {
    for(auto it = axes[axispos].first; it != axes[axispos].second; ++it) {
        std::vector<T> x = current_element; 
        x[axispos] = *it; 
        
        if(axispos == (axes.size()-1)) { 
            output.push_back(x); 
        } else {
            cart_prod_helper(output, axes, x, axispos + 1); 
        }

    }
    
}



template<typename ForwardIterator> 
std::set<group_coords_t> unique_axes_pos(std::vector<int> axis_pos, size_t val, 
                                         std::vector<std::pair<ForwardIterator, ForwardIterator>> axes)

{
    /* 
       DIMS: maximum dimension of group coords

    */ 
    std::set<group_coords_t> outset; 
    std::vector<group_coords_t> output; 
    group_coords_t o(axes.size()); 

    cart_prod_helper(output, axes, o, 0); 

    for(auto c : output) { 
        bool include = false; 
        for(auto i: axis_pos) { 
            if (c[i] == (int)val) 
                include = true; 
        }
        if(include)
            outset.insert(c); 
    }
    return outset; 
    
}


template<typename T>
std::vector<std::pair<typename T::iterator, typename T::iterator>>
    collection_of_collection_to_iterators(std::vector<T> & collections) 
{
    std::vector<std::pair<typename T::const_iterator, 
                          typename T::const_iterator>>  output; 
    for(auto & a : collections) { 
        output.push_back(std::make_pair(a.begin(), a.end())); 
    }
    
    return output; 
}


}



#endif
