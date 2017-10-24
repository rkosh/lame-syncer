# -*- coding: utf-8 -*-
"""
@author: Rajat Kosh
"""

#Authenticate through google drive OAuth 

from urllib import urlencode

import requests
import webbrowser
import json


# import credential
# import httplib2

# from apiclient import discovery

# credentials = credential.get_credentials()
# http = credentials.authorize(httplib2.Http())
# service = discovery.build('drive', 'v2', http=http)

# results = service.files().list(maxResults=10).execute()

# API_SECRET = 'AIzaSyDHJjCZWWNk8NKmnfUa4XISTJYtS5OriRg'

# r = requests.get('https://www.googleapis.com/drive/v2/files/', 
# 	headers = {
# 		'Authorization':'Bearer {}'.format(API_SECRET) 
# 	})

REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

'''


'''

with open('creds.json') as data_file:
    creds = json.load(data_file)

NAME = creds['name']
CLIENT_ID = creds['client_id']
CLIENT_SECRET = creds['client_secret']

req_auth = { 
            'response_type': 'code', 
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': (
            	r"email " +
              	r"profile " +
			  	r"https://www.googleapis.com/auth/drive " +
              	r"https://www.googleapis.com/auth/activity")
            }

headers = {
      'user-agent': NAME,
      'content-type': 'application/x-www-form-urlencoded',
    }

auth_code = ''

try:
	save_token = open('auth_code', 'r')
	auth_code = save_token.read()
	save_token.close()
except:

	r = webbrowser.open('https://accounts.google.com/o/oauth2/auth?'+urlencode(req_auth))
	auth_code = raw_input("Enter your Auth Code Here : ")

	save_token = open('auth_code', 'w')
	save_token.write(auth_code)
	save_token.close()

req_token = {
			 'grant_type': 'authorization_code',
			 'client_id': CLIENT_ID,
			 'client_secret': CLIENT_SECRET,
             'redirect_uri': REDIRECT_URI,
             'code': auth_code
            }

access_token = ''
ref_token = ''

try:
	handle = open('ref_token', 'r')
	ref_token = handle.read()
	handle.close()
	
	req_ref_token = {
			 'grant_type': 'refresh_token',
			 'client_id': CLIENT_ID,
			 'client_secret': CLIENT_SECRET,
             'refresh_token': ref_token
        }
	data = requests.post('https://accounts.google.com/o/oauth2/token', data=req_ref_token)
	access_token =  data.json()['access_token']
	
except:
	r = requests.post('https://accounts.google.com/o/oauth2/token', data=req_token)
	
	req = r.json()
	handle = open('ref_token', 'w')
	handle.write(req['refresh_token'])
	handle.close()
	
	ref_token = req['refresh_token']
	access_token = req['access_token']
	timer = req['expires_in']


resp = requests.get('https://www.googleapis.com/drive/v2/files?access_token='+access_token)

file_list = resp.json()

for item in file_list['items']:
	print item.get('title')