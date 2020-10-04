import requests
import sys
import shutil
import subprocess
from parser import ManifestParser
from downloader import Downloader
from interval import RepeatedTimer
Parser = ManifestParser()
Downloader = Downloader()

sys.stdout = open('./log/python-output.txt', 'w+')

outDir = './manifest'
POLL_INTERVAL = 2
MAX_ERROR_COUNT = 20
MAX_STALL_COUNT = 50

stopAfter = 60 * 60
remoteManifestUrl = 'https://sgp-haproxy.angelthump.com/hls/chihayalove72/index.m3u8?stream=chihayalove72'
outputFormat = 'mp4'

errorCount = 0
stallCount = 0
lastFragIdx = -1
fragStorageBase = 'frags'
masterUrl = ''
allFrags = []
downloadedFragIndeces = []
isFirstParse = True

def printStatus():
    global allFrags
    global downloadedFragIndeces
    estimatedLength = round(sum(map(lambda f: float(f['tags']['#EXTINF'].split(',')[0]), allFrags)))
    lengthStr = f'{round(estimatedLength)} seconds' if estimatedLength <= 59 else f'{estimatedLength // 60} minutes'
    # print(f'Downloaded {len(downloadedFragIndeces)} ({",".join([str(i) for i in downloadedFragIndeces])}) of {len(allFrags)} frags so far, manifest length={lengthStr}')
    print(f'Downloaded {len(downloadedFragIndeces)} of {len(allFrags)} frags so far, manifest length={lengthStr}', end='\r')


def handleLevelManifestText(manifestText, remoteLevelUrl):
    global isFirstParse
    global allFrags
    global outDir
    global errorCount
    global stallCount

    levelInfo = Parser.parseLevelManifest(manifestText, remoteLevelUrl, fragStorageBase)
    newManifestLines = []
    newFrags = []
    if isFirstParse:
        isFirstParse = False
        lastFrag = levelInfo['frags'][-1]
        firstFrag = levelInfo['frags'][0]
        for key, value in firstFrag['tags'].items():
            if key == '#EXT-X-MEDIA-SEQUENCE':
                newManifestLines.append('#EXT-X-MEDIA-SEQUENCE:' + str(lastFrag['idx']))
            elif key == '#EXT-X-KEY' and '#EXT-X-KEY' not in lastFrag['tags']:
                newManifestLines.append(levelInfo['mostRecentKeyLine'])
            elif key != '#EXTINF':
                newManifestLines.append(f'{key}:{value}' if value else key)

        open(outDir + '/level.m3u8', 'w').close()
        newFrags.append(lastFrag)

    else:
        lastStoredFragIdx = allFrags[-1]['idx']
        newFrags = list(filter(lambda f: f['idx'] > lastStoredFragIdx, levelInfo['frags']))
        if len(newFrags) == 0:
            stallCount += 1
            if stallCount > MAX_STALL_COUNT:
                print()
                print('Stall count more than max stall count, exiting')
                cancelTimer()
                if len(allFrags):
                    onStop()
                raise SystemExit(err)
    
    allFrags += newFrags
    printStatus()
    fragUrls = []
    for fragObj in newFrags:
        for key, value in fragObj['tags'].items():
            if (key == '#EXTM3U' or key == '#EXT-X-VERSION') and not isFirstParse:
                print('CAUTION extinf tag on non first parse\n')
            else:
                newManifestLines.append(f'{key}:{value}' if value else key)
        newManifestLines.append(fragObj['storagePath'])
    if len(newManifestLines):
        with open(outDir + '/level.m3u8', 'a') as levelFile:
            levelFile.write('\n'.join(newManifestLines))
            levelFile.write('\n')
        for frag in newFrags:
            Downloader.downloadFrag(frag['remoteUrl'], outDir + '/' + frag['storagePath'])
            downloadedFragIndeces.append(frag['idx'])
            printStatus()
            if lastFragIdx == frag['idx']:
                print('Downloaded Last Frag Finish!!')
                formatDownloadedVideo()
        errorCount = 0
    
    if levelInfo['endlistTag']:
        print('Endlist Encountered, exiting')
        onStop()

def writeMasterToFile(masterInfo):
    text = '\n'.join(masterInfo['tags'])
    with open(outDir + '/master.m3u8', 'w+') as masterFile:
        masterFile.write(text + '\n')
        masterFile.write('level.m3u8')

def formatDownloadedVideo():
    global outputFormat
    global masterUrl
    print('\n\n')
    print('=============Starting Fomat================')
    inputPath = outDir + '/master.m3u8' if masterUrl else outDir + '/level.m3u8'
    ffmpegCommand = ['ffmpeg',
    '-v',
    'verbose',
    '-allowed_extensions',
    'ALL',
    '-protocol_whitelist', 'file,http,https,tcp,tls',
    '-y',
    '-fflags',
    '+genpts+igndts',
    # '-r','30',
    '-i',
    inputPath,
    # '-r','30',
    '-c', 'copy',
    outDir + '/video.' + outputFormat
    ]
    subprocess.call(ffmpegCommand)
    print(' '.join(ffmpegCommand))
    # shutil.rmtree(outDir + '/frags')


def onStop():
    global outDir
    global allFrags
    global lastFragIdx
    
    fragIndeces = list(map(lambda f: f['idx'], allFrags))
    lastFragIdx = max(fragIndeces)
    print(f'Set last frag idx to {lastFragIdx}')
    
    with open(outDir + '/level.m3u8', 'a') as levelFile:
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
    global masterUrl
    try:
        manifestRequest = requests.get(remoteManifestUrl, verify=False)
        manifestRequest.raise_for_status()
        manifestText = manifestRequest.text
        if Parser.isLevelManifest(manifestText):
            handleLevelManifestText(manifestRequest.text, remoteManifestUrl)
        else:
            masterUrl = remoteManifestUrl
            masterInfo = Parser.getMasterInfo(manifestText, masterUrl)
            levelUrl = masterInfo['levelRemoteUrl']
            remoteManifestUrl = levelUrl
            
            writeMasterToFile(masterInfo)
            levelRequest = requests.get(levelUrl, verify=False)
            levelRequest.raise_for_status()
            if Parser.isLevelManifest(manifestText):
                handleLevelManifestText(levelRequest.text, levelUrl)

    except requests.exceptions.HTTPError as err:
        print('Error retrieving manifest')
        print(err)
        errorCount += 1
        if errorCount > MAX_ERROR_COUNT:
            cancelTimer()
            if len(allFrags):
                onStop()
            raise SystemExit(err)
    except Exception as e:
        errorCount += 1
        if errorCount > MAX_ERROR_COUNT:
            print('ERROR:' + str(e))
            if len(allFrags):
                onStop()
            cancelTimer()
            raise SystemExit(e)
        else:
            print(e)

def cancelTimer():
    k.stop()


k = RepeatedTimer(requestUrl, onStop, POLL_INTERVAL, stopAfter)


