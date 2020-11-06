# from experimentmanager import models

def filter_list(model, **kwargs):
    list_arg = {}
    norm_arg = {}
    for arg in kwargs.keys():
        if isinstance(kwargs[arg], list):
            list_arg[arg] = kwargs[arg]
        else:
            norm_arg[arg] = kwargs[arg]

    model.filter(norm_arg)

    print(list_arg, tuple(norm_arg))


a = [ "edoo"]
b = 3
c = "ciao"

filter_list(None, a=a, b=b, c=c)