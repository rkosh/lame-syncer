import os
import mimetypes
import httplib, urllib


from os.path import basename

def sync_files ():
  	pass

def upload_file(filename):
  	
  	mime, encoding = mimetypes.guess_type(filename)
  	title = basename(filename)
  	size = os.path.getsize(filename)
  	url = 'https://www.googleapis.com/drive/v2/files?uploadType=resumable'

	"""
	media = MediaFileUpload(filename,
                        mimetype=mime, 
                        resumable=True)

	file = drive_service.files().insert(body={'title': title},
           		                         media_body=media,
                	                    fields='id').execute()
	print 'File ID: %s' % file.get('id')
	"""

	headers = {
		"X-Upload-Content-Type": mime,
		"X-Upload-Content-Length": size,
		"Content-type": "application/x-www-form-urlencoded",
		"Accept": "text/plain"
	}



  	


if __name__ == '__main__':
    upload_file('D:\Beta-Stuff\Insync\experiments\lame-syncer\sync-data\ABC.txt')