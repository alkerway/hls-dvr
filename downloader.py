import urllib.request
import os

class Downloader:
    def __init__(self):
        pass
    
    def downloadFrag(self, remoteUrl, storagePath):
        storageDir = '/'.join(storagePath.split('/')[:-1])
        if not os.path.exists(storageDir):
            os.mkdir(storageDir)
        urllib.request.urlretrieve(remoteUrl, storagePath)