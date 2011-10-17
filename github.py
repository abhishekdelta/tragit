#!/usr/bin/env python
# Package: Tragit
# Author: Abhishek Shrivastava <i.abhi27[at]gmail[dot]com>.
# License: BSD License
# TODO: NEED TO FIND A WAY TO ACCESS GITHUB VIA API TOKEN WITHOUT PASSWORD
#   GITHUBLOGIN = os.popen('git config --global github.user').read().strip()
#   GITHUBTOKEN = os.popen('git config --global github.token').read().strip()
# TODO: NEED TO ALLOW FOR COMMENTS IMPORT TOO

import os,sys
import base64
from httplib import HTTPSConnection
from json import JSONDecoder, JSONEncoder

GITHUBAPI = 'api.github.com'

class Github(object):

    def __init__(self, username, password, project):
        self._username = username
        self._password = password
        self._project = project
        self.labels = []
        self.milestones = {}
        
                
    def get_milestones(self):
        if not self.milestones:
            x = GithubRequest(self._username, self._password)
            data = x.request('GET','/repos/%s/%s/milestones?state=open' % (self._username, self._project))
            self.milestones = dict([(y['title'], y['number']) for y in data])
            data = x.request('GET','/repos/%s/%s/milestones?state=closed' % (self._username, self._project))
            self.milestones.update(dict([(y['title'], y['number']) for y in data]))

        return self.milestones

    def create_milestone(self, ms_title, ms_desc = None, ms_dueon = None, ms_state = None):
        x = GithubRequest(self._username, self._password)
        milestone = {}
        milestone['title'] = ms_title    
        if ms_desc != None:
            milestone['description'] = ms_desc
        
        if ms_state != None:
            milestone['state'] = ms_state
        
        if ms_dueon != None:
            milestone['due_on'] = ms_dueon
        
        print "Creating milestone : "+str(milestone)
        data = x.request('POST','/repos/%s/%s/milestones' % (self._username, self._project), milestone)
        if 'title' in data and data['title'] == ms_title:
            self.milestones[ms_title] = data['number']
            return data['number']

        self._error(data)            
        return False

    def get_labels(self):
        if not self.labels:
            x = GithubRequest(self._username, self._password)
            data = x.request('GET','/repos/%s/%s/labels' % (self._username, self._project))
            self.labels = [x['name'] for x in data]
            
        return self.labels
        
    def create_label(self, lab_name, lab_color = '0000DD'):
        x = GithubRequest(self._username, self._password)
        label = {}
        label['name'] = lab_name
        label['color'] = lab_color
        print "Creating label : "+str(label)
        data = x.request('POST','/repos/%s/%s/labels' % (self._username, self._project), label)
        if 'name' in data and data['name'] == lab_name:
            self.labels.append(lab_name)
            return True

        self._error(data)
        return False

    def create_issue(self, iss_title, iss_body = None, iss_assignee = None, iss_milestone = None, iss_labels = None):
        x = GithubRequest(self._username, self._password)
        issue = {}
        issue['title'] = iss_title
        if iss_body != None:
            issue['description'] = iss_body
        
        if iss_assignee != None:
            issue['assignee'] = iss_assignee
        
        if iss_milestone != None and type(iss_milestone) == type(1):
            issue['milestone'] = iss_milestone
        
        if iss_labels != None and type(iss_labels) == type([]):
            issue['labels'] = iss_labels
        
        data = x.request('POST','/repos/%s/%s/issues' % (self._username, self._project), issue)
        if 'title' in data and data['title'] == iss_title:
            return data['number']
        
        self._error(data)        
        return False
     
    def close_issue(self, iss_id):
        x = GithubRequest(self._username, self._password)
        issue = {}
        issue['state'] = 'closed'
        data = x.request('PATCH','/repos/%s/%s/issues/%d' % (self._username, self._project, iss_id), issue)
        if 'state' in data and data['state'] == 'closed':
            return True
            
        self._error(data)        
        return False
    
    def _error(self, data):
        print "----------------ERROR--------------"
        print data
        print "----------------ERROR--------------"
      

class GithubRequest(object):
    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._create_connection()
        self._create_auth_header()
        self._decoder = JSONDecoder()
        self._encoder = JSONEncoder()

    def _create_auth_header(self):
        userpass = '%s:%s' % (self._username, self._password)
        authkey = base64.b64encode(userpass).replace('\n','')
        self._auth_header = {}
        self._auth_header['Authorization'] = 'Basic %s' % authkey

        
    def _create_connection(self):
        self._connection = HTTPSConnection(GITHUBAPI)
        self._connection.connect()

        
    def request(self, method, url, params = None):
        if params != None:
            jsondata = self._encoder.encode(params)
        else:
            jsondata = None
        
        self._connection.request(method,url,jsondata,self._auth_header)
        response = self._connection.getresponse()
        jsonresponse = response.read()
        textresponse = self._decoder.decode(jsonresponse)
        return textresponse
    
