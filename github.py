#!/usr/bin/env python
# Package: Tragit
# Author: Abhishek Shrivastava <i.abhi27[at]gmail[dot]com>.
# License: BSD License
# TODO: NEED TO FIND A WAY TO ACCESS GITHUB VIA API TOKEN WITHOUT PASSWORD
# TODO: NEED TO ALLOW FOR COMMENTS IMPORT TOO

import os,sys
import base64
from httplib import HTTPSConnection
from json import JSONDecoder, JSONEncoder
import ConfigParser

config = ConfigParser.ConfigParser()
config.read('tragit.conf')
GITHUBLOGIN = config.get('github','USERNAME')
GITHUBPASSWORD = config.get('github','PASSWORD')
#GITHUBLOGIN = os.popen('git config --global github.user').read().strip()
#GITHUBTOKEN = os.popen('git config --global github.token').read().strip()
GITHUBAPI = 'api.github.com'

class GithubRequest(object):
    def __init__(self):
        self._create_connection()
        self._create_auth_header()
        self._decoder = JSONDecoder()
        self._encoder = JSONEncoder()


    def _create_auth_header(self):
        userpass = '%s:%s' % (GITHUBLOGIN, GITHUBPASSWORD)
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
    

def get_milestones(project):
    x = GithubRequest()
    data = x.request('GET','/repos/%s/%s/milestones' % (GITHUBLOGIN, project))
    return [(x['number'], x['title']) for x in data]

def create_milestone(project, ms_title, ms_desc = None, ms_dueon = None, ms_state = None):
    x = GithubRequest()
    milestone = {}
    milestone['title'] = ms_title
    
    if ms_desc != None:
        milestone['description'] = ms_desc
    
    if ms_state != None:
        milestone['state'] = ms_state
    
    if ms_dueon != None:
        milestone['due_on'] = ms_dueon
        
    data = x.request('POST','/repos/%s/%s/milestones' % (GITHUBLOGIN, project), milestone)
    
    if data['title'] and data['title'] == ms_title:
        return data['number']
        
    return False

def get_labels(project):
    x = GithubRequest()
    data = x.request('GET','/repos/%s/%s/labels' % (GITHUBLOGIN, project))
    return [x['name'] for x in data]

def create_label(project, lab_name, lab_color = '0000DD'):
    x = GithubRequest()
    label = {}
    label['name'] = lab_name
    label['color'] = lab_color
    data = x.request('POST','/repos/%s/%s/labels' % (GITHUBLOGIN, project), label)
    if data['name'] and data['name'] == lab_name:
        return True
    
    return False

def create_issue(project, iss_title, iss_body = None, iss_assignee = None, iss_milestone = None, iss_labels = None):
    x = GithubRequest()
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
    
    data = x.request('POST','/repos/%s/%s/issues' % (GITHUBLOGIN, project), issue)
    print data
    if data['title'] and data['title'] == iss_title:
        return data['number']
        
    return False
 
def close_issue(project, iss_id):
    x = GithubRequest()
    issue = {}
    issue['state'] = 'closed'
    data = x.request('PATCH','/repos/%s/%s/issues/%d' % (GITHUBLOGIN, project, iss_id), issue)
    if data['title'] and data['state'] == 'closed':
        return True
    
    return False
