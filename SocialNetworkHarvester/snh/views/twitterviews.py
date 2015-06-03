# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django import template
from django.template.defaultfilters import stringfilter

import gviz_api
import datetime as dt
from django.http import HttpResponse

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from snh.models.dailymotionmodel import *

from snh.utils import get_datatables_records
from datetime import datetime

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")
import time
import types


#
# TWITTER
#
@login_required(login_url=u'/login/')
def tw(request, harvester_id):
    twitter_harvesters = TwitterHarvester.objects.all()
    if harvester_id == '0': 
        user_list = TWUser.objects.all()
        stags_list = [(obj, len(obj.status_list.all())) for obj in TWSearch.objects.all()]
    else:
        harvester = get_object_or_404(TwitterHarvester, pk=harvester_id)
        user_list = harvester.twusers_to_harvest.all()
        stags_list = [(obj, len(obj.status_list.all())) for obj in harvester.twsearch_to_harvest.all()]
    return  render_to_response(u'snh/twitter.html',{
                                                    u'tw_selected':True,
                                                    u'all_harvesters':twitter_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user_list': user_list,
                                                    u'stags_list': stags_list,
                                                  })

@login_required(login_url=u'/login/')
def tw_user_detail(request, harvester_id, screen_name):
    twitter_harvesters = TwitterHarvester.objects.all()
    user = get_list_or_404(TWUser, screen_name=screen_name)[0]

    status_list = [status.digest_source() for status in user.postedStatuses.all()]
    mention_list = [status.digest_source() for status in user.mentionedInStatuses.all()]
    return  render_to_response(u'snh/twitter_detail.html',{
                                                    u'tw_selected':True,
                                                    u'all_harvesters':twitter_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'user':user,
                                                    u'status_list': status_list,
                                                    u'mention_list': mention_list,
                                                  })
@login_required(login_url=u'/login/')
def tw_search_detail(request, harvester_id, search_id):
    twitter_harvesters = TwitterHarvester.objects.all()
    search = get_list_or_404(TWSearch, pmk_id=search_id)[0]

    status_list = [status.digest_source() for status in search.status_list.all()]

    return  render_to_response(u'snh/twitter_search_detail.html',{
                                                    u'tw_selected':True,
                                                    u'all_harvesters':twitter_harvesters,
                                                    u'harvester_id':harvester_id,
                                                    u'search':search,
                                                    u'status_list':status_list,
                                                  })
@login_required(login_url=u'/login/')
def tw_status_detail(request, harvester_id, status_id):
    twitter_harvesters = TwitterHarvester.objects.all()
    status = get_object_or_404(TWStatus, fid=status_id)
    return render_to_response(u'snh/twitter_status.html', {
                                                            u'tw_selected':True,
                                                            u'all_harvesters':twitter_harvesters,
                                                            u'harvester_id':harvester_id,
                                                            u'twuser': status.user, 
                                                            u'user_url':user.url or '',
                                                            u'status':status, 
                                                            u'mentions':status.user_mentions.all(),
                                                            u'urls':status.text_urls.all(),
                                                            u'tags':status.hash_tags.all(),
                                                           })

#
# TWITTER AJAX
#
@login_required(login_url=u'/login/')
def get_tw_list(request, call_type, harvester_id):
    querySet = None

    if harvester_id == "0":
        querySet = TWUser.objects.all()
    else:
        harvester = TwitterHarvester.objects.get(pmk_id__exact=harvester_id)
        querySet = harvester.twusers_to_harvest.all()

    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'pmk_id',
                            1: u'name',
                            2 : u'screen_name',
                            3 : u'description',
                            4 : u'followers_count',
                            5 : u'friends_count',
                            6 : u'statuses_count',
                            7 : u'listed_count',
                            }
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_twsearch_list(request, call_type, harvester_id):
    querySet = None

    if harvester_id == "0":
        querySet = TWSearch.objects.all()
    else:
        harvester = TwitterHarvester.objects.get(pmk_id__exact=harvester_id)
        querySet = harvester.twsearch_to_harvest.all()

    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'pmk_id',
                            1 : u'term',
                            }
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_tw_status_list(request, call_type, screen_name):
    querySet = None
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'created_at',
                            1 : u'fid',
                            2 : u'text',
                            3 : u'retweet_count',
                            4 : u'retweeted',
                            5 : u'source',
                            }
    try:
        user = get_list_or_404(TWUser, screen_name=screen_name)[0]
        querySet = TWStatus.objects.filter(user=user)#.values(*columnIndexNameMap.values())
    except ObjectDoesNotExist:
        pass

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_tw_statussearch_list(request, call_type, screen_name):
    querySet = None
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'created_at',
                            1 : u'fid',
                            2 : u'user__screen_name',
                            3 : u'text',
                            4 : u'source',
                            }
    try:
        search = TWSearch.objects.get(term__exact="@%s" % screen_name)
        querySet = search.status_list.all()
    except ObjectDoesNotExist:
        pass

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_tw_searchdetail_list(request, call_type, search_id):
    querySet = None
    #columnIndexNameMap is required for correct sorting behavior
    columnIndexNameMap = {
                            0 : u'created_at',
                            1 : u'fid',
                            2 : u'user__screen_name',
                            3 : u'text',
                            4 : u'source',
                            }
    try:
        search = TWSearch.objects.get(pmk_id=search_id)
        querySet = search.status_list.all()
    except ObjectDoesNotExist:
        pass

    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
def get_status_chart(request, harvester_id, screen_name):
    try:
        user = get_list_or_404(TWUser, screen_name=screen_name)[0]
        count = TWStatus.objects.filter(user=user).count()

        fromto = TWStatus.objects.filter(user=user).order_by(u"created_at")
        base = fromto[0].created_at if count != 0 else dt.datetime.now()
        order = 1
        while fromto[0].created_at == None and order < len(fromto):
            base = fromto[order].created_at
            order += 1
        to = fromto[count-1].created_at if count != 0 else dt.datetime.now()

        logger.debug("to: %s"%to)
        logger.debug("base: %s"%base)
        days = (to - base).days + 1
        dateList = [ base + dt.timedelta(days=x) for x in range(0,days) ]
        description = {"date_val": ("date", "Date"),
                       "status_count": ("number", "Status count"),
                      }
        data = []
        for date in dateList:
            c = TWStatus.objects.filter(user=user).filter(created_at__year=date.year,created_at__month=date.month,created_at__day=date.day).count()
            data.append({"date_val":date, "status_count":c})

        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)
        logger.debug(data_table.ToJSon())

        response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
        return response
    except:
        logger.exception('AN ERROR HAS OCCURED WHILE RENDERING A STATUS CHART')

@login_required(login_url=u'/login/')
def get_at_chart(request, harvester_id, screen_name):
    description = {"date_val": ("date", "Date"),
                   "status_count": ("number", "Status count"),
                  }
    data = []
    try:
        search = TWSearch.objects.get(term__exact="@%s" % screen_name)
    except ObjectDoesNotExist:
        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)
        response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
        return response 

    count = search.status_list.all().count()

    fromto = search.status_list.all().order_by(u"created_at")
    base = fromto[0].created_at if count != 0 else dt.datetime.now()
    to = fromto[count-1].created_at if count != 0 else dt.datetime.now()

    days = (to - base).days + 1
    dateList = [ base + dt.timedelta(days=x) for x in range(0,days) ]

    for date in dateList:
        c = search.status_list.all().filter(created_at__year=date.year,created_at__month=date.month,created_at__day=date.day).count()
        data.append({"date_val":date, "status_count":c})

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)

    response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
    return response

