import collections

def dict_path(l,node,path=None):
    """walk list l through dict l and return a list of all nodes found up until a leaf node"""
    if path==None:
        path=[]

    if len(l)==0: #list is finished
        return path

    if not isinstance(node,collections.Mapping): #leafnode
        if l[0]==node:
            path.append(node)
        return path

    if l[0] in node:
        path.append(l[0])
        return dict_path(l[1:],node[l[0]],path)

    return path

def dict_update(d, u):
    """add dict u into d changing leafnodes to dicts where necessary"""
    if not isinstance(d,collections.Mapping):
        d={d:{}}
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = dict_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d

def dict_topdown_iterator(d,path=None,skiptop=False):
    """walk through a dict and list all possible paths. Optional path prepends additional path elements
    if skiptop is True, skips the current level and drills down to the next level
    """

    allpaths=[]
    if path==None:
        path=[]
    currentlevel=sorted(d.keys())
    if not skiptop:
        for node in currentlevel:
            allpaths.append(path[:]+[node,])

    #drill down
    for node in currentlevel:
        if isinstance(d[node], collections.Mapping):
            for result in dict_topdown_iterator(d[node],path=path+[node,],skiptop=False):
                allpaths.append(result)

    for path in sorted(allpaths,key=len):
        yield path
        


def list_to_dict(l):
    """translate a list into a tree path"""
    d={}
    if len(l)==0:
        return d
    else:
        d[l[0]]=list_to_dict(l[1:])
        return d

