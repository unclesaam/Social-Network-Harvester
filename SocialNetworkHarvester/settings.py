# coding=UTF-8
# Django settings for SocialNetworkHarvester project.
import os
import logging
import sys

PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])
LOG_LEVEL = logging.DEBUG

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'snh_schema',                 # Or path to database file if using sqlite3.
        'USER': 'snh',                        # Not used with sqlite3.
        'PASSWORD': '123123',                 # Not used with sqlite3.
        'HOST': '127.0.0.1',                  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',                           # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            "init_command": "SET foreign_key_checks = 0;",
        }
    }
}

FACEBOOK_APPLICATION_ID = 'xxx'
FACEBOOK_APPLICATION_SECRET_KEY = 'xxx'
FACEBOOK_APPLICATION_NAMESPACE = 'xxx'
FACEBOOK_APPLICATION_ID = 'xxxxx'
FACEBOOK_APPLICATION_SECRET_KEY = 'xxxx'
FACEBOOK_APPLICATION_NAMESPACE = 'xxxx'
FACEBOOK_APPLICATION_INITIAL_PERMISSIONS = [
                                            'user_about_me','friends_about_me',
                                            'user_activities','friends_activities',
                                            'user_birthday','friends_birthday',
                                            'user_checkins','friends_checkins',
                                            'user_education_history','friends_education_history',
                                            'user_events','friends_events',
                                            'user_groups','friends_groups',
                                            'user_hometown','friends_hometown',
                                            'user_interests','friends_interests',
                                            'user_likes','friends_likes',
                                            'user_location','friends_location',
                                            'user_notes','friends_notes',
                                            #'user_photo_video_tags','friends_photo_video_tags',
                                            'user_photos','friends_photos',
                                            'user_questions','friends_questions',
                                            'user_relationships','friends_relationships',
                                            'user_relationship_details','friends_relationship_details',
                                            'user_religion_politics','friends_religion_politics',
                                            'user_status','friends_status',
                                            'user_videos','friends_videos',
                                            'user_website','friends_website',
                                            'user_work_history','friends_work_history',
                                            'email',
                                            'read_friendlists',
                                            'read_insights',
                                            'read_mailbox',
                                            'read_requests',
                                            'read_stream',
                                            'xmpp_login',
                                            'ads_management',
                                            'create_event',
                                            'manage_friendlists',
                                            'manage_notifications',
                                            #'offline_access',
                                            'user_online_presence',
                                            'friends_online_presence',
                                            'publish_checkins',
                                            'publish_stream',
                                            'rsvp_event',
                                            #'publish_actions',
                                            ]

#FACEBOOK_APPLICATION_INITIAL_PERMISSIONS = ['read_stream', 'publish_stream','friends_online_presence','friends_status','read_friendlists']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Montreal'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-ca'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, "upload/")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, "public/")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = STATIC_URL + "grappelli/"

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, "static/"),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'b6%$tv8f@y3s8*tm!b0$(a4u^#j_#itv9d7g7%wx-@0cdt9_*l'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'fandjango.middleware.FacebookMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, "templates/"),
)

GRAPPELLI_ADMIN_TITLE = "<a href='/admin'>SNH Admin</a> | <a href='/'>Consultation</a> | <a href='/test_fb_token'>Test Facebook token</a>"

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'fandjango',
    'snh',
    'grappelli.dashboard',
    'grappelli',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

GRAPPELLI_ADMIN_TITLE = "<a href='/admin'>SNH Admin</a> | <a href='/'>Consultation</a> | <a href='/test_fb_token'>Test Facebook token</a>"

LOGIN_REDIRECT_URL = "/"

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.request",
    "django.core.context_processors.i18n",
    'django.contrib.messages.context_processors.messages',
)

GRAPPELLI_INDEX_DASHBOARD = {
    'django.contrib.admin.site': 'snh.dashboard.CustomIndexDashboard',
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
