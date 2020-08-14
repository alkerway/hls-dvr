import requests
import sys
import shutil
import subprocess
from parser import ManifestParser
from downloader import Downloader
from interval import RepeatedTimer
Parser = ManifestParser()
Downloader = Downloader()

outDir = './manifest'
pollInterval = 2
stopAfter = 120
remoteManifestUrl = 'https://ul.cdn946.net:8443/hls/9uu1uxfe.m3u8?s=pXdJnBv6Jz6LbMgu2wbWvA&e=1597378294'

errorCount = 0
lastFragIdx = -1
fragStorageBase = 'frags'
allFrags = []
downloadedFragIndeces = []
isFirstParse = True

def printStatus():
    global allFrags
    global downloadedFragIndeces
    estimatedLength = round(sum(map(lambda f: float(f['tags']['#EXTINF'].split(',')[0]), allFrags)))
    lengthStr = f'{round(estimatedLength)} seconds' if estimatedLength <= 59 else f'{estimatedLength // 60} minutes'
    # print(f'Downloaded {len(downloadedFragIndeces)} ({",".join([str(i) for i in downloadedFragIndeces])}) of {len(allFrags)} frags so far, manifest length={lengthStr}')
    print(f'Downloaded {len(downloadedFragIndeces)} of {len(allFrags)} frags so far, manifest length={lengthStr}')


def handleManifestText(manifestText, remoteManifestUrl):
    global isFirstParse
    global allFrags
    global outDir
    isLevelManifest = Parser.isLevelManifest(manifestText)
    if isLevelManifest:
        levelInfo = Parser.parseLevelManifest(manifestText, remoteManifestUrl, fragStorageBase)
        newManifestLines = []
        newFrags = []
        if isFirstParse:
            isFirstParse = False
            lastFrag = levelInfo['frags'][-1]

            newManifestLines.append('#EXTM3U')
            newManifestLines.append('#EXT-X-VERSION:' + levelInfo['version'])
            newManifestLines.append('#EXT-X-TARGETDURATION:' + levelInfo['targetDuration'])
            newManifestLines.append('#EXT-X-MEDIA-SEQUENCE:' + str(lastFrag['idx']))
            open(outDir + '/manifest.m3u8', 'w').close()
            newFrags.append(lastFrag)

        else:
            lastStoredFragIdx = allFrags[-1]['idx']
            newFrags = list(filter(lambda f: f['idx'] > lastStoredFragIdx, levelInfo['frags']))
        
        allFrags += newFrags
        printStatus()
        fragUrls = []
        for fragObj in newFrags:
            for key, value in fragObj['tags'].items():
                newManifestLines.append(f'{key}: {value}')
            newManifestLines.append(fragObj['storagePath'])
        if len(newManifestLines):
            with open(outDir + '/manifest.m3u8', 'a') as levelFile:
                levelFile.write('\n'.join(newManifestLines))
                levelFile.write('\n')
            for frag in newFrags:
                Downloader.downloadFrag(frag['remoteUrl'], outDir + '/' + frag['storagePath'])
                downloadedFragIndeces.append(frag['idx'])
                printStatus()
                if lastFragIdx == frag['idx']:
                    print('Downloaded Last Frag Finish!!')
                    formatDownloadedVideo()
            
    else:
        pass

def formatDownloadedVideo():
    print('\n\n')
    print('=============Starting Fomat================')
    subprocess.call(['ffmpeg','-y','-i', outDir + '/manifest.m3u8', outDir + '/video.mp4'])


def onStop():
    global outDir
    global allFrags
    global lastFragIdx
    
    fragIndeces = list(map(lambda f: f['idx'], allFrags))
    lastFragIdx = max(fragIndeces)
    print(f'Set last frag idx to {lastFragIdx}')
    
    with open(outDir + '/manifest.m3u8', 'a') as levelFile:
        levelFile.write('#EXT-X-ENDLIST')
        levelFile.write('\n')

    if lastFragIdx in downloadedFragIndeces:
        print('Already downloaded last frag on finish')
        formatDownloadedVideo()

    sys.exit()


def requestUrl():
    global allFrags
    global errorCount
    global remoteManifestUrl
    try:
        manifestRequest = requests.get(remoteManifestUrl, verify=False)
        manifestRequest.raise_for_status()
        handleManifestText(manifestRequest.text, remoteManifestUrl)
    except requests.exceptions.HTTPError as err:
        print('Error retrieving manifest')
        print(err)
        errorCount += 1
        if errorCount > 20:
            cancelTimer()
            if len(allFrags):
                onStop()
            raise SystemExit(err)
    except Exception as e:  # This is the correct syntax
        errorCount += 1
        if errorCount > 20:
            print('ERROR:' + str(e))
            if len(allFrags):
                onStop()
            cancelTimer()
            raise SystemExit(e)
        else:
            print(e)

def cancelTimer():
    k.stop()


k = RepeatedTimer(requestUrl, onStop, pollInterval, stopAfter)


