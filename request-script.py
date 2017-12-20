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
		if '?' in data_url:
			data_url = data_url+'&access_token='+self.ACCESS_TOKEN
		else:
			data_url = data_url+'?access_token='+self.ACCESS_TOKEN
		resp = requests.get(data_url)
		file_list = resp.json()

		nextToken = file_list.get('nextPageToken')
		new_list = file_list
		# Get the complete file list
		if nextToken:
			print("Retriveing the list wait..."),
			while True:
				new_resp = requests.get(new_list['nextLink']+'&access_token='+self.ACCESS_TOKEN)
				new_list = new_resp.json()
				for item in new_list['items']:
					file_list['items'].append(item)
				print("\b..."),
				if not new_list.get('nextPageToken'):
					break
		return file_list


	# TODO - Make a single class to share vairables and data between them instead of this mumbo jumbo
	# This is an important one!
	def _init(self):

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


avail_cmds = {} # All the available commands go inside this dict along with their handles
# Decorator for user input
def user_input(input_fn):
	if not input_fn.__name__ in avail_cmds:
		avail_cmds[input_fn.__name__] = input_fn

	def wrapper(*args, **kwargs):
		input_fn(*args, **kwargs)
		return wrapper



class Interface (object):

	def __init__(self, file_list, names, handle):
		self.file_list = file_list
		self.names = names
		self.gdrive = handle
		self.current_folder = None
		self.visited = []	# Keep Tracks of Visited folders (Helpful for cd ..)

	def list_dirs(self, file_list, folder=None):
		dir_struct = {}
		# TODO: Merge Repetition
		for item in file_list['items']:
			if not folder:
				if item['parents'] and item['parents'][0]['isRoot'] and not item['labels']['trashed']:
					filename = self.names[item['id']] 
					ext = item['mimeType']
					if ext == "application/vnd.google-apps.folder":
						filename += '/'
					dir_struct[item['id']] = filename 
			else:
				if not item['labels']['trashed']:
					filename = self.names[item['id']] 
					ext = item['mimeType']
					if ext == "application/vnd.google-apps.folder":
						filename += '/'
					dir_struct[item['id']] = filename
		
		if not folder:
			folder = 'My Drive'
			self.current_folder = []
		else:
			self.current_folder = folder

		print("\n" + "%45s" %folder + "\n"+ "-"*80)

		for index, val in enumerate(dir_struct):
			# TODO: remove encode(utf8) as this is a poor hack
			print ("%25s" %dir_struct[val].encode('utf8')),
			if (index+1) % 3 == 0:
				print ("")

	def start(self):
		self.list_dirs(self.file_list)

		while True:
			print("\n\nAvailable Commands:")
			print("cd - Change Directory,   dl - Download File,      rm - Delete/Remove File")
			print("up - Upload File,        mv - Move/Rename File,   wc - Watch File \n(Press 'q' to quit)")
			usr_inp = raw_input("> ")

			# User input must always contain the space after command 
			cmd = usr_inp.split(" ", 1)

			if cmd[0] in avail_cmds:
				avail_cmds[cmd[0]](cmd[1])
			else:
				if cmd[0] == 'q':
					break
				print("Sorry Wrong Command! Try Again")

	@user_input
	def cd(self, folder):

		if not folder:	# List all directories
			self.list_dirs(self.file_list)
			return
		elif "." in folder:	# Check if user inputted dot notation
			if not folder == ".":
				if self.visited:
					# Simple single/double dot notation is used 
					# up_level = folder.split("/")
					#Implement the up logic. Make use of up_level.length
					self.current_folder = None
					prev_dir = self.visited.pop()
					self.cd(prev_dir)	# Single level
				else:
					self.cd(None) # Go to Root
					self.visited = []
			return
		item_id = ''
		data_list = {'items': []}

		for item in self.file_list['items']:
			if item['mimeType'] == 'application/vnd.google-apps.folder' and self.names.get(item['id']) == folder:
				item_id = item['id']
				break
		if item_id:
			for item in self.file_list['items']:
				if item['parents'][0]['id'] == item_id:
					data_list['items'].append(item)
			if self.current_folder:
				self.visited.append(self.current_folder)
			self.list_dirs(data_list, folder)
		else:
			print("No such directory :( Please try again")

	@user_input
	def dl(self, filename):
		for item in self.file_list['items']:
			if item['mimeType'] != 'application/vnd.google-apps.folder' and self.names.get(item['id']) == filename:
				# TODO: Seperate thread spawning for the Downloads
				if(item['downloadUrl']):
					if Utility.download_file(downloadUrl, filename):
						print("File saved successfully as %s " %filename)
				else:
					print("Unable to retrieve download url :(")
				break


class Utility(object):

	@classmethod
	def download_file(cls, url, filename):
	    r = requests.get(url, stream=True)
	    # TODO: Exception Handling
	    with open(filename, 'wb') as f:
	    	for chunk in r.iter_content(chunk_size=1024):
	    		print("#"),
	    		f.write(chunk)
		return True


# Run main if module is run alone
if __name__ == '__main__':
	my_drive = GDrive()
	my_drive._init()