import sys, time
import xml.dom.minidom
import TwitterFunctions
import getpass
import threading
#import Tkinter as tk
import settings
import logging
import simplejson
import logging.handlers
from optparse import OptionParser

logger = logging.getLogger('twitterClient')
hdlr = logging.handlers.TimedRotatingFileHandler(settings.logFile, 'D', 1)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)



class Callable:
	def __init__(self, anycallable):
        	self.__call__ = anycallable



class Utils:
	def parseDate(date):
		# Sun Mar 18 06:42:26 +0000 2007
		#"Wed, 08 Apr 2009 19:22:10 +0000"
		try:
			dt_array = time.strptime(date,"%a %b %d %H:%M:%S +0000 %Y")
		except ValueError:
			dt_array =time.strptime(date, "%a, %d %b %Y %H:%M:%S +0000")
		return time.mktime(dt_array)

	def compareStatus(status1, status2):
		if status1.createdAt > status2.createdAt :
			return 1
		elif status1.createdAt == status2.createdAt :
			return 0
		else:
			return -1
	
	def getDisplayDate(date):
		return time.strftime('%d %b %Y %H:%M:%S', time.gmtime(date))

	def formatStatus(status, level=1):
		output =''
		displayDate = Utils.getDisplayDate(status.createdAt)
		#print displayDate
		#print status.user.screen_name
		#print unicode(status.text)
		output = displayDate.encode('utf8') +' '+status.user.screen_name.encode('utf8')+' :'+status.text.encode('utf8')+'\n'
		if(status.replyStatus != None):
			for i in range(level):
				output = output+'\t'
			output = output+Utils.formatStatus(status.replyStatus, level+1)
		return output

	parseDate =Callable(parseDate)
	compareStatus = Callable(compareStatus)	
	getDisplayDate = Callable(getDisplayDate)
	formatStatus = Callable(formatStatus)

class Result():
	def __init__(self, text, to_user_id, to_user, from_user, id, from_user_id, iso_lang_code, source, profile_image_url,  created_at):
		self.text = text
		self.to_user_id = to_user_id
		self.to_user = to_user
		self.from_user = from_user
		self.id = id
		self.from_user_id = from_user_id
		self.lang = iso_lang_code
		self.source = source
		self.profile_image_url = profile_image_url
		self.created_at = Utils.parseDate(created_at)

	def __str__(self):
		displayDate = Utils.getDisplayDate(self.created_at)
		return displayDate.encode('utf8')+' '+ self.from_user.encode('utf8')+' '+self.text.encode('utf8')


class Status:
	def __init__(self, id, user, createdAt, text, replyStatus=None):
		self.id = id
		self.user = user
		self.createdAt = Utils.parseDate(createdAt)
		self.text = text
		self.replyStatus = replyStatus

	def __str__(self):
		output = Utils.formatStatus(self)
		return output


class User:
	def __init__(self, id, screen_name, location, description, followers_count, created_at, statuses_count):
		self.id = id
		self.screen_name = screen_name
		self.location = location
		self.description = description
		self.followers_count = followers_count
		self.created_at = Utils.parseDate(created_at)
		self.statuses_count =statuses_count
	
	def __str__(self):
		return str(self.id)+","+str(self.screen_name)+","+str(self.location)+","+str(self.description)+","+str(self.followers_count)+","+str(self.created_at)+","+str(self.statuses_count)


class AccountRateLimit:
	def __init__(self, data):
		doc = xml.dom.minidom.parseString(data)
		self.__parseMessage(doc)

	def __parseMessage(self, doc):
		remainingHitsElement = doc.getElementsByTagName('remaining-hits')
		self.remainingHits= self.__parseTextValue(remainingHitsElement[0])
		hourlyLimitElement = doc.getElementsByTagName('hourly-limit')
		self.hourlyLimit = self.__parseTextValue(hourlyLimitElement[0])
		resetTimeElement = doc.getElementsByTagName('reset-time')
		self.resetTime = self.__parseTextValue(resetTimeElement[0])
		resetTimeSecondsElement = doc.getElementsByTagName('reset-time-in-seconds')
		self.resetTimeSeconds = self.__parseTextValue(resetTimeSecondsElement[0])

	def __parseTextValue(self, element):
		element.normalize()
		value=''
		for child in element.childNodes:
			if child.nodeType == child.TEXT_NODE:
				value = value + child.nodeValue
		return value

	def __str__(self):
		output='Remaining Hits: '+self.remainingHits+'\t HourlyLimit: '+self.hourlyLimit+'\t Reset Time: '+self.resetTime+'\t Reset Time Seconds: '+self.resetTimeSeconds
		return output


class TwitterFeed:
	
	def __init__(self, data, level=0, username=None, password=None):
		self.statusesDict ={}
		self.statuses=[]
		self.maxid=0
		self.username= username
		self.password = password
		self.__parse(data, level)

	
	def update(self, data , level=0):
		self.__parse(data, level)

	def __parse(self, data, level):
		doc = xml.dom.minidom.parseString(data)
		root = doc.documentElement
		#print root.localName
		if root.localName =='statuses' or root.localName =='status':
			self.__parseTwit(doc, level)
		else:
			self.__parseError(doc, level)

	def __parseTwit(self, doc, level):
		statusesElement = doc.getElementsByTagName("status")
		for statusElement in statusesElement:
			status = self.__parseStatus(statusElement, level)
			#for key, value in self.statusesDict.iteritems():
			#	logger.info(key)
			if not self.statusesDict.has_key(status.id):
				logger.info('adding status: '+status.text)
				self.statusesDict[status.id]=status
				self.statuses.append(status)
				if int(status.id)>self.maxid:
					self.maxid = int(status.id)
		logger.info('statuses length: '+ str(len(self.statuses)))
		logger.info('statusesDict length: '+ str(len(self.statusesDict)))

	def __parseError(self, doc, level):
		requestElement = doc.getElementsByTagName("request")
		request = self.__parseTextValue(requestElement[0])
		errorElement = doc.getElementsByTagName("error")
		error = self.__parseTextValue(errorElement[0])
		logger.error( 'Request: ' +request+' has '+error)
		raise TwitterFunctions.TwitterException('Request: ' +request+' has '+error)

	
	def __parseStatus(self, statusElement, level):
		idElement = statusElement.getElementsByTagName("id")
		id = self.__parseTextValue(idElement[0])
		createdAtElement = statusElement.getElementsByTagName("created_at")
		createdAt = self.__parseTextValue(createdAtElement[0])
		textElement = statusElement.getElementsByTagName("text")
		text = self.__parseTextValue(textElement[0])
		inReplyStatusElement = statusElement.getElementsByTagName("in_reply_to_status_id")
		inReplyStatus = self.__parseTextValue(inReplyStatusElement[0])
		if (inReplyStatus!=''):
			replyStatus= self.__getReplyStatus(inReplyStatus, level)
		else:
			replyStatus=None
		userElement = statusElement.getElementsByTagName("user")
		user = self.__parseUser(userElement[0])
		status = Status(id, user, createdAt, text, replyStatus)
		return status
	
	def __getReplyStatus(self, inReplyStatus, level):
		if level > 3:
			return None
		else:
			try:
				data = TwitterFunctions.getTwitterStatus(inReplyStatus)
				#print data
				twitterFeed = TwitterFeed(data, level+1)
				return twitterFeed.statuses[0]
			except TwitterFunctions.TwitterException, ex:
				return None

	def __parseTextValue(self, element):
		element.normalize()
		value=''
		for child in element.childNodes:
			if child.nodeType == child.TEXT_NODE:
				value = value + child.nodeValue
		return value


	def __parseUser(self, userElement):
		id = self.__parseTextValue(userElement.getElementsByTagName("id")[0])
		screen_name= self.__parseTextValue(userElement.getElementsByTagName("screen_name")[0])
		location = self.__parseTextValue(userElement.getElementsByTagName("location")[0])
		description= self.__parseTextValue(userElement.getElementsByTagName("description")[0])
		followers_count=self.__parseTextValue(userElement.getElementsByTagName("followers_count")[0])
		friends_count=self.__parseTextValue(userElement.getElementsByTagName("friends_count")[0])
		created_at=self.__parseTextValue(userElement.getElementsByTagName("created_at")[0])
		statuses_count=self.__parseTextValue(userElement.getElementsByTagName("statuses_count")[0])
		return User(id, screen_name, location, description, followers_count, created_at, statuses_count)


class ResultPage():
	def __init__(self, json):
		self.results=[]
		simplejson.loads(json, object_hook=self.__parseResultPageJSON)

	
	def __parseResultPageJSON(self, jsonDct):
		if 'since_id' in jsonDct:
			self.since_id =  jsonDct['since_id']				
			self.max_id = jsonDct['max_id']
			self.refresh_url = jsonDct['refresh_url']
			self.results_per_page= jsonDct['results_per_page']
			if 'next_page' in jsonDct:
				self.next_page = jsonDct['next_page']
			else:
				self.next_page = None
			self.completed_in = jsonDct['completed_in']
			self.page = jsonDct['page']
			self.query = jsonDct['query']
		else:
			text = jsonDct['text']
			to_user_id = jsonDct['to_user_id']
			if 'to_user' in jsonDct:
				to_user = jsonDct['to_user']
			else:
				to_user=None
			from_user = jsonDct['from_user']
			#print jsonDct
			id = jsonDct['id']
			from_user_id = jsonDct['from_user_id']
			lang = jsonDct['iso_language_code']
			source = jsonDct['source']
			profile_image_url = jsonDct['profile_image_url']
			created_at = jsonDct['created_at']
			result = Result(text, to_user_id, to_user, from_user, id, from_user_id, lang, source, profile_image_url, created_at)		
			self.results.append(result)
				
	def __str__(self):
		output=''
		for result in self.results:
			 output+=str(result)+'\n'
		return output


			
class Runner(threading.Thread):

	def __init__(self, function, *args):
		threading.Thread.__init__(self)
		self.__function = function
		#print args
		self.__args = args
		self.event = threading.Event()

	def run(self):
		logger.info('Runner Thread has started!')
		self.event.set()
		self.__function(self.__args)
		self.event.clear()



def trackUserFeed(args):
	screen_name=args[0]
	#print screen_name
	while True:
		try:
			if 'twitterFeed' in locals():
				maxid = twitterFeed.maxid
			else:
				maxid = 0
			rateData = TwitterFunctions.getTwitterRateLimitStatus()
			accountRateLimit = AccountRateLimit(rateData)
			print accountRateLimit
			if int(accountRateLimit.remainingHits) ==0:
				time.sleep(int(accountRateLimit.resetTimeSeconds)-int(time.time())+5)
			data = TwitterFunctions.getUserTwitterFeed(screen_name, maxid, '', 10)
			if not 'twitterFeed' in locals():
				twitterFeed = TwitterFeed(data)
			twitterFeed.update(data)
			displayStatus(twitterFeed)
			time.sleep(90)
		except TwitterFunctions.TwitterException, ex:
			logger.error(ex)
			continue

def trackFriendFeed(args):
	screen_name = args[0]
	password = args[1]
	if password=='' or password==None:
		password = getpass.getpass('Enter '+screen_name+' password: ')
	while True:
		try:
			if 'twitterFeed' in locals():
				logger.info('Choon Kee')
				maxid = twitterFeed.maxid
			else:
				logger.info('not choon kee')
				maxid = 0
			
			rateData = TwitterFunctions.getTwitterRateLimitStatus(screen_name, password)
			accountRateLimit = AccountRateLimit(rateData)
			print accountRateLimit
			if int(accountRateLimit.remainingHits) ==0:
				time.sleep(int(accountRateLimit.resetTimeSeconds)-int(time.time())+5)
			data = TwitterFunctions.getFriendTwitterFeed(screen_name, password, maxid, '', 10)
			if not 'twitterFeed' in locals():
				twitterFeed = TwitterFeed(data)
			twitterFeed.update(data)
			displayStatus(twitterFeed)	
			time.sleep(90)
		except TwitterFunctions.TwitterException, ex:
			logger.error(ex)
			continue
			
def getAccountRateLimit(args):
	screen_name = args[0]
	password = args[1]
	if screen_name:
		if password:
			rateData = TwitterFunctions.getTwitterRateLimitStatus(screen_name, password)
			accountRateLimit = AccountRateLimit(rateData)
			print accountRateLimit
		else:
			password = getpass.getpass('Enter '+screen_name+' password: ')
			rateData = TwitterFunctions.getTwitterRateLimitStatus(screen_name, password)
			accountRateLimit = AccountRateLimit(rateData)
			print accountRateLimit
	else:
		rateData = TwitterFunctions.getTwitterRateLimitStatus()
		accountRateLimit = AccountRateLimit(rateData)
		print accountRateLimit
		

def getSearchResult(args):
	query = args[0]
	if query:
		data = TwitterFunctions.getSearchResults(query)
		resultPage = ResultPage(data)
		print str(resultPage)


def getUserInput(args):
	while True:
		quitCommand = raw_input('\nPress q enter to quit...\n')
		if quitCommand == 'q':
			sys.exit(1)	

def displayStatus(twitterFeed):
	logger.info('2 statuses length: '+ str(len(twitterFeed.statuses)))
	logger.info('2 statusesDict length: '+ str(len(twitterFeed.statusesDict)))
	twitterFeed.statuses.sort(Utils.compareStatus)
	logger.info('3 statuses length: '+ str(len(twitterFeed.statuses)))
	logger.info('3 statusesDict length: '+ str(len(twitterFeed.statusesDict)))
	while twitterFeed.statuses:
			print str(twitterFeed.statuses.pop(0))
	logger.info('Loop ending!')
			

def keypress(event):
	if event.keysym == 'Escape':
		sys.exit(1)


def main():
	parser =OptionParser()
	parser.add_option('--user', action='store_true', help='track user feed mode', dest='user')
	parser.add_option('--friend', action='store_true', help='track friend feed mode',  dest='friend')
	parser.add_option('--accountratelimit' , action='store_true', help='find out rate limit of machine')
	parser.add_option('--search', action='store_true', help='search for particular term')
	parser.add_option('-s', dest='screen_name', help='screen name of twitter user')
	parser.add_option('-p', dest='password', help='password of twitter user')
	parser.add_option('-q', dest='query', help='query')
	(options, arg)= parser.parse_args() 
	if options.user:
		thread = Runner(trackUserFeed, options.screen_name)
	elif options.friend:
		thread = Runner(trackFriendFeed, options.screen_name, options.password)
	elif options.accountratelimit:
		thread = Runner(getAccountRateLimit, options.screen_name, options.password)
	elif options.search:
		thread = Runner(getSearchResult, options.query)
	else:
		print 'No such option'
	thread.start()
	readUserInputThread = Runner(getUserInput)
	readUserInputThread.start()
	thread.event.wait()
		
	#root = tk.Tk()
	#root.bind_all('<Key>', keypress)
	#root.withdraw()
	#root.mainloop()
	


if __name__=="__main__":
	main()	
