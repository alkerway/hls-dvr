import requests
import threading
from parser import ManifestParser
Parser = ManifestParser()

outDir = './manifest'
fragStorageBase = 'frags'
allFrags = []
isFirstParse = True

def handleManifestText(manifestText, remoteManifestUrl):
    global isFirstParse
    global allFrags
    global outDir
    isLevelManifest = Parser.isLevelManifest(manifestText)
    if isLevelManifest:
        levelInfo = Parser.parseLevelManifest(manifestText, remoteManifestUrl, fragStorageBase)
        if isFirstParse:
            isFirstParse = False
            newManifestLines = ['#EXTM3U']
            newManifestLines.append('#EXT-X-VERSION:' + levelInfo['version'])
            newManifestLines.append('#EXT-X-TARGETDURATION:' + levelInfo['targetDuration'])
            lastFrag = levelInfo['frags'][-1]
            newManifestLines.append('#EXT-X-MEDIA-SEQUENCE:' + str(lastFrag['idx']))
            newManifestLines.append('#EXTINF:' + lastFrag['tags']['#EXTINF'])
            newManifestLines.append(lastFrag['storagePath'])
            allFrags.append(lastFrag)
            with open(outDir + '/manifest.m3u8', 'w+') as levelFile:
                levelFile.write('\n'.join(newManifestLines) + '\n')
        else:
            lastStoredFragIdx = allFrags[-1]['idx']
            newFrags = list(filter(lambda f: f['idx'] > lastStoredFragIdx, levelInfo['frags']))
            allFrags += newFrags
            newLines = []
            for fragObj in newFrags:
                newLines.append('#EXTINF:' + fragObj['tags']['#EXTINF'])
                newLines.append(fragObj['storagePath'])
            if len(newLines):
                with open(outDir + '/manifest.m3u8', 'a') as levelFile:
                    levelFile.write('\n'.join(newLines))
                    levelFile.write('\n')
    else:
        pass






def requestUrl():
    remoteManifestUrl = 'http://35.202.188.10:8081/hls/D-3/chunks.m3u8?nimblesessionid=3757'
    manifestRequest = requests.get(remoteManifestUrl)
    handleManifestText(manifestRequest.text, remoteManifestUrl)

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


set_interval(requestUrl, 1.5)

