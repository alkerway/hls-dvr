import requests
import shutil
import os

requests.packages.urllib3.disable_warnings()

class Downloader:
    def __init__(self):
        pass
    
    def downloadFrag(self, remoteUrl, storagePath, referer):
        storageDir = '/'.join(storagePath.split('/')[:-1])
        if not os.path.exists(storageDir):
            os.mkdir(storageDir)
        try:
            headers = None
            if referer:
                headers = {'Referer': referer, 'Origin': referer}
            with requests.get(remoteUrl, headers=headers, stream=True, verify=False) as r:
                with open(storagePath, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print('Error downloading frag')
            print(str(e))