import hashlib
def filehash(fname):
    """Returns hash of the file"""
    fhash = hashlib.sha256()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            fhash.update(chunk)
    return fhash.hexdigest()
