# Referenced from https://djangosnippets.org/snippets/678/
# Licensed under same BSD license as Django itself

from django.core.files.uploadhandler import FileUploadHandler, StopUpload
from django.core.exceptions import ValidationError

from django.core.cache import cache
from django.http import HttpResponse, HttpResponseServerError 
from django.views.decorators.csrf import csrf_exempt

class UploadProgressCachedHandler(FileUploadHandler):
    """
    Tracks progress for file uploads.
    The http post request must contain a header or query parameter, 'X-Progress-ID'
    which should contain a unique string to identify the upload to be tracked.
    """

    def __init__(self, request=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        self.progress_id = None
        self.cache_key = None
        self.cancelled = False

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        self.content_length = content_length
        if 'X-Progress-ID' in self.request.GET :
            self.progress_id = self.request.GET['X-Progress-ID']
        #elif 'X-Progress-ID' in self.request.META:
            #self.progress_id = self.request.META['X-Progress-ID']
        elif 'HTTP_X_PROGRESS_ID' in self.request.META:
            self.progress_id = self.request.META['HTTP_X_PROGRESS_ID']
        if self.progress_id:
            #self.cache_key = "%s_%s" % (self.request.META['REMOTE_ADDR'], self.progress_id )
            self.cache_key = "%s_%s" % (self.request.session._session_key, self.progress_id)

            data = cache.get(self.cache_key)
            if data and 'cancelled' in data:
                self.cancelled = True
                cache.delete(self.cache_key)
                raise StopUpload(True)
            else:
                cache.set(self.cache_key, {
                    'length': self.content_length,
                    'uploaded' : 0
                })

    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
        pass

    def receive_data_chunk(self, raw_data, start):
        if self.cache_key:
            data = cache.get(self.cache_key)
            if data and 'cancelled' in data:
                self.cancelled = True
                cache.delete(self.cache_key)
                raise StopUpload(True)
                return QueryDict(), 
            elif data and 'uploaded' in data:
                data['uploaded'] += self.chunk_size
                cache.set(self.cache_key, data)
        return raw_data
    
    def file_complete(self, file_size):
        pass

    def upload_complete(self):
        if self.cache_key:
            cache.delete(self.cache_key)
        if self.cancelled:
            raise StopUpload(True)
        


import json
# report back on upload progress:
@csrf_exempt
def upload_progress(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    progress_id = ''
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    #elif 'X-Progress-ID' in request.META:
        #progress_id = request.META['X-Progress-ID']
    elif 'HTTP_X_PROGRESS_ID' in request.META:
            progress_id = request.META['HTTP_X_PROGRESS_ID']
    if progress_id:
        #cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
        cache_key = "%s_%s" % (request.session._session_key, progress_id)
        data = cache.get(cache_key)
        return HttpResponse(json.dumps(data))
    else:
        return HttpResponseServerError('Server Error: You must provide X-Progress-ID header or query param.')

@csrf_exempt
def cancel_upload(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    progress_id = ''
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    elif 'HTTP_X_PROGRESS_ID' in request.META:
            progress_id = request.META['HTTP_X_PROGRESS_ID']
    if progress_id:
        #cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
        cache_key = "%s_%s" % (request.session._session_key, progress_id)
        cache.set(cache_key, {
            'cancelled': True
        })
    else:
        return HttpResponseServerError('Server Error: You must provide X-Progress-ID header or query param.')
    return HttpResponse({ 'status': 'cancelled' })

