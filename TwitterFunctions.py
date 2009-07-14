import sys, urllib2, urllib, base64

TWITTER_HOST='twitter.com'

def getUserTwitterFeed(screenName, since_id='', max_id='', count=5, page=1):
	data=''
	try:
		params=urllib.urlencode({'screen_name': screenName, 'count': count, 'page': page})
		if max_id !='':
			params=params+urllib.urlencode({'max_id': max_id})
		if since_id!='':
			params=params+urllib.urlencode({'since_id': since_id})
		#print 'http://twitter.com/statuses/user_timeline.xml?%s' %params
		request = urllib2.Request('http://twitter.com/statuses/user_timeline.xml?suppress_response_codes=true&%s' %params)
		u = urllib2.urlopen(request)
		data = u.read()
		return data
	except urllib2.HTTPError, e:
		error = 'HttpError: '+str(e.code)+str(e.read())
		raise TwitterException(error)
	except urllib2.URLError, e:
		error ='URLError: '+str(e.reason)
		raise TwitterException(error)
	except Exception, e:
		error =' Unknown Exception: '+str(e)
		raise TwitterException(e)

def getFriendTwitterFeed(username, password, since_id='', max_id='', count=5, page=1):
	try:
		data=''	
		__authenticate(username, password)
		data={'count': count, 'page': page}
		params = urllib.urlencode(data)
		if since_id!='':
			params=params+urllib.urlencode({'since_id': since_id})
		if max_id!='':
			params=params+urllib.urlencode({'max_id': max_id})
		request = urllib2.Request('http://twitter.com/statuses/friends_timeline.xml?%s' %params)
		response = urllib2.urlopen(request)
		#print response.geturl()
		data = response.read()
		return data
	except urllib2.HTTPError, e:
		error = 'HttpError: '+str(e.code)+str(e.read())
		raise TwitterException(error)
	except urllib2.URLError, e:
		error ='URLError: '+str(e.reason)
		raise TwitterException(error)
	except Exception, e:
		error =' Unknown Exception: '+str(e)
		raise TwitterException(e)
	


def getTwitterStatus(id):
	try:
		url ='http://twitter.com/statuses/show/%s.xml?suppress_response_codes=true' %id
		request = urllib2.Request(url)
		u = urllib2.urlopen(request)
		data = u.read()
		return data
	except urllib2.HTTPError, e:
		error = 'HttpError: '+str(e.code)+str(e.read())
		raise TwitterException(error)
	except urllib2.URLError, e:
		error ='URLError: '+str(e.reason)
		raise TwitterException(error)
	except Exception, e:
		error =' Unknown Exception: '+str(e)
		raise TwitterException(e)

def getTwitterRateLimitStatus(username=None, password=None):
	try:	
		url='http://twitter.com/account/rate_limit_status.xml'
		if username and password:
			__authenticate(username, password)
		request = urllib2.Request(url)
		u = urllib2.urlopen(request)
		data = u.read()
		return data
	except urllib2.HTTPError, e:
		error = 'HttpError: '+str(e.code)+str(e.read())
		raise TwitterException(error)
	except urllib2.URLError, e:
		error ='URLError: '+str(e.reason)
		raise TwitterException(error)
	except Exception, e:
		error =' Unknown Exception: '+str(e)
		raise TwitterException(e)

def getSearchResults(query, lang=None, rpp=10, page=1, since_id=None, geocode='1.3667,103.9833,25km', show_user=True):
	try:
		if query:
			url='http://search.twitter.com/search.json'
			data={'rpp':rpp, 'page':page, 'geocode':geocode, 'show_user':show_user, 'q':query}
			params = urllib.urlencode(data)
			if since_id:
				params = params+urllib.urlencode({'since_id':since_id})
			if lang:
				params= params+urllib.urlencode({'lang': lang})
			request =urllib2.Request(url+'?%s' %params)
			response = urllib2.urlopen(request)
			data = response.read()
			return data
	except urllib2.HTTPError, e:
		error = 'HttpError: '+str(e.code)+str(e.read())
		raise TwitterException(error)
	except urllib2.URLError, e:
		error ='URLError: '+str(e.reason)
		raise TwitterException(error)
	except Exception, e:
		error =' Unknown Exception: '+str(e)
		raise TwitterException(e)
		


def __authenticate(username, password):
	passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
	passman.add_password(None, TWITTER_HOST, username, password)
	auth_handler = urllib2.HTTPBasicAuthHandler(passman)
	opener = urllib2.build_opener(auth_handler)
	urllib2.install_opener(opener)


class TwitterException(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)
