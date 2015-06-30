from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
import os
import sys
import json
import urllib
import httplib2
import youtube_dl
from youtube_dl.utils import DownloadError



class YoutubeAPIClient():
    '''List of supported caption languages:
    
    'gu','zh-Hans','zh-Hant','ga','gl','la','lo','tr','lv','lt','th','tg',
    'te','fil','ta','yi','ceb','yo','de','da','el','eo','en','eu','et','es',
    'ru','ro','bn','be','bg','ms','jv','bs','ja','ca','cy','cs','pt','pa',
    'vi','pl','hy','hr','ht','hu','hmn','hi','ha','mg','uz','ml','mn','mi',
    'mk','ur','mt','uk','mr','my','af','sw','is','it','iw','kn','ar','km',
    'zu','az','id','ig','nl','no','ne','ny','fr','fa','fi','ka','kk','sr',
    'sq','ko','sv','su','st','sk','si','so','sl'


    '''

    __required_params = ['client_id']
    client_id = ''
    caption_languages = ['en']



    def __init__(self, params):
        for requiredElem in self.__required_params:
            if requiredElem not in params:
                raise MissingRequiredParam(requiredElem, self)
        for givenElem in params:
            if hasattr(self,givenElem) and '__' not in givenElem:
                setattr(self, givenElem, params[givenElem])
            else:
                raise UnrecognizedParameter(givenElem, self)

        self.ytdl = youtube_dl.YoutubeDL(
            params={'writesubtitles': True,
                    'writeautomaticsub': True,
                    'quiet': True,
                    'no_warnings': True,
                    'subtitlesformat': 'srt',
                    'subtitleslangs':self.caption_languages,
                    'listformat': True
                    })

        self.ytClient = build('youtube','v3',developerKey=self.client_id)
        self.gPlusClient = build('plus', 'v1', developerKey=self.client_id)

    def search(self, term, scope='channel,playlist,video',parts="id,snippet"):
        result = self.ytClient.search().list(
            q=term,
            type=scope,
            part=parts,
            maxResults=50
            ).execute()
        return result['items']

    def channel_lookup(self, channelId=None, userName=None, 
        parts='snippet,contentDetails,id,statistics,status'):
        result = self.ytClient.channels().list(
            part=parts,
            id=channelId,
            forUsername=userName
            ).execute(),
        return result

    def video_list_lookup(self, videoIdList, 
        parts='id,snippet,statistics,contentDetails'):
        result = self.ytClient.videos().list(
            part=parts,
            id=videoIdList
            ).execute()
        return result

    def gPlus_person_lookup(self, gPlusId):
        result = self.gPlusClient.people().get(userId=gPlusId).execute()
        return result

    def comment_threads_list(self, videoId, pageToken=None,
        parts='snippet,id,replies'):
        result = self.ytClient.commentThreads().list(
            part=parts,
            videoId=videoId,
            maxResults=50,
            pageToken=pageToken
            ).execute(),
        return result

    def activities_list(self, channelId, pageToken=None,
        parts='id,snippet,contentDetails', 
        publishedBefore=None, publishedAfter=None):
        '''
        publishedBefore, publishedAfter: 'YYYY-MM-DDThh:mm:ss.sZ'
        '''
        result = self.ytClient.activities().list(
            part=parts,
            channelId=channelId,
            maxResults=50,
            pageToken=pageToken,
            publishedBefore=publishedBefore,
            publishedAfter=publishedAfter
            ).execute()
        return result

    def caption_list(self, videoId):
        '''This method tries to retrieve the original human-made captions URL,
        if they exists. Otherwise, the automaticaly generated captions urls are returned.
        Only the selected languages are returned ('en' by default)
        '''

        info = self.extract_video_infos(videoId)

        auto_generated = False
        captions = info['subtitles'] if info['subtitles'] else None

        if captions:
            temp = {}
            for lang in captions:
                for format in captions[lang]:
                    if format['ext'] == 'srt':
                        temp[lang] = format['url']
            captions = temp

        if not captions and info['automatic_captions']:
            captions = {}
            for lang in self.caption_languages:
                for format in info['automatic_captions'][lang]:
                    if format['ext'] == 'srt':
                        captions[lang] = format['url']
            auto_generated = True
        return captions, auto_generated

    def caption_download(self, captionUrl):
        captions = urllib.urlopen(captionUrl)
        return captions.read()

    def video_format_list(self, videoId):
        pass


    def video_download(self, videoId, **kwargs):
        filename=None
        format='worst'

        if 'format' in kwargs and kwargs['format'] in ['best', 'worst', None]:
            format = kwargs['format']

        info = self.extract_video_infos(videoId)
        dlFormat = self.ytdl.select_format(format, info['formats'])
        return dlFormat


    def extract_video_infos(self, videoId):
        try:
            info = self.ytdl.extract_info('https://www.youtube.com/watch?v=%s'%videoId,download=False)
        except DownloadError:
            raise InaccessibleContent()
        return info




#======================= Exception Objects ================================

class MissingRequiredParam(Exception):
    '''An item is missing from the object constructor'''

    def __init__(self, paramName, objType):
        msg = 'The item %s is missing from the constructor of %s'%(paramName, objType)
        super(MissingRequiredParam, self).__init__(msg)
        self.exc_info = sys.exc_info()


class UnrecognizedParameter(Exception):
    '''An unknown parameter was passed to the constructor'''

    def __init__(self, paramName, objType):
        msg = 'The parameter %s is not an attribute of %s'%(paramName, objType)
        super(UnrecognizedParameter,self).__init__(msg)
        self.exc_info = sys.exc_info()

class InaccessibleContent(Exception):
    '''Content is inaccessible from the public'''

    def __init__(self):
        msg = 'The selected content is private and is not visible from the public'
        super(InaccessibleContent,self).__init__(msg)
        self.exc_info = sys.exc_info()













    '''
    List of all methods for <class 'youtube_dl.YoutubeDL.YoutubeDL'>:
        add_default_extra_info('self', 'ie_result', 'ie', 'url')
        add_default_info_extractors('self',)
        add_extra_info('info_dict', 'extra_info')
        add_info_extractor('self', 'ie')
        add_post_processor('self', 'pp')
        add_progress_hook('self', 'ph')
        download('self', 'url_list')
        download_with_info_file('self', 'info_filename')
        encode('self', 's')
        extract_info('self', 'url', 'download', 'ie_key', 'extra_info', 'process')
        filter_requested_info('info_dict',)
        format_resolution('format', 'default')
        get_encoding('self',)
        get_info_extractor('self', 'ie_key')
        in_download_archive('self', 'info_dict')
        list_formats('self', 'info_dict')
        list_subtitles('self', 'video_id', 'subtitles', 'name')
        list_thumbnails('self', 'info_dict')
        post_process('self', 'filename', 'ie_info')
        prepare_filename('self', 'info_dict')
        print_debug_header('self',)
        process_ie_result('self', 'ie_result', 'download', 'extra_info')
        process_info('self', 'info_dict')
        process_subtitles('self', 'video_id', 'normal_subtitles', 'automatic_captions')
        process_video_result('self', 'info_dict', 'download')
        record_download_archive('self', 'info_dict')
        report_error('self', 'message', 'tb')
        report_file_already_downloaded('self', 'file_name')
        report_warning('self', 'message')
        restore_console_title('self',)
        save_console_title('self',)
        select_format('self', 'format_spec', 'available_formats')
        to_console_title('self', 'message')
        to_screen('self', 'message', 'skip_eol')
        to_stderr('self', 'message')
        to_stdout('self', 'message', 'skip_eol', 'check_quiet')
        trouble('self', 'message', 'tb')
        urlopen('self', 'req')
        warn_if_short_id('self', 'argv')
    '''