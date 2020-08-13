import requests
import sys
from parser import ManifestParser
from downloader import Downloader
from interval import RepeatedTimer
Parser = ManifestParser()
Downloader = Downloader()

outDir = './manifest'
timeLimit = 2
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
            Downloader.downloadFrag(lastFrag['remoteUrl'], outDir + '/' + lastFrag['storagePath'])
        else:
            lastStoredFragIdx = allFrags[-1]['idx']
            newFrags = list(filter(lambda f: f['idx'] > lastStoredFragIdx, levelInfo['frags']))
            allFrags += newFrags
            newLines = []
            fragUrls = []
            for fragObj in newFrags:
                newLines.append('#EXTINF:' + fragObj['tags']['#EXTINF'])
                newLines.append(fragObj['storagePath'])
            if len(newLines):
                with open(outDir + '/manifest.m3u8', 'a') as levelFile:
                    levelFile.write('\n'.join(newLines))
                    levelFile.write('\n')
                for frag in newFrags:
                    Downloader.downloadFrag(frag['remoteUrl'], outDir + '/' + frag['storagePath'])
    else:
        pass

def onStop():
    global outDir
    with open(outDir + '/manifest.m3u8', 'a') as levelFile:
        levelFile.write('#EXT-X-ENDLIST')
        levelFile.write('\n')
    sys.exit()


def requestUrl():
    remoteManifestUrl = 'http://35.202.188.10:8081/hls/D-3/chunks.m3u8?nimblesessionid=3757'
    manifestRequest = requests.get(remoteManifestUrl)
    handleManifestText(manifestRequest.text, remoteManifestUrl)

k = RepeatedTimer(requestUrl, onStop, 2, 300)


