# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django import template
from django.template.defaultfilters import stringfilter
from django.views.decorators.csrf import csrf_exempt

from settings import PROJECT_PATH, DEBUG

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from snh.models.dailymotionmodel import *


import os
import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")

register = template.Library()
@register.filter
@stringfilter
def int_to_string(value):
    return value

@login_required(login_url=u'/login/')
def index(request):
    twitter_harvesters = list(TwitterHarvester.objects.filter(is_active=True))
    twitter_harvesters += list(TwitterHarvester.objects.filter(is_active=False))
    facebook_harvesters = list(FacebookHarvester.objects.filter(is_active=True))
    facebook_harvesters += list(FacebookHarvester.objects.filter(is_active=False))
    dailymotion_harvesters = list(DailyMotionHarvester.objects.filter(is_active=True))
    dailymotion_harvesters += list(DailyMotionHarvester.objects.filter(is_active=False))
    youtube_harvesters = list(YoutubeHarvester.objects.filter(is_active=True))
    youtube_harvesters += list(YoutubeHarvester.objects.filter(is_active=False))

    return  render_to_response(u'snh/index.html',{
                                                    u'home_selected':True,
                                                    u'twitter_harvesters':twitter_harvesters,
                                                    u'facebook_harvesters':facebook_harvesters,
                                                    u'dailymotion_harvesters':dailymotion_harvesters,
                                                    u'youtube_harvesters':youtube_harvesters,
                                                    'user': request.user,
                                                  })

@csrf_exempt
@login_required(login_url=u'/login/')
def get_event_logs(request, **kwargs):
    if 'resetLog' in request.POST:
        if request.POST['resetLog'] == 'Facebook log':
            open(os.path.join(PROJECT_PATH,"log/facebook.log"), 'w').close()

        elif request.POST['resetLog'] == 'Twitter log':
            open(os.path.join(PROJECT_PATH,"log/twitter.log"), 'w').close()

        elif request.POST['resetLog'] == 'Youtube log':
            open(os.path.join(PROJECT_PATH,"log/youtube.log"), 'w').close()

        elif request.POST['resetLog'] == 'Dailymotion log':
            open(os.path.join(PROJECT_PATH,"log/dailymotion.log"), 'w').close()

    logfile = 'Select a logfile to display'
    title = 'Event logs'
    if 'logfile' in kwargs:
        if kwargs['logfile'] == 'facebooklog':
            logfile = open(os.path.join(PROJECT_PATH,"log/facebook.log"), 'r').read()
            title = 'Facebook log'

        elif kwargs['logfile'] == 'twitterlog':
            logfile = open(os.path.join(PROJECT_PATH,"log/twitter.log"), 'r').read()
            title = 'Twitter log'

        elif kwargs['logfile'] == 'youtubelog':
            logfile = open(os.path.join(PROJECT_PATH,"log/youtube.log"), 'r').read() 
            title = 'Youtube log'   

        elif kwargs['logfile'] == 'dailymotionlog':
            logfile = open(os.path.join(PROJECT_PATH,"log/dailymotion.log"), 'r').read()
            title = 'Dailymotion log'

        else:
            logfile = 'Non-existent'
    if logfile == '': logfile = 'Log is empty'

        
    return render_to_response('snh/getLogger.html', {'logfile': logfile,
                                                    'title': title})

@csrf_exempt
@login_required(login_url=u'/login/')
def toggle_harvester(request):
    if request.POST['type'] == 'twitterHarvester':
        harvester = TwitterHarvester.objects.get(pk=request.POST['id'])

    elif request.POST['type'] == 'facebookHarvester':
        harvester = FacebookHarvester.objects.get(pk=request.POST['id'])

    elif request.POST['type'] == 'youtubeHarvester':
        harvester = YoutubeHarvester.objects.get(pk=request.POST['id'])

    elif request.POST['type'] == 'dailyMotionHarvester':
        harvester = DailymotionHarvester.objects.get(pk=request.POST['id'])
    else: 
        return redirect('/')

    if 'enabled' in request.POST:
        harvester.is_active = True
    else:
        harvester.is_active = False

    harvester.save()

    return redirect('/')