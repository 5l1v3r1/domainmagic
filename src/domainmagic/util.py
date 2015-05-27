
#TODO: unit tests
def dict_path(self,l,node,path=None):
    """walk list l through dict l and return a list of all nodes found up until a leaf node"""
    if path==None:
        path=[]

    if len(l)==0:
        return path

    if l[0] in node:
        path.append(l[0])
        return dict_path(l[1:],node[l[0]],path)

    return path

def dict_update(self,d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = dict_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d

def list_to_dict(self,l):
    """translate a list into a tree path"""
    d={}
    if len(l)==0:
        return d
    else:
        d[l[0]]=list_to_dict(l[1:])
        return d