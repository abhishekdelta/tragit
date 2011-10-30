#!/usr/bin/env python
# Package: Tragit
# Author: Abhishek Shrivastava <i.abhi27[at]gmail[dot]com>.
# License: BSD License
# TODO: Add optionsparser. Specify username password via options parser and auto create setup file. Override configs via optionsparser.

import sys
import github
import csv
import ConfigParser

class Tragit:

    def __init__(self, trac_csv, project): 
        self._traccsv = trac_csv
        self._project = project
        self._config = ConfigParser.ConfigParser()
        self._config.read('tragit.conf')
        self._config_sanity_check()
        self._username = self._config.get('github','username')
        self._password = self._config.get('github','password')
        self._defaultcolor = self._config.get('github','defaultcolor').lstrip('#')
        self._project = self._config.get('github','project')
        self._defaultassignee = self._config.get('github','defaultassignee')
        self._projectinorg = self._config.get('github','projectinorg')
        self._orgname = self._config.get('github','orgname')
        if self._projectinorg == 'true':
            self._projectsource = self._orgname
        else:
            self._projectsource = self._username
            
        self._conf_map = {}
        for conf_item in dict(self._config.items('issue')).keys():
            self._conf_map[conf_item] = self._config.get('issue',conf_item)
            
        self._github = github.Github(self._username, self._password, self._project, self._projectsource)
        
        print "Github API successfully loaded!"  
            
    def _config_sanity_check(self):
        if not self._config:
            sys.exit("Config file could not be loaded.")   
        
        sections = self._config.sections()
        for section in ['github','issue']:
            if section not in sections:
                sys.exit(section +" section undefined.")
            
        githubitems = dict(self._config.items('github'))
        for item in ['username','password','defaultcolor','project','projectinorg']:
            if item not in githubitems.keys():
                sys.exit(item +' is missing from github section.')                
                
            if githubitems[item] == "":
                sys.exit(item + ' has an empty value.')
        
        if 'defaultassignee' not in githubitems.keys() or githubitems['defaultassignee'] == "":
            print 'No default assignee specified.'
            print 'Tragit will assign tickets to you in Github, if the actual owner could not be found. Is it ok ?'
            go = sys.stdin.readline().strip().lower()
            if go[0:1] != 'y':
                sys.exit('Give some username as the default assignee and try again.')
            self._config.set('github','defaultassignee',self._config.get('github','username'))
        
        projectinorg = githubitems['projectinorg'].lower()
        if projectinorg not in ['true','false']:
            sys.exit('Invalid entry in projectinorg setting. Should be either true or false.')
        
        if projectinorg == 'true' and ('orgname' not in githubitems.keys() or githubitems['orgname'] == ""):
            sys.exit('orgname setting is empty or undefined. Since projectinorg is true, a valid organization name must be specified.')
        
        githubitems = dict(self._config.items('issue'))
        for item in ['title','body','assignee','state','milestone','labels']:
            if item not in githubitems.keys():
                if item == 'title':
                    sys.exit(item +' is missing from issue section.')
                else:
                    print 'No Trac equivalent to ' + item + ' specified.'
                    print 'Tragit will simply leave it blank in all issues. Continue ?'
                    go = sys.stdin.readline().strip().lower()
                    if go[0:1] != 'y':
                        sys.exit('Add some Trac column equivalent to ' + item + ' and try again.')
                    
            if githubitems[item] == "":
                if item == 'title':
                    sys.exit(item + ' has an empty value.')
                elif item == 'labels':
                    print 'No labels specified.'
                    print 'Tragit will simply ticket ignore priorities, severities, components and types if they exist. Continue ?'
                    go = sys.stdin.readline().strip().lower()
                    if go[0:1] != 'y':
                        sys.exit("Add some labels and try again.")
                else:
                    print 'The Trac equivalent to ' + item + ' has no values.'
                    print 'Tragit will simply leave it blank in all issues. Continue ?'
                    go = sys.stdin.readline().strip().lower()
                    if go[0:1] != 'y':
                        sys.exit('Add some Trac column equivalent to ' + item + ' and try again.')
      
        if githubitems['labels'] != '':
            labels = githubitems['labels'].split(',')
            labels = map(lambda x: x.strip(), labels)
            for label in labels:
                if label not in sections or len(self._config.items(label)) == 0:
                    print label+' is specified in labels but has no section or has empty section. You might want to add some colors to it.'
                    print 'Otherwise, Tragit will use default color for all '+label+'. Continue ?'
                    go = sys.stdin.readline().strip().lower()
                    if go[0:1] != 'y':
                        sys.exit("Create the section and add some entries with colors in in and try again.")
                            
    
    def transfer(self):
        csvfile = open(self._traccsv,'rb')
        csvreader = csv.DictReader(csvfile)
        counter = 0
        for row in csvreader:
            counter += 1
            for key in row.keys():
                row[key] = row[key].decode('utf-8')
            
            for field in self._conf_map.keys():
                if field == 'labels':
                    continue
                if self._conf_map[field] not in row.keys():
                    row[field] = None
                    
            self._process_ticket(row)
        
        print "Done! Transferred "+str(counter)+" trac tickets to Github issues."

    def _process_labels(self, ticket):
        conf_labels_cat = self._config.get('issue','labels')
        if not conf_labels_cat:
            return None

        conf_sections = self._config.sections()    
        conf_labels_cat = map(lambda x: x.strip(), conf_labels_cat.split(','))
        ticket_labels = []
        for cat in conf_labels_cat:
            if cat in ticket.keys():
                label = ticket[cat]
                ticket_labels.append(label)
                labels = self._github.get_labels()
                if labels == False:
                    sys.exit("Cannot fetch existing labels because something went wrong with Github API.")
                    
                if label not in labels:
                    if cat in conf_sections and label in dict(self._config.items(cat)).keys():
                        color = self._config.get(cat,label).lstrip('#')
                    else:
                        color = self._defaultcolor
                    
                    resp = self._github.create_label(label,color)
                    if resp == False:
                        sys.exit(label+" label cannot be created because something went wrong with Github API.")
         
        return ticket_labels

    def _process_milestone(self, ticket):
        if not ticket[self._conf_map['milestone']]:
            return None
        
        milestone = ticket[self._conf_map['milestone']]
        milestonesmap = self._github.get_milestones()
        if milestonesmap == False:
            sys.exit("Cannot fetch existing milestones because something went wrong with Github API.")
            
        if milestone not in milestonesmap.keys():
            m_id = self._github.create_milestone(milestone)
            if m_id == False:
                sys.exit(milestone+" milestone cannot be created because something went wrong with Github API.")
            
            return m_id
        
        return milestonesmap[milestone]
    
    def _process_ticket(self, ticket):
        columns = ticket.keys()
        issue_labels = self._process_labels(ticket)
        milestone_id = self._process_milestone(ticket)
        issue_id = self._github.create_issue(ticket[self._conf_map['title']], ticket[self._conf_map['body']], 
                                             ticket[self._conf_map['assignee']], milestone_id, issue_labels)
        if issue_id == False:
            sys.exit(ticket[self._conf_map['title']]+" issue cannot be created because something went wrong with Github API.")
                
        if ticket[self._conf_map['state']] == 'closed':
            resp = self._github.close_issue(issue_id)
            if resp == False:
                sys.exit(issue_id+" number issue cannot be closed because something went wrong with Github API.")
        
        print "Created Github Issue #"+str(issue_id)+" from Trac Ticket "+ticket[self._conf_map['title']]        
        
if __name__ == "__main__":
    tragit = Tragit("/home/jereme/Desktop/testcsv.csv")
    tragit.transfer()


