#-*-coding:UTF-8-*-
'''
Created on 2012-12-10

@author: jixianwu
'''
from weibo import APIClient,APIError
import urllib,httplib
import operator
from wordSegmentation import tokenizer

class AppClient(object):
    ''' initialize a app client '''
    def __init__(self,*aTuple):
        self._appKey = aTuple[0] #your app key
        self._appSecret = aTuple[1] #your app secret
        self._callbackUrl = aTuple[2] #your callback url
        self._account = aTuple[3] #your weibo user name (eg.email)
        self._password = aTuple[4] # your weibo pwd
        self.AppCli = APIClient(app_key=self._appKey,app_secret=self._appSecret,redirect_uri=self._callbackUrl)
        self._author_url = self.AppCli.get_authorize_url()
        self._getAuthorization()
    
    def __str__(self):
        return 'your app client is created with callback %s' %(self._callbackUrl)
    
    def _get_code(self):
        conn = httplib.HTTPSConnection('api.weibo.com')
        postdict = {"client_id": self._appKey,
             "redirect_uri": self._callbackUrl,
             "userId": self._account,
             "passwd": self._password,
             "isLoginSina": "0",
             "action": "submit",
             "response_type": "code",
             }
        postdata = urllib.urlencode(postdict)
        conn.request('POST', '/oauth2/authorize', postdata, {'Referer':self._author_url,'Content-Type': 'application/x-www-form-urlencoded'})
        res = conn.getresponse()
        location = res.getheader('location')
        code = location.split('=')[1]
        conn.close()
        return code
    
    def _getAuthorization(self):
        ''' get the authorization from sinaAPI with oauth2 authentication method '''
        code = self._get_code()
        r = self.AppCli.request_access_token(code)
        access_token = r.access_token # The token return by sina
        expires_in = r.expires_in
        self.AppCli.set_access_token(access_token, expires_in)
    
    def getCurrentUid(self):
        ''' get the current authorized user id'''
        try:
            uid = self.AppCli.account.get_uid.get()['uid']
            #print uid
            return uid
        except Exception:
            print 'get userid failed'
            return
    
    def getFocus(self,userid):
        ''' get focused users list by current user '''
        focus = self.AppCli.friendships.friends.ids.get(uid=userid)
        try:
            return focus.get('ids')
        except Exception:
            print 'get focus failed'
            return
    
    def getTags(self,userid):
        ''' get last three tags stored by weight of this user'''
        try:
            tags = self.AppCli.tags.get(uid=userid)
        except Exception:
            print 'get tags failed'
            return
        userTags = []
        sortedT = sorted(tags,key=operator.attrgetter('weight'),reverse=True)
        if len(sortedT) > 3:
            sortedT = sortedT[-3:]
        for tag in sortedT:
            for item in tag:
                if item != 'weight':
                    userTags.append(tag[item])
        return userTags
    
    def getRecommendedUsers(self,userid):
        recommendUsers={}
        tkr = tokenizer()
        lstrwords = ''
        userTags = self.getTags(userid)
        #print len(userTags)
        userFocus = self.getFocus(userid)
        #print len(userFocus)
        
        #concatenate all the tags of the user into a string ,then segment the string
        for tag in userTags:
            utf8_tag = tag.encode('utf-8')
            #print utf8_tag
            lstrwords += utf8_tag
        words = tkr.parse(lstrwords)
        
        for keyword in words:
            #print keyword
            searchUsers = self.AppCli.search.suggestions.users.get(q=keyword.decode('utf-8'))
            
            #recommendation the top ten users
            if len(searchUsers) >10:
                searchUsers = searchUsers[-10:]
                
            for se_user in searchUsers:
                #print se_user
                uid = se_user['uid']
                #filter those had been focused by the current user
                if uid not in userFocus:
                    recommendUsers[uid] = se_user['screen_name'].encode('utf-8')
        return recommendUsers
    
    def collectPublicTags(self):
	''' don't call this function if you have no plan to update the userdict.txt(only for words segmentation)'''
        tagSet = set()
        userID = self.getCurrentUid()
        print userID
        currentUserTags = self.AppCli.tags.get(uid=userID)
        iterator_Users = self.getFocus(userID)
        #print iterator_Users
        #iterator_Users = ['2654042367','1695711143','2655842855','2655822735','2734016824','2629033945','2169393374','2618489905','2632987730','2632001903','2550228443','2550239427','1659922801','2632017781','1649154715']
        iterator_Users.append(userID)
        for user in iterator_Users:
            try:
                userTags = self.AppCli.tags.get(uid=user)
            except APIError:
                print 'userid:%s' %(user)
                continue
            for tag in userTags:
                try:
                    for item in tag:
                        if item != 'weight':
                            tagSet.add(tag[item])
                    #theTag = tag.itervalues().next()
                    #tagSet.add(theTag)
                except Exception:
                    print 'get the tags failed'
                    continue
        
        user_Dictionary_File = 'userdict.txt'
        udf = open(user_Dictionary_File,'a+')
        for tag in tagSet:
            print tag
            #utf8_tag = tag.encode('utf-8')
            udf.write(str(tag)+'\n')
        udf.close()        

if __name__ == '__main__':
    appTuple = ('your app key','your app secret','your call back url',\
                'your sina weibo account','your weibo password') #note:you can applicate some test accounts
    AppClient = AppClient(*appTuple)
    
    #if you want to update userdict.txt, you only remove the annotation of below code
    #AppClient.collectPublicTags()

    #give the userid,of course,you can give yourself id to getting recommmendation users; in partice,this userID should be the user using this app
    userID = '1823788613'#AppClient.getCurrentUid()
    recommUsersDict = AppClient.getRecommendedUsers(userID)
    #print recommUsersDict
    for uid,sname in recommUsersDict.items():
        print sname.decode('utf-8').encode('gbk')
    


    

        
         
        
    
    
    
                