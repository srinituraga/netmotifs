import numpy as np
from irm import kernels

from matplotlib import pylab


temps = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0]


def log_norm_dens(x, mu, var):
    c = -np.log(np.sqrt(var*2*np.pi) )
    v = -(x-mu)**2 / (2*var)
    return c + v 


def dens(x):
    D = 10
    return np.logaddexp(log_norm_dens(x, -D, 1.0),  log_norm_dens(x, D, 1.0))


class Model(object):
    def __init__(self):
        self.temp = 1.0
        self.x = 0.0

    def get_score(self):
        return dens(self.x) / self.temp

    def set_temp(self, temp):
        self.temp = temp

    def latent_set(self, x):
        self.x = x

    def latent_get(self):
        return self.x 

    
def do_inference(model, rng, foo=None):
    x = np.random.normal(model.x, 1.0)

    s_pre = model.get_score()

    init_state = model.latent_get()

    model.latent_set(x)

    s_post = model.get_score()
    d = np.exp(s_post-s_pre)
    if np.random.rand() < d:
        # accept
        pass
    else:
        model.latent_set(init_state)


def temp_trans():
    x = np.linspace(-15, 15, 1000)
    m = Model()

    ITERS = 10000
    samps = []
    for i in range(ITERS):
        kernels.tempered_transitions(m, None, temps, 
                                     Model.latent_get, 
                                     Model.latent_set, 
                                     Model.set_temp, 
                                     do_inference)
        #do_inference(m, None)

        samps.append(m.latent_get())
    pylab.subplot(1, 2, 1)
    pylab.plot(x, np.exp(dens(x)))
    pylab.subplot(1, 2, 2)
    pylab.hist(samps, bins=100)
    pylab.show()

def pt():
    x = np.linspace(-15, 15, 1000)
    m = Model()

    ITERS = 10000
    samps = []
    chain_states = [m.latent_get() for _ in temps]
    for i in range(ITERS):
        chain_states = kernels.parallel_tempering(m, chain_states, 
                                   None, temps, 
                                   Model.latent_get, 
                                   Model.latent_set, 
                                   Model.set_temp, 
                                   do_inference)
        #do_inference(m, None)
        m.latent_set(chain_states[0])
        samps.append(m.latent_get())
    pylab.subplot(1, 2, 1)
    pylab.plot(x, np.exp(dens(x)))
    pylab.subplot(1, 2, 2)
    pylab.hist(samps, bins=100)
    pylab.show()




temp_trans()
