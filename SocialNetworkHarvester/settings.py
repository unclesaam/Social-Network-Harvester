# coding=UTF-8
# Django settings for SocialNetworkHarvester project.
import os
import logging
import sys
from DebugLogger import DebugLogger
from warnings import filterwarnings, resetwarnings
import MySQLdb as Database

PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])
LOG_LEVEL = logging.INFO

PROD = True

dLogger = DebugLogger('debug'+__name__, os.path.join(PROJECT_PATH,"log/debugLogger.log"), '<%(thread)d>%(message)s')
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

if PROD: #en mode production:
    DEBUG = False
    DEBUGCONTROL = {'commonmodel':      False,
                    'facebookmodel':    False,
                    'dailymotionmodel': False,
                    'twittermodel':     False,
                    'youtubemodel':     False,
                    'facebookch':       False,
                    'twitterch':        False,
                    'dailymotionch':    False,
                    'youtubech':        False,
                    'twitterview':      False
                    }

    DOWNLOADED_VIDEO_PATH = 'mnt/video/2015/'
    TEMPO_JSON_FILE_PATH = 'mnt/video/2015/JSON/Statuses.json'

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'snh_2015_schema',                
            'USER': 'root',                       
            'PASSWORD': 'grcp2014',                
            'HOST': '127.0.0.1',                 
            'PORT': '3306',                          
            'OPTIONS': {
                "init_command": "SET foreign_key_checks = 0;",
            }
        }
    }
    
    FACEBOOK_APPLICATION_ID = '382086531988825'
    FACEBOOK_APPLICATION_SECRET_KEY = '2079f3b96d08ef4edd8460fdab0db27c'
    FACEBOOK_APPLICATION_NAMESPACE = 'socnetapps'
    filterwarnings('ignore', category = Database.Warning)


else: # en mode développement:
    DEBUG = True
    DEBUGCONTROL = {'commonmodel':      True,
                    'facebookmodel':    True,
                    'dailymotionmodel': True,
                    'twittermodel':     True,
                    'youtubemodel':     True,
                    'facebookch':       True,
                    'twitterch':        True,
                    'dailymotionch':    True,
                    'youtubech':        True,
                    'twitterview':      True
                    }
    # For videos downloaded from youtube and dailymotion. Also contains the 
    # related captions files when available
    DOWNLOADED_VIDEO_PATH = 'C:\Users\Sam\Desktop\YoutubeVideos\\'
    TEMPO_JSON_FILE_PATH = 'C:\Users\Sam\Desktop/Statuses.json'

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            #'NAME': 'aspira_test',         
            'NAME': 'snh_2015_schema',       
            'USER': 'root',                       
            'PASSWORD': '1234',                
            'HOST': '127.0.0.1',                 
            'PORT': '3306',                          
            'OPTIONS': {
                "init_command": "SET foreign_key_checks = 0;",
            }
        }
    }
    FACEBOOK_APPLICATION_ID = '382086531988825'
    FACEBOOK_APPLICATION_SECRET_KEY = '2079f3b96d08ef4edd8460fdab0db27c'
    FACEBOOK_APPLICATION_NAMESPACE = 'aspiratest'
    resetwarnings()

TEMPLATE_DEBUG = DEBUG

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
    #'sslify.middleware.SSLifyMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'fandjango.middleware.FacebookMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

)

#SSLIFY_PORT = 80

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, "templates/"),
    os.path.join(PROJECT_PATH, "templates/admin/"),
)

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
    'django.contrib.admin',
)

GRAPPELLI_ADMIN_TITLE = "<a href='/admin'>SNH Admin</a> |\
                         <a href='/'>Consultation</a> |\
                         <a href='/test_fb_token'>Facebook token</a> |\
                         <a href='/event_logs'>Event logs</a>"

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
