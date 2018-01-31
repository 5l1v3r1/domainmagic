# -*- coding: UTF-8 -*-

######################
# new get_tld functions with support for subsubdomains
######################

def tld_tree_path(tldlist, tree, path=None):
    """
    walk list tldlist through tld tree and return a list of all tld candidates found in tree.
    candidate list is a list of tuples
        first tuple item contains the tld part,
        second tuple item a boolean: True if this is a leaf, False if intermediate node
    """
    if path is None:
        path = []
    
    if len(tldlist) == 0:  # list is finished
        return path
    
    if tldlist[0] in tree:
        node = tree[tldlist[0]]
        path.append((tldlist[0], node[0]))
        return tld_tree_path(tldlist[1:], node[1], path)
    
    return path


def tld_tree_update(d, u):
    """add tld tree u into tree d"""
    for k, v in u.items():
        kbranch = d.get(k, (False, {}))
        leaf = v[0] or kbranch[0]
        r = tld_tree_update(kbranch[1], v[1])
        d[k] = (leaf, r)
    return d


def tld_list_to_tree(tldlist):
    """translate a list into a tree path"""
    d = {}
    if len(tldlist) == 0:
        return d
    else:
        is_leaf = len(tldlist)==1
        d[tldlist[0]] = (is_leaf, tld_list_to_tree(tldlist[1:]))
        return d



#######################
# old get_tld functions with subsubdomain detection issues
#######################

import collections

def dict_path(l, node, path=None):
    """walk list l through dict node and return a list of all nodes found up until a leaf node"""
    if path is None:
        path = []
    
    if len(l) == 0:  # list is finished
        return path
    
    if not isinstance(node, collections.Mapping):  # leafnode
        if l[0] == node:
            path.append(node)
        return path
    
    if l[0] in node:
        path.append(l[0])
        return dict_path(l[1:], node[l[0]], path)
    
    return path


def dict_update(d, u):
    """add dict u into d changing leafnodes to dicts where necessary"""
    if not isinstance(d, collections.Mapping):
        d = {d: {}}
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = dict_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def dict_topdown_iterator(d, path=None, skiptop=False):
    """walk through a dict and list all possible paths. Optional path prepends additional path elements
    if skiptop is True, skips the current level and drills down to the next level
    """

    allpaths = []
    if path is None:
        path = []
    currentlevel = sorted(d.keys())
    if not skiptop:
        for node in currentlevel:
            allpaths.append(path[:] + [node, ])

    # drill down
    for node in currentlevel:
        if isinstance(d[node], collections.Mapping):
            for result in dict_topdown_iterator(d[node], path=path + [node, ], skiptop=False):
                allpaths.append(result)

    for path in sorted(allpaths, key=len):
        yield path


def list_to_dict(l):
    """translate a list into a tree path"""
    d = {}
    if len(l) == 0:
        return d
    else:
        d[l[0]] = list_to_dict(l[1:])
        return d
