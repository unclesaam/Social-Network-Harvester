# coding=UTF-8

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404, redirect, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django import template
from django.template.defaultfilters import stringfilter
from django.core.servers.basehttp import FileWrapper
from django.db.models import Q

import gviz_api
import datetime as dt
from django.http import HttpResponse

from snh.models.twittermodel import *
from snh.models.facebookmodel import *
from snh.models.youtubemodel import *
from snh.models.dailymotionmodel import *

from snh.utils import get_datatables_records, Twitter_raw_json_posts_data,generate_csv_response
from datetime import datetime

import snhlogger
logger = snhlogger.init_logger(__name__, "view.log")
import time
import types
import re

from settings import DEBUGCONTROL, dLogger
debugging = DEBUGCONTROL['twitterview']
if debugging: print "DEBBUGING ENABLED IN %s"%__name__


#
# TWITTER
#
tw_status_fields = [['fid','text'],
    ['created_at','favorited'],
    ['retweet_count','retweeted'],
    ['truncated','text_urls'],
    ['hash_tags','user_mentions'],
    ['source','user__screen_name'],
    ['user__fid','user__name'],
    ['user__description','user__url'],
    ['user__location','user__time_zone'],
    ['user__utc_offset','user__protected'],
    ['user__favourites_count','user__followers_count'],
    ['user__friends_count','user__statuses_count'],
    ['user__listed_count','user__created_at'],
    ['user__lang','user__profile_text_color'],
    ['user__profile_background_color','user__profile_background_tile'],
    ['user__profile_background_image_url','user__profile_image_url'],
    ['user__profile_link_color','user__profile_sidebar_fill_color']]


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
                                                    'status_fields':tw_status_fields
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
                                                    'status_fields': tw_status_fields
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
                                                    'status_fields': tw_status_fields,
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
                            8 : u'location',
                            }
    #call to generic function from utils
    return get_datatables_records(request, querySet, columnIndexNameMap, call_type)

@login_required(login_url=u'/login/')
@dLogger.debug
def get_twsearch_list(request, call_type, harvester_id):
    if debugging:
        dLogger.log('get_twsearch_list()')

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
                            2 : u'len#status_list'
                            }
    #call to generic function from utils
    db_record = get_datatables_records(request, querySet, columnIndexNameMap, call_type)
    #dLogger.log('    db_record: %s'%db_record)
    return db_record

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
def get_tw_harvester_status_list(request, call_type, harvester_id):
    querySet = None
    columnIndexNameMap = {
                            0 : u'created_at',
                            1 : u'fid',
                            2 : u'text',
                            3 : u'retweet_count',
                            4 : u'retweeted',
                            5 : u'source',
                            }
    if harvester_id == '0':
        querySet = TWStatus.objects.all()
    else:
        harvester = get_list_or_404(TwitterHarvester, pmk_id=harvester_id)[0]
        #querySet = [user.postedStatuses.all() for user in harvester.twusers_to_harvest.all()]

        # merge two conditional filter in queryset:
        conditionList = [Q(user=user) for user in harvester.twusers_to_harvest.all()]
        conditionList += [Q(TWSearch_hit=search) for search in harvester.twsearch_to_harvest.all()]
        querySet = TWStatus.objects.filter(reduce(lambda x, y: x | y, conditionList)).distinct()

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
        logger.exception('AN ERROR HAS OCCURED WHILE RENDERING A STATUS CHART. SCREEN_NAME: %s'%screen_name)

@login_required(login_url=u'/login/')
def get_search_status_chart(request, harvester_id, search_term):
    try:
        search = get_list_or_404(TWSearch, term=search_term)[0]
        count = search.status_list.count()

        fromto = search.status_list.order_by(u"created_at")
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
            c = search.status_list.filter(created_at__year=date.year,created_at__month=date.month,created_at__day=date.day).count()
            data.append({"date_val":date, "status_count":c})

        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)
        logger.debug(data_table.ToJSon())
        response =  HttpResponse(data_table.ToJSon(), mimetype='application/javascript')
        return response
    except:
        dLogger.exception("AN ERROR HAS OCCURED WHILE RENDERING STATUS CHART: SEARCH_TERM: %s"%search_term)



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

@login_required
def get_tw_status_json(request):
    if debugging: dLogger.log('get_tw_status_json()')

    if 'search_id' in request.GET:
        search_id = request.GET['search_id']
        dLogger.log('search_id: %s'%search_id)
        try:
            search = TWSearch.objects.get(pk=search_id)
            querySet = search.status_list.all()
            queryName = search.term.encode('ascii', 'replace')
        except:
            raise
            return HttpResponse('<strong>Wrong request</strong>')

    elif 'user_id' in request.GET:
        user_id = request.GET['user_id']
        dLogger.log('user_id: %s'%user_id)
        try:
            user = TWUser.objects.get(pk=user_id)
            querySet = user.postedStatuses.all()
            queryName = user.screen_name.encode('ascii', 'replace')
        except:
            raise
            return HttpResponse('<strong>Wrong request</strong>')

    else:
        return HttpResponse('<strong>Wrong request</strong>')
    #dLogger.log(querySet)
    return Twitter_raw_json_posts_data(queryName, querySet)

@dLogger.debug
@login_required(login_url=u'/login/')
def dwld_tw_status_csv(request):
    if debugging: dLogger.log('dwld_tw_status_csv')

    columns = request.GET.getlist('fields')
    sColumns = ''
    for column in columns:
        sColumns += str(column)+','

    start, end = 0,None
    if 'range' in request.GET:
        rng = request.GET['range']
        start, end = re.split('-', rng)

    aadata = []
    search_id,harvester_id,TWUser_id = None,None,None
    if 'search_id' in request.GET:
        search_id = request.GET['search_id']
        search = get_object_or_404(TWSearch, pk=search_id)
        statuses = search.status_list.all()[start:end]
        filename = '%s_TWStatuses'%re.sub(' ', '_',unicode(search))

    elif 'harvester_id' in request.GET:
        harvester_id = request.GET['harvester_id']
        if harvester_id == '0':   #tous les harvesters.
            statuses = TWStatus.objects.all()[start:end]
            filename = 'all_TWStatuses'
        else:
            harvester = get_object_or_404(TwitterHarvester, pmk_id=harvester_id)
            # merge two conditional filter in queryset:
            conditionList = [Q(user=user) for user in harvester.twusers_to_harvest.all()]
            conditionList += [Q(TWSearch_hit=search) for search in harvester.twsearch_to_harvest.all()]
            statuses = TWStatus.objects.filter(reduce(lambda x, y: x | y, conditionList)).distinct()[start:end]
            filename = '%s_TWStatuses'%re.sub(' ', '_',unicode(harvester))

    elif 'TWUser_id' in request.GET:
        TWUser_id = request.GET['TWUser_id']
        user = get_object_or_404(TWUser, pmk_id=TWUser_id)
        statuses = user.postedStatuses.all()[start:end]
        filename = '%s_TWStatuses'%re.sub(' ', '_',unicode(user))

    if end:
        filename += '_%s-%s'%(start,int(end)-1)   

    count = statuses.count()
    step_size = 10000
    if count > step_size:
        files = []
        for i in range(0, count, step_size):
            url = '/dwld_tw_status_csv?range=%s-%s'%(i,i+step_size)
            if search_id:
                url += '&search_id=%s'%search_id
            elif harvester_id:
                url += '&harvester_id=%s'%harvester_id
            elif TWUser_id:
                url += '&TWUser_id=%s'%TWUser_id
            for field in columns:
                url += '&fields=%s'%field
            files.append( ('%s_%s-%s.csv'%(filename,i,i+step_size-1), url))
        context = {'files': files}
        return render_to_response('snh/multiple_files_download.html', context)

    for status in statuses:
        #dLogger.log('    status: %s'%status)
        adata = []
        user = status.user
        for column in columns:
            if 'user__' in column:
                value = getattr(user, re.sub('user__', '', column))
            elif column in ['text_urls', 'hash_tags', 'user_mentions']:
                manager = getattr(status, column)
                value = manager.all()
            else:
                value = getattr(status, column)
            #dLogger.log('    %s: %s'%(column, value))
            adata.append(unicode(value))
        aadata.append(adata)

    data = {'sColumns': sColumns, 'aaData': aadata}
    return generate_csv_response(data, filename=filename+'.csv')
