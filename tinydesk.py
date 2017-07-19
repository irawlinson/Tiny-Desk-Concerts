#!/usr/local/opt/pyenv/shims python

# title:  tinydesk.py
# author: Isaiah Rawlinson
# date:   07/19/2017
# desc:   Downloads mp3 files of npr's tiny desk concerts

import urllib2
import urllib
import ssl
from xml.etree import ElementTree as etree
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.mp3 import HeaderNotFoundError
import os.path
import subprocess

# Create Folders
if not os.path.exists("concerts"):
    os.makedirs("concerts")

if not os.path.exists("trimmed"):
    os.makedirs("trimmed")

if not os.path.exists("images"):
    os.makedirs("images")

# Context to bypass ssl verification
context = ssl._create_unverified_context()

# Get the rss feed for the tiny desk concert podcast

nprFile = urllib2.urlopen('https://www.npr.org/rss/podcast.php?id=510306')
nprData = nprFile.read()
nprFile.close()

nprRoot = etree.fromstring(nprData)
items = nprRoot.findall('channel/item')
# coverArt = nprRoot.find('channel/itunes:image').get('href')
coverArt = "images/npr.jpg"

if not os.path.isfile(coverArt):
    urllib.urlretrieve("https://media.npr.org/images/podcasts/primary/icon_510306_sq-e07b7d616c85f470d3f723646c10bdfe42b845c2.jpg?s=1400", coverArt)

# Gather the metadata we need for the files
# Title (artist), url

songTitles = []
songUrls = []
songYears = []

for entry in items:
    title = entry.findtext('title')
    url = entry.find('enclosure').get('url')
    year = entry.findtext('pubDate')[8:16]
    songTitles.append(title)
    songUrls.append(url)
    songYears.append(year)

# Retrieve files and populate their metadata

albumArtist = "NPR Tiny Desk"

# data to save in the audio file:
# - title
# - artist
# - albumartist
# - album
# - date
# - tracknum

# Albums will be separated by video year (2016, 2017)

for i in xrange(len(songTitles)):
    songTitles[i] = songTitles[i].replace("/", ", ").rstrip()

def downloadMP3(n):
    try:
        print "Downloading " + songTitles[n] + "..."
        fileName = "concerts/" + songTitles[n].replace("/", ", ") + ".mp3"
        urllib.urlretrieve(songUrls[n], fileName)
        print "Downloaded " + songTitles[n] + "."
    except (HeaderNotFoundError, IOError):
        print "Could not download " + songTitles[n]

def getTrackNum(song):
    firstTrackInAlbum = songYears.index(songYears[song])
    totalTracksInAlbum = songYears.count(songYears[song])
    num = song - firstTrackInAlbum + 1
    return (num, totalTracksInAlbum)

def editMetadata(n):
    try:
        fileName = "concerts/" + songTitles[n] + ".mp3"
        audioFile = MP3(fileName, ID3=EasyID3)
        audioFile['title'] = songTitles[n]
        audioFile['artist'] = songTitles[n]
        audioFile['albumartist'] = albumArtist
        audioFile['album'] = albumArtist + " " + songYears[n]
        trackNum = str(getTrackNum(n)[0])
        totalTracks = str(getTrackNum(n)[1])
        audioFile['tracknumber'] = trackNum
        audioFile.save()
    except HeaderNotFoundError:
        print "Error editing metadata in " + songTitles[n]


def trimMp3(song, introLen):
    inputFile = "concerts/" + songTitles[song] + ".mp3"
    outputFile = "trimmed/" + songTitles[song] + ".mp3"

    if os.path.isfile(inputFile) and not os.path.isfile(outputFile):
        print "Trimming " +  songTitles[song] + "..."
        command = ["ffmpeg", "-ss", introLen, "-i", inputFile, "-acodec", "copy", outputFile]
        return subprocess.call(command)
    else: return

# Trimming Files
# ffmpeg -ss 14 -i concerts/input.mp3 -vcodec copy trimmed/output.mp3
# 14 seconds for songs w/o ad
# First song w/o ad: Teddy Abrams
# 24 seconds for songs w/ ad
# Last song with ad: Youth Lagoon

def trimIntros():
    breakPoint = songTitles.index("Youth Lagoon")
    for i in xrange(breakPoint):
        intro = "14"
        trimMp3(i, intro)
    for i in range(breakPoint, len(songTitles)):
        intro = "25"
        trimMp3(i, intro)

def addArt():
    for i in xrange(len(songTitles)):
        fileName = "trimmed/" + songTitles[i] + ".mp3"
        artArg = coverArt + ":FRONT_COVER"
        if os.path.isfile(fileName):
            print "Adding art to " + songTitles[i]
            command = ["eyeD3", "--add-image", artArg, "images/npr.jpg", fileName]
            subprocess.call(command)

for i in xrange(len(songTitles) - 1):
    # Redownload last attempted files in case of crash
    song = "concerts/" + songTitles[i] + ".mp3"
    nextSong = "concerts/" + songTitles[i + 1] + ".mp3"
    if not (os.path.isfile(song) and os.path.isfile(nextSong)):
        downloadMP3(i)
    if os.path.isfile(song):
        editMetadata(i)

trimIntros()

addArt()

# import pprint.pprint as pprint
# pprint(EasyID3.valid_keys.keys())

print 'Done!'
