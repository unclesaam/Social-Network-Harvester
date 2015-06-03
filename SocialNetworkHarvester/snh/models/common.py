# coding=UTF-8

from datetime import datetime
from django.db import models

from settings import DEBUGCONTROL, dLogger
debugging = DEBUGCONTROL['commonmodel']
if debugging: print "DEBBUGING ENABLED IN %s"%__name__

class AbstractHaverster(models.Model):

    class Meta:
        app_label = "snh"
        abstract = True

    def __unicode__(self):
        return u"%s" % unicode(self.harvester_name)

    def harvester_type_func():
        return "AbstractHaverster"

    pmk_id = models.AutoField(primary_key=True)

    harvester_type = models.CharField(max_length=255, null=True)
    harvester_name = models.CharField(max_length=255, null=True)

    is_active = models.BooleanField()
    harvest_in_progress =  models.BooleanField()
    last_user_harvest_was_aborted =  models.BooleanField()
    retry_user_after_abortion =  models.BooleanField()

    last_harvest_start_time = models.DateTimeField(null=True)
    last_harvest_end_time = models.DateTimeField(null=True)

    current_harvest_start_time = models.DateTimeField(null=True)

    max_retry_on_fail = models.IntegerField(null=True)

    dont_harvest_further_than = models.IntegerField(null=True)

    harvest_window_from = models.DateTimeField(null=True)
    harvest_window_to = models.DateTimeField(null=True)

    full_harvest_on_next_run = models.BooleanField()

    def start_new_harvest(self):
        self.current_harvest_start_time = datetime.utcnow()
        self.current_harvest_call_count = 0
        self.harvest_in_progress = True
        self.save()

    def end_current_harvest(self):
        self.last_harvest_start_time = self.current_harvest_start_time
        self.last_harvest_end_time = datetime.utcnow()
        self.current_harvest_start_time = None
        self.last_harvest_call_count = self.current_harvest_call_count
        self.last_user_harvest_was_aborted = bool(self.get_current_harvested_user())
        self.harvest_in_progress = False
        self.save()

    def api_call(self, method, params):
        pass

    def get_last_harvested_user(self):
        raise NotImplementedError( "Should have implemented this" )

    def get_current_harvested_user(self):
        raise NotImplementedError( "Should have implemented this" )

    def get_next_user_to_harvest(self):
        raise NotImplementedError( "Should have implemented this" )

    def get_stats(self):
        if debugging: 
            dLogger.log('<Harvester: \'%s\'>::get_stats()'%self)
            #dLogger.log('    harvester_type: %s'%self.harvester_type)
            #dLogger.log('    harvester_name: %s'%self.harvester_name)
            #dLogger.log('    is_active: %s'%self.is_active)
            #dLogger.log('    harvest_in_progress: %s'%self.harvest_in_progress)
            #dLogger.log('    last_harvest_start_time: %s'%self.last_harvest_start_time)
            #dLogger.log('    last_harvest_end_time: %s'%self.last_harvest_end_time)
            #dLogger.log('    last_user_harvest_was_aborted: %s'%self.last_user_harvest_was_aborted)
            #dLogger.log('    current_harvest_start_time: %s'%self.current_harvest_start_time)
            
        return {"abstract":
                    {
                    "harvester_type":self.harvester_type,
                    "harvester_name":self.harvester_name,

                    "is_active":self.is_active,
                    "harvest_in_progress":self.harvest_in_progress,

                    "last_harvest_start_time":self.last_harvest_start_time,
                    "last_harvest_end_time":self.last_harvest_end_time,

                    "last_user_harvest_was_aborted":self.last_user_harvest_was_aborted,

                    "current_harvest_start_time":self.current_harvest_start_time,
                    },
                "concrete":{},
                }

class URL(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.original_url or 'None'

    pmk_id =  models.AutoField(primary_key=True)
    original_url = models.TextField(null=True)
    unshorten_url = models.TextField(null=True)
    take_snapshot = models.BooleanField()
    snapshot_file_path = models.TextField(null=True)

class Tag(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.text

    pmk_id =  models.AutoField(primary_key=True)
    text = models.TextField(null=True)

class Image(models.Model):

    class Meta:
        app_label = "snh"

    def __unicode__(self):
        return self.name

    pmk_id =  models.AutoField(primary_key=True)
    name = models.TextField(null=True)
