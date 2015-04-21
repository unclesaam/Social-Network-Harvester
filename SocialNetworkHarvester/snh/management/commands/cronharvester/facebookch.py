# coding=UTF-8

import sys
import time
import Queue
import threading
import urlparse
import psutil
import datetime

from django.core.exceptions import ObjectDoesNotExist
from facepy.exceptions import FacepyError
from fandjango.models import User as FanUser, OAuthToken
from snh.models.facebookmodel import *

import snhlogger
logger = snhlogger.init_logger(__name__, "facebook.log")

E_DNEXIST = "E_DNEXIST"
E_PATH = "E_PATH"
E_FALSE = "E_FALSE"
E_UNMAN = "E_UNMAN"
E_UNEX = "E_UNEX"
E_USER_QUOTA = "E_USER_QUOTA"
E_QUOTA = "E_QUOTA"
E_GRAPH = "E_GRAPH"
E_MAX_RETRY = "E_MAX_RETRY"

E_CRITICALS = [E_DNEXIST, E_PATH, E_FALSE, E_UNMAN, E_USER_QUOTA]

def run_facebook_harvester():
    harvester_list = FacebookHarvester.objects.all()
    fanuser = FanUser.objects.all()[0]
    for harvester in harvester_list:
        harvester.set_client(fanuser.graph)
        logger.info(u"The harvester %s is %s" % 
                                                (unicode(harvester), 
                                                "active" if harvester.is_active else "inactive"))
        if harvester.is_active:
            run_harvester_v3(harvester)

def gbp_error_man(bman_obj, fbobj):

    e_code = E_UNMAN
    error = None

    if fbobj:
        error = unicode(fbobj).split(":")[1].strip()
    else:
        msg = u"fbobj is None!! bman:%s" % bman_obj
        logger.error(msg)

    if error:
        e_code = gbp_facepyerror_man(error, fbobj)

    bman_obj["retry"] += 1

    return e_code

def gbp_facepyerror_man(fex, src_obj=None):

    e_code = E_UNMAN
    if unicode(fex).startswith(u"(#803)"):
        e_code = E_DNEXIST
    elif unicode(fex).startswith("(#613)"):
        e_code = E_QUOTA
    elif unicode(fex).startswith("(#4) User request limit reached"):
        e_code = E_USER_QUOTA
    elif unicode(fex).startswith("GraphMethodException"):
        e_code = E_GRAPH
    elif unicode(fex).startswith("Error: An unexpected error has occurred"):
        e_code = E_UNEX
    elif unicode(fex).startswith("An unknown error occurred"):
        e_code = E_UNEX
    elif unicode(fex).startswith("Unknown path components"):
        e_code = E_PATH
    elif unicode(fex).startswith("false"):
        e_code = E_FALSE
    elif unicode(fex).startswith("Max retries exceeded for url:"):
        e_code = E_MAX_RETRY
    else:
        e_code = E_UNMAN

    msg = "e_code:%s, msg:%s src:%s" % (e_code, fex, src_obj)
    logger.error(msg)

    return e_code

def gbp_core(harvester, bman_chunk, error_map, next_bman_list, failed_list):

    error = False

    try:
        urlized_batch = [bman_chunk[j]["request"] for j in range(0, len(bman_chunk))]
        batch_result = harvester.api_call("batch",{"requests":urlized_batch})

        for (counter, fbobj) in enumerate(batch_result):
            bman_obj = bman_chunk[counter]
    
            if type(fbobj) == dict:
                next = bman_obj["callback"](harvester, bman_obj["snh_obj"], fbobj)
                if next:
                    next_bman_list += next
            else:
                e_code = gbp_error_man(bman_obj, fbobj)
                if e_code == E_UNEX:
                    error = True
                error_map[e_code] = error_map[e_code] + 1 if e_code in error_map else 0

                if e_code in E_CRITICALS:
                    failed_list.append(bman_obj)
                else:
                    next_bman_list.append(bman_obj)

    except FacepyError, fex:
        e_code = gbp_facepyerror_man(fex, {"bman_chunk":bman_chunk})
        if e_code == E_UNEX:
            error = True
        error_map[e_code] = error_map[e_code] + 1 if e_code in error_map else 0

        if e_code in E_CRITICALS:
            msg = u"CRITICAL gbp_core: Unmanaged FacepyError error:%s. Aborting a full bman_chunk." % (e_code)
            logger.exception(msg)
            failed_list += bman_chunk
        else:
            next_bman_list += bman_chunk

    except:
        error = True
        msg = u"CRITICAL gbp_core: Unmanaged error. Aborting a full bman_chunk."
        logger.exception(msg)
        failed_list += bman_chunk

    return error

def generic_batch_processor_v2(harvester, bman_list):

    error_map = {}
    next_bman_list = []
    failed_list = []
    max_step_size = 50
    step_size = max_step_size #full throttle!
    fail_ratio = 0.15
    step_factor = 1.66
    lap_start = time.time()
    bman_total = 1
    error_sum = 0

    while bman_list:
        usage = psutil.virtual_memory
        logger.info(u"New batch. Size:%d for %s Mem:%s MB" % (len(bman_list), harvester, int(usage[4])/(1024.0)))

        if (E_UNEX in error_map and error_map[E_UNEX] / float(bman_total) > fail_ratio) or error_sum > 4:
            step_size = int(step_size / step_factor) if int(step_size / step_factor) > 1 else 1
            del error_map[E_UNEX]
        else:
            step_size = step_size * 2 if step_size * 2 < max_step_size else max_step_size

        split_bman = [bman_list[i:i+step_size] for i  in range(0, len(bman_list), step_size)]
        bman_total = len(split_bman)

        for (counter, bman_chunk) in enumerate(split_bman,1):
            
            if not(E_UNEX in error_map and error_map[E_UNEX] / float(bman_total) > fail_ratio) or not (E_USER_QUOTA in error_map):
                actual_fail_ratio = error_map[E_UNEX] / float(bman_total) if E_UNEX in error_map else 0
                usage = psutil.virtual_memory
                logger.info(u"bman_chunk (%d/%d) chunk_total:%s InQueue:%d fail_ratio:%s > %s Mem:%s KB" % (counter, bman_total, len(bman_chunk), len(next_bman_list), actual_fail_ratio, fail_ratio, getattr(usage, "ru_maxrss")/(1024.0)))

                if E_QUOTA in error_map:
                    logger.info("Quota error, waiting for 10 minutes")
                    del error_map[E_QUOTA]
                    time.sleep(10*60)
                
                if (time.time() - lap_start) < 1:
                    logger.info(u"Speed too fast. will wait 1 sec")
                    time.sleep(1)

                lap_start = time.time()
                error = gbp_core(harvester, bman_chunk, error_map, next_bman_list, failed_list)
                error_sum = error_sum + 1 if error else 0
                logger.info(u"gbp_core: len(next_bman_list): %s" % len(next_bman_list))
            elif E_USER_QUOTA in error_map:
                logger.error("bman(%d/%d) User quota reached. Aborting the harvest!" % (counter, bman_total))
                failed_list += bman_chunk
            else:
                logger.info("bman(%d/%d) Failed ratio too high. Retrying with smaller batch" % (counter, bman_total))
                next_bman_list += bman_chunk

        bman_list = next_bman_list
        next_bman_list = []

    usage = psutil.virtual_memory
    readable_failed_list = [failed_list[j]["request"]["relative_url"] for j in range(0, len(failed_list))]
    logger.debug(u"END harvesting. Mem:%s MB" % int(usage[4])/(1024.0))
    logger.debug(u"Failed list: %s" % (readable_failed_list))

def get_feed_paging(page):
    until = None
    new_page = False
    if u"paging" in page and u"next" in page[u"paging"]:
        url = urlparse.parse_qs(page[u"paging"][u"next"])
        until = url[u"until"][0]
        new_page = True
    return ["until",until], new_page

def get_comment_paging(page):
    __after_id = None
    new_page = False
    if u"paging" in page and u"next" in page[u"paging"]:
        url = urlparse.parse_qs(page[u"paging"][u"next"].split("?")[1])
        __after_id = url[u"__after_id"][0]
        offset = url[u"offset"][0]
        new_page = True
    return "offset=%s&__after_id=%s" % (offset, __after_id), new_page

def update_user_statuses(harvester, statuses):
    for res in statuses:
        status = eval(res.result)
        snhuser = FBUser.objects.get(fid=res.parent)
        try:
            try:
                fb_status = FBPost.objects.get(fid=status["id"])
            except ObjectDoesNotExist:
                fb_status = FBPost(user=snhuser)
                fb_status.save()
            fb_status.update_from_facebook(status,snhuser)
        except:
            msg = u"Cannot update status %s for %s:(%s)" % (unicode(status), unicode(snhuser), snhuser.fid if snhuser.fid else "0")
            logger.exception(msg) 

def update_user_from_batch(harvester, snhuser, fbuser):
    snhuser.update_from_facebook(fbuser)
    return None

def update_user_batch(harvester):

    all_users = harvester.fbusers_to_harvest.all()
    batch_man = []

    for snhuser in all_users:
        if not snhuser.error_triggered:
            uid = snhuser.fid if snhuser.fid else snhuser.username
            d = {"method": "GET", "relative_url": uid}
            batch_man.append({"snh_obj":snhuser,"retry":0,"request":d, "callback":update_user_from_batch})
        else:
            logger.info(u"Skipping user update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    usage = psutil.virtual_memory
    logger.info(u"Will harvest users for %s Mem:%s MB" % (harvester,int(usage[4])/(1024.0)))
    generic_batch_processor_v2(harvester, batch_man)

def update_user_status_from_batch(harvester, snhuser, status):

    res = FBResult()
    res.harvester = harvester
    res.result = status
    res.ftype = "FBPost"
    res.fid = status["id"]
    res.parent = snhuser.fid
    res.save()

def update_user_feed_from_batch(harvester, snhuser, fbfeed_page):
    next_bman = []
    feed_count = len(fbfeed_page["data"])
    too_old = False

    if feed_count:
        usage = psutil.virtual_memory
        logger.debug(u"Updating %d feeds: %s Mem:%s MB" % (feed_count, harvester, int(usage[4])/(1024.0)))

        for feed in fbfeed_page["data"]:
            if feed["created_time"]:
                feed_time = datetime.strptime(feed["created_time"],'%Y-%m-%dT%H:%M:%S+0000')
            else:
                feed_time = datetime.strptime(feed["updated_time"],'%Y-%m-%dT%H:%M:%S+0000')
            
            if feed_time > harvester.harvest_window_from and \
                    feed_time < harvester.harvest_window_to:
                lc_param = ""
                
                if "link" in feed:
                    if feed["link"].startswith("https://www.facebook.com/notes") or feed["link"].startswith("http://www.facebook.com/notes"):
                        spliturl = feed["link"].split("/")
                        lid = spliturl[len(spliturl)-1]
                        d = {"method": "GET", "relative_url": u"%s" % unicode(lid)}
                        next_bman.append({"snh_obj":snhuser, "retry":0, "request":d, "callback":update_user_status_from_batch})

                        d = {"method": "GET", "relative_url": u"%s/comments?limit=300%s" % (unicode(lid), lc_param)}
                        next_bman.append({"snh_obj":str(lid),"retry":0,"request":d, "callback":update_user_comments_from_batch})

                        if harvester.update_likes:
                            d = {"method": "GET", "relative_url": u"%s/likes?limit=300%s" % (unicode(lid), lc_param)}
                            next_bman.append({"snh_obj":str(lid),"retry":0,"request":d, "callback":update_likes_from_batch})

                update_user_status_from_batch(harvester, snhuser, feed)

                d = {"method": "GET", "relative_url": u"%s/comments?limit=300%s" % (unicode(feed["id"]), lc_param)}
                next_bman.append({"snh_obj":str(feed["id"]),"retry":0,"request":d, "callback":update_user_comments_from_batch})

                if harvester.update_likes:
                    d = {"method": "GET", "relative_url": u"%s/likes?limit=300%s" % (unicode(feed["id"]), lc_param)}
                    next_bman.append({"snh_obj":str(feed["id"]),"retry":0,"request":d, "callback":update_likes_from_batch})

            if feed_time < harvester.harvest_window_from:
                too_old = True
                break

        paging, new_page = get_feed_paging(fbfeed_page)

        if not too_old and new_page:
            d = {"method": "GET", "relative_url": u"%s/feed?limit=300&%s=%s" % (unicode(snhuser.fid), paging[0], paging[1])}
            next_bman.append({"snh_obj":snhuser, "retry":0, "request":d, "callback":update_user_feed_from_batch})
    #else:
    #    logger.debug(u"Empty feed!! %s" % (fbfeed_page))

    return next_bman

def update_user_statuses_batch(harvester):

    all_users = harvester.fbusers_to_harvest.all()
    batch_man = []

    for snhuser in all_users:
        if not snhuser.error_triggered:
            uid = snhuser.fid if snhuser.fid else snhuser.username
            d = {"method": "GET", "relative_url": u"%s/feed?limit=300" % unicode(uid)}
            batch_man.append({"snh_obj":snhuser,"retry":0,"request":d,"callback":update_user_feed_from_batch})
        else:
            logger.info(u"Skipping status update: %s(%s) because user has triggered the error flag." % (unicode(snhuser), snhuser.fid if snhuser.fid else "0"))

    usage = psutil.virtual_memory
    logger.info(u"Will harvest statuses for %s Mem:%s MB" % (harvester, int(usage[4])/(1024.0)))
    generic_batch_processor_v2(harvester, batch_man)

def update_user_comments(harvester, fbcomments):
    for fbresult in fbcomments:
        fbcomment = eval(fbresult.result)
        status = FBPost.objects.get(fid=fbresult.parent)
        try:
            try:
                snh_comment = FBComment.objects.get(fid=fbcomment["id"])
            except ObjectDoesNotExist:
                snh_comment = FBComment()
                snh_comment.save()
            snh_comment.update_from_facebook(fbcomment, status)                
        except:
            msg = u"Cannot update comment %s" % (fbcomment)
            logger.exception(msg) 

def update_user_comments_from_batch(harvester, statusid, fbcomments_page):
    next_bman = []

    if "data" not in fbcomments_page:
        logger.debug("DEVED: %s: %s" % (statusid, fbcomments_page))

    comment_count = len(fbcomments_page["data"])

    if comment_count:

        for comment in fbcomments_page["data"]:
            res = FBResult()
            res.harvester = harvester
            res.result = comment
            res.ftype = "FBComment"
            res.fid = comment["id"]
            res.parent = statusid
            res.save()

        paging, new_page = get_comment_paging(fbcomments_page)
        
        usage = psutil.virtual_memory
        logger.debug(u"Updating %d comments. New: %s Paging: %s Mem:%s MB" % (comment_count, new_page, paging, int(usage[4])/(1024.0)))

        if new_page:
            d = {"method": "GET", "relative_url": u"%s/comments?limit=300&%s" % (statusid, paging)}
            next_bman.append({"snh_obj":statusid,"retry":0,"request":d,"callback":update_user_comments_from_batch})
    #else:
    #    logger.debug("Empty comment page!! %s" % fbcomments_page)

    return next_bman

def update_likes_from_batch(harvester, statusid, fblikes_page):
    next_bman = []
    likes_count = len(fblikes_page["data"])

    if likes_count:
        res = FBResult()
        res.harvester = harvester
        res.result = fblikes_page["data"]
        res.ftype = "FBPost.likes"
        res.fid = statusid
        res.parent = statusid
        res.save()

        paging, new_page = get_comment_paging(fblikes_page)

        usage = psutil.virtual_memory
        logger.debug(u"Updating %d likes. statusid:%s paging:%s Mem:%s MB" % (likes_count, statusid, paging, int(usage[4])/(1024.0)))
        
        if new_page:
            d = {"method": "GET", "relative_url": u"%s/likes?limit=300&%s" % (statusid, paging)}
            next_bman.append({"snh_obj":statusid,"retry":0,"request":d,"callback":update_likes_from_batch})
    #else:
    #    logger.debug(u"Empty likes page!! %s" % fblikes_page)

    return next_bman

queue = Queue.Queue()

class ThreadStatus(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        statuscount = 0
        logger.info(u"ThreadStatus %s. Start." % self)
        while True: 
            try:
                fid = self.queue.get()
                fbpost = FBResult.objects.filter(fid=fid).filter(ftype="FBPost")[0]
                user = FBUser.objects.get(fid=fbpost.parent)
                rez = eval(fbpost.result)
                snh_status = self.update_user_status(rez,user)
                fbpost.delete()
                #signals to queue job is done
            except ObjectDoesNotExist:
                logger.exception("DEVED %s %s" % (fbpost.parent, fbpost.ftype))
            except Queue.Empty:
                logger.info(u"ThreadStatus %s. Queue is empty." % self)
                break;
            except:
                msg = u"ThreadStatus %s. Error" % self
                logger.exception(msg)
            finally:
                self.queue.task_done()
                
        logger.info(u"ThreadStatus %s. End." % self)

    def update_user_status(self, fbstatus, user):
        snh_status = None
        try:
            try:
                snh_status = FBPost.objects.get(fid=fbstatus["id"])
            except ObjectDoesNotExist:
                snh_status = FBPost(user=user)
                snh_status.save()
            snh_status.update_from_facebook(fbstatus,user)
            likes_list = FBResult.objects.filter(ftype="FBPost.likes").filter(parent=fbstatus["id"])
            all_likes = []            
            for likes in likes_list:
                all_likes += eval(likes.result)
            snh_status.update_likes_from_facebook(all_likes)
            likes_list.delete()
        except IntegrityError:
            try:
                snh_status = FBPost.objects.get(fid=fbstatus["id"])
                snh_status.update_from_facebook(fbstatus, user)
            except ObjectDoesNotExist:
                msg = u"ERROR! Post already exist but not found %s for %s" % (unicode(fbstatus), user.fid if user.fid else "0")
                logger.exception(msg) 
        except:
            msg = u"Cannot update status %s for %s" % (unicode(fbstatus), user.fid if user.fid else "0")
            logger.exception(msg) 
        return snh_status

class ThreadComment(threading.Thread):
    def __init__(self, commentqueue):
        threading.Thread.__init__(self)
        self.queue = commentqueue

    def run(self):
        logger.info(u"ThreadComment %s. Start." % self)
        while True: 

            try:
                fid = self.queue.get()
                if fid:
                    fbcomment = FBResult.objects.filter(fid=fid)[0]
                    post = FBPost.objects.get(fid=fbcomment.parent)
                    self.update_comment_status(eval(fbcomment.result), post)
                    fbcomment.delete()
                else:
                    logger.error(u"ThreadComment %s. fid is none! %s." % (self, fid))
                #signals to queue job is done
            except Queue.Empty:
                logger.info(u"ThreadComment %s. Queue is empty." % self)
                break;
            except:
                msg = u"ThreadComment %s. Error." % self
                logger.exception(msg)                 
            finally:
                self.queue.task_done()
                
        logger.info(u"ThreadComment %s. End." % self)

    def update_comment_status(self, comment, post):
        fbcomment = None
        try:
            try:
                fbcomment = FBComment.objects.get(fid=comment["id"])
            except ObjectDoesNotExist:
                fbcomment = FBComment(post=post)
                fbcomment.save()
            fbcomment.update_from_facebook(comment,post)
        except IntegrityError:
            try:
                fbcomment = FBComment.objects.get(fid=comment["id"])
                fbcomment.update_from_facebook(comment,post)
            except ObjectDoesNotExist:
                msg = u"ERROR! Comments already exist but not found%s for %s" % (unicode(comment), post.fid if post.fid else "0")
                logger.exception(msg) 
        except:
            msg = u"Cannot update comment %s for %s" % (unicode(comment), post.fid if post.fid else "0")
            logger.exception(msg) 
        return fbcomment

def compute_new_post(harvester):
    global queue
    queue = Queue.Queue()
    all_posts = FBResult.objects.filter(ftype="FBPost").values("fid")
    for post in all_posts:
        queue.put(post["fid"])

    for i in range(3):
        t = ThreadStatus(queue)
        t.setDaemon(True)
        t.start()
      
    queue.join()

def compute_new_comment(harvester):
    global commentqueue
    commentqueue = Queue.Queue()

    all_comments = FBResult.objects.filter(ftype="FBComment").values("fid")
    for comment in all_comments:
        commentqueue.put(comment["fid"])

    for i in range(3):
        t = ThreadComment(commentqueue)
        t.setDaemon(True)
        t.start()
      
    commentqueue.join()

def compute_results(harvester):
    if FBResult.objects.filter(harvester=harvester).count() != 0: 
        start = time.time()
        logger.info(u"Starting results computation")
        compute_new_post(harvester) 
        compute_new_comment(harvester)
        FBResult.objects.filter(harvester=harvester).delete()
        logger.info(u"Results computation complete in %ss" % (time.time() - start))

def run_harvester_v3(harvester):
    harvester.start_new_harvest()
    try:
        #launch result computation in case where the previous harvest was interrupted
        compute_results(harvester)
        update_user_batch(harvester)
        update_user_statuses_batch(harvester)
        compute_results(harvester)
    except:
        logger.exception(u"EXCEPTION: %s" % harvester)
    finally:
        usage = psutil.virtual_memory
        harvester.end_current_harvest()
        logger.info(u"End: %s Stats:%s Mem:%s MB" % (harvester,unicode(harvester.get_stats()), int(usage[4])/(1024.0)))

