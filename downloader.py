import requests
import shutil
import os

requests.packages.urllib3.disable_warnings()

class Downloader:
    def __init__(self):
        pass
    
    def downloadFrag(self, remoteUrl, storagePath):
        storageDir = '/'.join(storagePath.split('/')[:-1])
        if not os.path.exists(storageDir):
            os.mkdir(storageDir)
        try:
            # with open(storagePath, 'wb') as f:
            #     resp = requests.get(remoteUrl, verify=False)
            #     f.write(resp)
            with requests.get(remoteUrl, stream=True, verify=False) as r:
                with open(storagePath, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print('Error downloading frag')
            print(str(e))