from fileupdate import FileUpdater

fileupdater=FileUpdater()

def updatefile(local_path,update_url,**kwargs):
    """decorator which automatically downlads/updates required files
    see fileupdate.Fileupdater.add_file() for possible arguments
    """
    fileupdater.add_file(local_path,update_url,**kwargs)
    def wrap(f):
        def wrapped_f(*args,**kwargs):
            fileupdater.wait_for_file(local_path)
            return f(*args,**kwargs)
        return wrapped_f
    return wrap

