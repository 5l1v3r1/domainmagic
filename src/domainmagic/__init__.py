from fileupdate import FileUpdater

fileupdater=FileUpdater()


CACHEDIR="/tmp"

def updatefile(local_path,update_url,**kwargs):
    fileupdater.add_file(local_path,update_url,**kwargs)
    def wrap(f):
        def wrapped_f(*args,**kwargs):
            fileupdater.wait_for_file(local_path)
            return f(*args,**kwargs)
        return wrapped_f
    return wrap
