from mypkg.somedep import somedep_function
from otherpkg.dep import otherpkg_function


def target_function(x):
    return somedep_function(x), otherpkg_function(x)
