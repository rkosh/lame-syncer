# -*- coding: utf-8 -*-
"""
@author: Rajat Kosh
"""

#Authenticate through google drive OAuth 

from urllib import urlencode

import requests
import webbrowser
import json

'''
function : load credentials
input : json file that contains credentials from the Google API console
output : json parsed credentials
'''

class GDrive (object):

	def __init__(self):
		self.NAME = 'Lame_Syncer'
		self.CLIENT_ID = 'XXXXXX.googleapis.com'
		self.CLIENT_SECRET = 'YYYYAAZZ'
		self.ACCESS_TOKEN = 'XXYY'
		self.REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

	def load_credentials(self, json_file):
		creds = None
		try:
			with open(json_file) as data_file:
				creds = json.load(data_file)
			self.CLIENT_SECRET = creds['client_secret']
			self.CLIENT_ID = creds['client_id']
		except Exception as excp:
			creds = {
			'error' : excp
			}
		return creds
		

	'''
	function : get_auth_code
	input : None
	output : Returns auth code for further calls to get API code 
	'''
	def get_auth_code(self):
		req_auth = { 
		            'response_type': 'code', 
		            'client_id': self.CLIENT_ID,
		            'redirect_uri': self.REDIRECT_URI,
		            'scope': (
		            	r"email " +
		              	r"profile " +
					  	r"https://www.googleapis.com/auth/drive " +
		              	r"https://www.googleapis.com/auth/activity")
		            }

		auth_code = ''

		try:
			auth_code = open('auth_code', 'r').read()
		except Exception:
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
	def request_token(self, auth_code):
		req_token = {
					 'grant_type': 'authorization_code',
					 'client_id': self.CLIENT_ID,
					 'client_secret': self.CLIENT_SECRET,
		             'redirect_uri': self.REDIRECT_URI,
		             'code': auth_code
		            }

		access_token = ''
		ref_token = ''

		try:
			ref_token = open('ref_token', 'r').read()
			access_token = self.refresh_access_token(ref_token)
			
		except Exception:
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

	def refresh_access_token(self, ref_token):
		req_ref_token = {
					 'grant_type': 'refresh_token',
					 'client_id': self.CLIENT_ID,
					 'client_secret': self.CLIENT_SECRET,
		             'refresh_token': ref_token
		        }
		data = requests.post('https://accounts.google.com/o/oauth2/token', data=req_ref_token)
		access_token =  data.json()['access_token']

		return access_token

	def get_response(self, data_url):
		resp = requests.get(data_url+'?access_token='+self.ACCESS_TOKEN)
		file_list = resp.json()
		return file_list


	# TODO - Make a single class to share vairables and data between them instead of this mumbo jumbp
	# This is an important one! 
	def open(self):

		creds = self.load_credentials('creds.json')
		if creds.get('error'):
			print (creds['error'])
			return

		auth_code = self.get_auth_code()	# get auth code
		self.ACCESS_TOKEN, self.REFRESH_TOKEN = self.request_token(auth_code)

		#let's list the files first
		file_list = self.get_response('https://www.googleapis.com/drive/v2/files')
		names = {}	# Stores a dict of 'ID' : 'Name'
		
		for item in file_list['items']:
			if not item['labels']['trashed']:
				names[item['id']] = item['title']	#Build a dict for link -> names

		drive_interface = Interface(file_list, names, self)
		drive_interface.start()


class Interface (object):

	def __init__(self, file_list, names, handle):
		self.file_list = file_list
		self.names = names
		self.gdrive = handle

	def list_dirs(self, file_list, folder=None):
		dir_struct = {}
		if not folder:
			folder = "My Drive"
			for item in file_list['items']:
				if item['parents']:
					if item['parents'][0]['isRoot'] and not item['labels']['trashed']:
						filename = self.names[item['id']] 
						ext = item['mimeType']
						if ext == "application/vnd.google-apps.folder":
							filename += '/'
						dir_struct[item['id']] = filename 
		else:
			for item in file_list['items']:
				if not item['labels']['trashed']:
					filename = names[item['id']] 
					ext = item['mimeType']
					if ext == "application/vnd.google-apps.folder":
						filename += '/'
					dir_struct[item['id']] = filename


		print("\n" + "%45s" %folder + "\n"+ "-"*80)

		for index, val in enumerate(dir_struct):
			# TODO - .encode(utf8) is a poor hack
			print ("%25s" %dir_struct[val].encode('utf8')),
			if (index+1) % 3 == 0:
				print ("")

	def start(self):
		self.list_dirs(self.file_list)
		
		cmds = ["cd", "dl", "rm", "up", "mv", "q"]

		while True:
			print("\n\ncommands:")
			print("cd - Change Directory,   dl - Download File, rm - Delete/Remove File")
			print("up - Upload File,   mv - Move/Rename File, q - Quit Terminal Drive")
			usr_inp = raw_input("> ")

			# User input must always contain the  
			cmd = usr_inp.split(" ")
			
			if cmd[0].lower() in cmds:
				if cmd[0] == "cd" :
					self.change_dir(cmd[1])
				elif cmd[0] == "q" :
					break
				else:
					self.list_dirs(self.file_list)
			else:
				print("Sorry Wrong Command! Exiting")
				break

	def change_dir(self, folder):

		if "." in folder:
			if folder == ".":
				# Same folder level
				print("Same folder")
			else:
				# Simple single/double dot notation is used 
				up_level = folder.split("/")
				#Implement the up logic. Make use of up_level.length

		for item in self.file_list['items']:
			if item['mimeType'] == 'application/vnd.google-apps.folder' and self.names[item['id']] == folder:
				data_list = self.gdrive.get_response('https://www.googleapis.com/drive/v2/files/'+item['id'])
				self.list_dirs(data_list, folder)
				break


# Run main if module is run alone
if __name__ == '__main__':
	my_drive = GDrive()
	my_drive.open()