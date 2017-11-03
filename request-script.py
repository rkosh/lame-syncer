# -*- coding: utf-8 -*-
"""
@author: Rajat Kosh
"""

#Authenticate through google drive OAuth 

from urllib import urlencode

import requests
import webbrowser
import json

REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
NAME = 'Lame_Syncer'
CLIENT_ID = 'XXXXXX.googleapis.com'
CLIENT_SECRET = 'YYYYAAZZ'


'''
function : load credentials
input : json file that contains credentials from the Google API console
output : json parsed credentials
'''

def load_credentials(json_file):
	creds = None
	with open(json_file) as data_file:
		creds = json.load(data_file)
	return creds


creds = load_credentials('creds.json')

NAME = creds['name']
CLIENT_ID = creds['client_id']
CLIENT_SECRET = creds['client_secret']


'''
function : get_auth_code
input : None
output : Returns auth code for further calls to get API code 
'''
def get_auth_code():
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

	auth_code = ''

	try:
		open('auth_code', 'r').read()
	except:
		webbrowser.open('https://accounts.google.com/o/oauth2/auth?'+urlencode(req_auth))
		auth_code = raw_input("Enter your Auth Code Here : ")
		open('auth_code', 'w').write(auth_code)

	return auth_code

'''
function : request_token
input : auth code
output : Returns access token and refresh token in order to use with the core Drive API.
		 Note: access token is time bound and expires after a short duration. Therefore we
		 must create a method to periodically refresh the access token using ref_token 
'''
def request_token(auth_code):
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
		ref_token = open('ref_token', 'r').read()
		access_token = refresh_access_token(ref_token)
		
	except:
		r = requests.post('https://accounts.google.com/o/oauth2/token', data=req_token)
		req = r.json()
		open('ref_token', 'w').write(req['refresh_token'])
		ref_token = req['refresh_token']
		access_token = req['access_token']

	return access_token, ref_token

'''
function : refresh_access_token
input : ref_token
output : Returns a renewed access token. Since access_token expires after a duration therefore
		 this method should be called periodically
'''

def refresh_access_token(ref_token):
	req_ref_token = {
				 'grant_type': 'refresh_token',
				 'client_id': CLIENT_ID,
				 'client_secret': CLIENT_SECRET,
	             'refresh_token': ref_token
	        }
	data = requests.post('https://accounts.google.com/o/oauth2/token', data=req_ref_token)
	access_token =  data.json()['access_token']

	return access_token



def main():

	auth_code = get_auth_code()	#get auth code
	access_token, refresh_token = request_token(auth_code)	#refres_token


	#let's list the files first
	resp = requests.get('https://www.googleapis.com/drive/v2/files?access_token='+access_token)

	file_list = resp.json()

	names = {}	# Stores a dict of 'ID' : 'Name'

	#print(json.dumps(file_list['items'], sort_keys=True, indent=4))

	for item in file_list['items']:
		names[item['id']] = item['title']	#Build a dict for link -> names

	enter_dir(file_list, names)


def enter_dir(file_list, names):
	print_dir(file_list, names, True)
	
	cmds = ["cd", "dl", "rm", "up", "mv", "wc"]

	while True:
		print("\n\ncommands:")
		print("cd - Change Directory,   dl - Download File, rm - Delete/Remove File")
		print("up - Upload File,   mv - Move/Rename File, q - Quit")
		cmd = raw_input("> ")

		if cmd.lower() in cmds:
			print_dir(file_list, names, True)
		else:
			print_dir(file_list, names, True)


def print_dir(file_list, names, is_root=False):

	dir_struct = {}
	folder = "My Drive"
	if is_root:
		for item in file_list['items']:
			if item['parents']:
				if item['parents'][0]['isRoot']:
					filename = names[item['id']] 
					ext = item['mimeType']
					if ext == "application/vnd.google-apps.folder":
						filename += '/'
					dir_struct[item['id']] = filename 


		print("-"*80 +"\n" + "%45r" %folder + "\n"+ "-"*80)

		for index, val in enumerate(dir_struct):
			
			print ("%25r" %dir_struct[val]),
			if (index+1) % 3 == 0:
				print ("\n")

# Run main if module is run alone
if __name__ == '__main__':
	main()
