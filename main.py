# -*- coding: utf-8 -*-

import applescript
from appscript import *
import time
import sys
import PIL
import os
import discogs_client
import json
import urllib
import sys
from colorthief import ColorThief
import requests
import creds

reload(sys)
sys.setdefaultencoding('utf-8')

# Discogs client
d = discogs_client.Client('ExampleApplication/0.1', user_token=creds.discogs_client)


def giveData():

  # Initialize song data
  last_title, last_artist, last_album = None, None, None
  while True:
    
    iTunesCount = app('System Events').processes[its.name == 'iTunes'].count()
    if iTunesCount > 0:
      iTunes = app('iTunes')
      if iTunes.player_state.get() == k.playing:

        # Grab song data via AppleScript
        scpt = applescript.AppleScript('''
            on trackInfo()
              tell application "iTunes"
                {name, artist, album} of current track
              end tell
            end trackInfo
          ''')
        track = scpt.call('trackInfo')

        title = str(track[0])
        artist = str(track[1])
        album = str(track[2])

        # Detect change in songs
        if title != last_title or artist != last_artist:
          last_title, last_artist = title, artist
          future = time.time() + 2

          broken = False

          while time.time() < future:
            track = scpt.call('trackInfo')
            if str(track[0]) != title or str(track[1]) != artist or str(track[2]) != album:
              try:
                title, artist, album = str(track[0]), str(track[1]), str(track[2])
                broken = True
                break

              except ValueError:
                # Skipping songs too quickly throws this error.
                pass

          if broken == False:
            # If change, show new data
            song_info = "Title: " + title + "\nArtist: " + artist + "\nAlbum: " + album 
            print song_info

            # This is where the files for colour analysis will save
            # Change this to whatever path you want (but change AppleScript below as well)

            IMAGE_PATH = "/Users/NikolaDraca/Desktop/cover.png"

            # Remove saved image everytime
            if os.path.isfile(IMAGE_PATH):
              os.remove(IMAGE_PATH)

            # Save artwork as file
            scpt = applescript.AppleScript('''
              on getImage()
                tell application "iTunes" to tell artwork 1 of current track
                  set srcBytes to raw data
                    set ext to ".png"
                end tell

                set fileName to (((path to desktop) as text) & "cover" & ext)
                set outFile to open for access file fileName with write permission
                set eof outFile to 0
                write srcBytes to outFile
                close access outFile

              end getImage
            ''')

            try:
              scpt.call('getImage')

              if os.path.isfile(IMAGE_PATH):
                # Local album artwork exists

                color_thief = ColorThief(IMAGE_PATH)
                led_colour = color_thief.get_color(quality=6)

            except applescript.ScriptError:

              try:
                # Force error to check for Apple Music
                # AppleScript doesn't have a way to distinguish local files from AM
                track = iTunes.current_track.get()
                artist = track.artist.get()
                led_colour = [255, 255, 255]

              except:
                # Apple Music
                # Search Discogs for matching artist + album
                # Obviously this isn't perfect, but it works relatively well for now! 

                results = d.search(str(album.split('(')[0]).strip() + " " + artist, type='release')

                try:

                  # Save image from Discogs
                  image_url = results[0].images[0]['resource_url']
                  urllib.urlretrieve(image_url, IMAGE_PATH)
                  color_thief = ColorThief(IMAGE_PATH)
                  led_colour = color_thief.get_color(quality=6)

                except IndexError:
                  led_colour = [255, 255, 255]

            print "RGB:" + str(led_colour)

            # Send request to RPi
            # Change to address of your device
            
            r = requests.get('http://192.168.0.34:8080/artwork/' + str(led_colour[0]) + '/' + str(led_colour[1]) + '/' + str(led_colour[2]) )
            print "Status: " + str(r.status_code) + "\n"



            
time.sleep(1)

giveData()


