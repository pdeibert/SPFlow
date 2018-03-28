'''
Created on March 20, 2018

@author: Alejandro Molina
'''



import numpy as np

from spn.algorithms import Inference
from spn.structure.Base import Leaf

rpy_initialized = False

def init_rpy():
    if rpy_initialized:
        return

    from rpy2 import robjects
    from rpy2.robjects import numpy2ri
    import os
    path = os.path.dirname(__file__)
    with open(path + "/Histogram.R", "r") as rfile:
        code = ''.join(rfile.readlines())
        robjects.r(code)

    numpy2ri.activate()

class Histogram(Leaf):
    def __init__(self, breaks, densities):
        Leaf.__init__(self)
        self.breaks = breaks
        self.densities = densities


def create_histogram_leaf(data, ds_context, scope, alpha=1.0):
    assert len(scope) == 1, "scope of univariate histogram for more than one variable?"
    assert data.shape[1] == 1, "data has more than one feature?"

    idx = scope[0]
    statistical_type = ds_context.statistical_type[idx]
    domain = ds_context.domain[idx]

    if statistical_type == 'continuous':
        maxx = np.max(domain)
        minx = np.min(domain)

        if np.var(data) > 1e-10:
            breaks, densities, mids = getHistogramVals(data)
        else:
            breaks = np.array([minx, maxx])
            densities = np.array([1 / (maxx - minx)])

    elif statistical_type in {'discrete', 'categorical'}:
        breaks = np.array([d for d in domain] + [domain[-1] + 1])
        densities, breaks = np.histogram(data, bins=breaks, density=True)

    else:
        raise Exception('Invalid statistical type: ' + statistical_type)


    # laplacian smoothing
    if alpha:
        n_samples = data.shape[0]
        n_bins = len(breaks) - 1
        counts = densities * n_samples
        densities = (counts + alpha) / (n_samples + n_bins * alpha)

    assert(len(densities) == len(breaks) - 1)

    return Histogram(breaks.tolist(), densities.tolist())


def histogram_likelihood(node, data):

    probs = np.zeros((data.shape[0]), dtype=np.float64)

    for i, x in enumerate(data):
        if x < node.breaks[0] or x > node.breaks[-1]:
            continue

        j = 0
        for b in node.breaks:
            if b > x:
                break
            j += 1

        probs[i] = node.densities[j-1]


    probs[probs < Inference.EPSILON] = Inference.EPSILON

    return np.log(probs)



def histogram_to_str(node, feature_names=None):
    if feature_names is None:
        fname = "V"+str(node.scope[0])
    else:
        fname = feature_names[node.scope[0]]

    breaks = np.array2string(np.array(node.breaks), precision=10, separator=',')
    densities = np.array2string(np.array(node.densities), precision=10, separator=',', formatter={'float_kind':lambda x: "%.10f" % x})

    return "Histogram(%s|%s;%s)" % (fname, breaks, densities)


def histogram_to_cpp(node, leaf_name, vartype):
    inps = np.arange(int(max(node.breaks))).reshape((-1, 1))


    leave_function = """
    {vartype} {leaf_name}_data[{max_buckets}];
    inline {vartype} {leaf_name}(uint8_t v_{scope}){{
        return {leaf_name}_data[v_{scope}];
    }}
    """.format(vartype=vartype, leaf_name=leaf_name, max_buckets=len(inps), scope=node.scope[0])

    leave_init = ""

    ll = np.exp(histogram_likelihood(node, inps))

    for bucket, value in enumerate(ll):
        leave_init += "\t{leaf_name}_data[{bucket}] = {value};\n".format(leaf_name=leaf_name, bucket=bucket, value=value)
    leave_init += "\n"

    return leave_function, leave_init



def getHistogramVals(data):
    from rpy2 import robjects
    init_rpy()

    result = robjects["getHistogram"](data)
    breaks = np.asarray(result[0])
    densities = np.asarray(result[2])
    mids = np.asarray(result[3])

    return breaks, densities, mids



def add_domains(data, ds_context):
    domain = []

    for col in range(data.shape[1]):
        feature_type = ds_context.statistical_type[col]
        if feature_type == 'continuous':
            domain.append([np.min(data[:, col]), np.max(data[:, col])])
        elif feature_type in {'discrete', 'categorical'}:
            domain.append(np.unique(data[:, col]))

    ds_context.domain = np.asanyarray(domain)


def tree_to_spn(tree, features):
    node = Histogram(list(map(float,tree.children[1].children)), list(map(float,tree.children[2].children)))

    feature = str(tree.children[0])

    node.scope.append(features.index(feature))

    return node

Histogram_str_to_spn = {"histogram" : (tree_to_spn, """
%import common.WORD -> WORDHIST
%import common.DIGIT -> DIGITHIST
HISTVARNAMECHAR: "a".."z"|"A".."Z"|DIGITHIST
HISTVARNAME: HISTVARNAMECHAR+
listhist : "[" [DECIMAL ("," DECIMAL)*] "]"
histogram: "Histogram(" HISTVARNAME "|" listhist ";" listhist ")" 
""")}

