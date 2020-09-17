from dateutil import parser as DateParser
from urllib.parse import urlparse
import os

class ManifestParser:
    def __init__(self):
        pass
    def isLevelManifest(self, manifest):
        if not manifest.startswith('#EXTM3U'):
            raise Exception('Level Text File Not Manifest')
        return '#EXTINF:' in manifest or '#EXT-X-TARGETDURATION:' in manifest
    
    def parseLevelManifest(self, manifest, manifestUrl, fragStorageBase):
        lines = manifest.split('\n')
        infoDict = {}
        infoDict['mostRecentKeyLine'] = ''
        infoDict['endlistTag'] = ''
        frags = []
        currentTags = {}
        currentFragNumber = 0
        for line in lines:
            if line.startswith('#EXT'):
                tagInfo = self.getTagObj(line)
                if not tagInfo:
                    pass
                else:
                    # if '#EXT-X-VERSION' in tagInfo:
                    #     infoDict['version'] = tagInfo['#EXT-X-VERSION']
                    if '#EXT-X-MEDIA-SEQUENCE' in tagInfo:
                        mediaSequence = int(tagInfo['#EXT-X-MEDIA-SEQUENCE'])
                        currentFragNumber = mediaSequence
                        infoDict['mediaSequence'] = mediaSequence
                    elif '#EXT-X-KEY' in tagInfo:
                        infoDict['mostRecentKeyLine'] = line
                    elif '#EXT-X-ENDLIST' in tagInfo:
                        infoDict['endlistTag'] = line

                    # elif '#EXT-X-TARGETDURATION' in tagInfo:
                    #     infoDict['targetDuration'] = tagInfo['#EXT-X-TARGETDURATION']
                    # elif '#EXT-X-PROGRAM-DATE-TIME' in tagInfo:
                    #     pdt = DateParser.parse(tagInfo['#EXT-X-PROGRAM-DATE-TIME'])
                    #     infoDict['pdt'] = round(pdt.timestamp() * 1000)
                    # elif '#EXT-X-DISCONTINUITY-SEQUENCE' in tagInfo:
                    #     infoDict['discontinuitySequence'] = tagInfo['#EXT-X-DISCONTINUITY-SEQUENCE']
                    currentTags.update(tagInfo)
            elif line and not line.startswith('#'):
                fullUrl = line
                storagePath = line
                if line.startswith('/'):
                    parseObj = urlparse(manifestUrl)
                    fullUrl = parseObj.scheme + '://' + parseObj.netloc + line
                    storagePath = line.split('?')[0].split('/')[-1]
                elif line.startswith('http'):
                    storagePath = line.split('?')[0].split('/')[-1]
                else:
                    storagePath = '-'.join(line.split('?')[0].split('/'))
                    urlWithoutEnd = os.path.dirname(manifestUrl)
                    fullUrl = urlWithoutEnd + '/' + line
                frags.append({
                    'storagePath': fragStorageBase + '/' + storagePath,
                    'remoteUrl': fullUrl,
                    'tags': currentTags,
                    'idx': currentFragNumber 
                })
                currentTags = {}
                currentFragNumber += 1
            else:
                # Ignore, not tag or url
                pass
        infoDict['frags'] = frags
        return infoDict

    def getTagObj(self, line):
        tagAndData = line.split(':')
        tag = tagAndData[0]
        store = {}
        if len(tagAndData) > 1:
            data = ':'.join(tagAndData[1:])
            store[tag] = data
            # attributes = data.split(',')
            # if len(list(filter(lambda x: x, attributes))) > 1:
            #     keyDict = {}
            #     for pair in attributes:
            #         nameAndVal = pair.split('=')
            #         name = nameAndVal[0]
            #         val = '='.join(nameAndVal[1:])
            #         if val[0] == '"' and val[-1] == '"':
            #             val = val[1:-1]
            #         keyDict[name] = val
            #     store[tag] = keyDict
            # else:
        else:
            store[tag] = ''
        return store

    def getMasterInfo(self, manifestText, masterUrl):
        masterInfo = {
            'tags': []
        }
        textLines = list(filter(lambda x: x, manifestText.split('\n')))
        if textLines[0] != '#EXTM3U':
            raise Exception('Master Text File Not Manifest')
        for eachLine in textLines:
            if eachLine.startswith('#'):
                masterInfo['tags'].append(eachLine)
            else:
                if eachLine.startswith('http'):
                    masterInfo['levelRemoteUrl'] = eachLine
                elif eachLine.startswith('/'):
                    parseObj = urlparse(masterUrl)
                    masterInfo['levelRemoteUrl'] = parseObj.scheme + '://' + parseObj.netloc + eachLine
                else:
                    masterBase = os.path.dirname(masterUrl)
                    masterInfo['levelRemoteUrl'] = masterBase + '/' + eachLine
                return masterInfo
        raise Exception('Reached end of master file without encountering level url')
                
