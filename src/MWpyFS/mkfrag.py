import scipy as sp
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt



def plothist(x):
    plt.hist(x, 1000, facecolor='g', alpha=0.75)
    plt.show()


def frags(alpha, beta, count, sum_lim):
    "Using R to find proper parameters (because I am better with R..)"
    l = np.random.beta(alpha, beta, count)
    expl = []
    for x in l:
        expl.append( 2**(10*x) )
    sm = 0
    for x in expl:
        sm += x
    fragsz = []
    for x in expl:
        fragsz.append( sum_lim*x/sm )
    plothist(fragsz)
        
def fragplan():
    """
    """
    pass

frags(0.87, 0.3, 1000, 100)

#a = stats.lognorm(scale=0.1)
#a = np.random.beta(0.75, 0.25, 10000)
#print a.rvs(2, size=10)
#help(stats.lognorm.rvs)
#help(a.rvs)
#plothist(a)
