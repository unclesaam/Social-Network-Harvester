# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django import template
from django.template.defaultfilters import stringfilter

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from snh.models.dailymotionmodel import *

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")

register = template.Library()
@register.filter
@stringfilter
def int_to_string(value):
    return value

@login_required(login_url=u'/login/')
def index(request):
    twitter_harvesters = TwitterHarvester.objects.all()
    facebook_harvesters = FacebookHarvester.objects.all()
    dailymotion_harvesters = DailyMotionHarvester.objects.all()
    youtube_harvesters = YoutubeHarvester.objects.all()

    return  render_to_response(u'snh/index.html',{
                                                    u'home_selected':True,
                                                    u'twitter_harvesters':twitter_harvesters,
                                                    u'facebook_harvesters':facebook_harvesters,
                                                    u'dailymotion_harvesters':dailymotion_harvesters,
                                                    u'youtube_harvesters':youtube_harvesters,
                                                  })

@login_required(login_url=u'/login/')
def get_event_logs(request):
    return render_to_response('snh/getLogger.html')