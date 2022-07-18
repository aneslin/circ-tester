## This is a very basic tool to allow you to provide FOLIO with a CSV file of settings UUIDs 
## which FOLIO then sends back and tells you what circulation policies would be applied. 
##
## It should function in FOLIO for the Lotus release and later - in Kiwi, there is a permission
## issue that prevents the overdue and lost item policies from being retrieved.
##
## Your input file should be in CSV format like so:
##
## patron_type_id,loan_type_id,item_type_id,location_id
## patrontypeUUID,loantypeUUID,itemtypeUUID,locationUUID
## ...
## ...
## ...
##
## "item_type" in this script is referring to what appears as "material type" in the UI - the API calls it
## item type, I think that is tech debt from very early project decisions.
##
## You must run this as a user who has the following specific permissions:
##
## circulation.rules.loan-policy.get
## circulation.rules.overdue-fine-policy.get
## circulation.rules.lost-item-policy.get
## circulation.rules.request-policy.get
## circulation.rules.notice-policy.get
##
## These permissions are hidden by default, so you will need administrator access to assign these permissions to a user.

import requests
import csv
import sys
from functools import lru_cache
from datetime import datetime
import tk_token


def fetch_json(server, session, *args ):
    if args:
        url = f'{server}{"".join(args)}'
    else:
        url=server
    req = session.get(url)
    return req.json()


def make_friendly(id, json_list, key):
    for i in json_list:
        if i['id'] == id:
            return i[key]



def main():
    ## Set up variables for use in the script
    ## If you are repurposing this for another institution, you'll want to add the 
    ## appropriate okapi URLs, tenant names, tokens, etc. and make sure
    ## that the appropriate points throughout the script have your variables.

    # okapi environments that can be used
    snapshotEnvironment = "https://folio-snapshot-okapi.dev.folio.org"
    snapshot2Environment = "https://okapi-fivecolleges-sandbox.folio.ebsco.com"

    # tenant names
    snapshotTenant = "diku"
    snapshot2Tenant = "fs00001006"

    # headers for use with forming API calls

    snapshotPostHeaders = {
    'x-okapi-tenant': snapshotTenant,
    'x-okapi-token': "snapshotToken",
    'Content-Type': 'application/json'
}
    snapshot2PostHeaders = {
    'Content-Type': 'application/json',
    'x-okapi-tenant': snapshot2Tenant,
    'x-okapi-token': tk_token.tk["token"]
    }

    ## Now you can start asking for input from the person running the script
    ## They need to specify the name of the server they want to test on
    ##
    ## Again, if you are tweaking for another environment, you need to make appropriate
    ## updates here.

    environment = input("What server do you want to test on? (snapshot, snapshot2)  ")

    if environment == 'snapshot':
        testServer = snapshotEnvironment
        postHeaders = snapshotPostHeaders
        snapshotToken = input("provide the token for snapshot ")
    elif environment == 'snapshot2':
        testServer = snapshot2Environment
        postHeaders = snapshot2PostHeaders
        snapshotToken = tk_token.tk["token"]
    

    # Print start time for script - 
    startTime = datetime.now()
    print("Script starting at: %s" % startTime)

    # fetch settings files to query in the script; makes things faster

    s = requests.Session()
    s.headers= postHeaders

    # fetch patron groups
    patronGroupsJson = fetch_json(testServer,s,'/groups?limit=1000')

    # fetch loan types
    loanTypesJson = fetch_json(testServer,s,'/loan-types?limit=1000')

    # fetch material types
    materialTypesJson = fetch_json(testServer,s,'/material-types?limit=1000')

    # fetch locations
    locationsJson = fetch_json(testServer,s,'/locations?limit=1500')

    # fetch loan policies
    loanPoliciesJson = fetch_json(testServer,s, '/loan-policy-storage/loan-policies?limit=500')

    # fetch notice policies
    noticePoliciesJson = fetch_json(testServer, s,'/patron-notice-policy-storage/patron-notice-policies?limit=100')

    # fetch request policies
    requestPoliciesJson = fetch_json(testServer, s,'/request-policy-storage/request-policies?limit=50')

    # fetch overdue policies
    overduePoliciesJson = fetch_json(testServer,s, '/overdue-fines-policies?limit=100')

    # fetch lost item policies
    lostItemPoliciesJson = fetch_json(testServer,s,'/lost-item-fees-policies?limit=100')
    #fetch libraries
    librariesJson = fetch_json(testServer,s,'/location-units/libraries?limit=100')


    # open the file with test information - assumes name of file is loan_tester.csv but that's easy to change
    # 
    # encoding = 'utf-8-sig' tells Python to compensate for Excel encoding
    # first row should have four values - patron_type_id,	item_type_id,	loan_type_id,	location_id
    # then you put in the values for each loan scenario as a row in the file
    #
    # values are specified in UUIDs, but output will be in friendly name.
    # the API calls the material type id the "item type id" - tech debt artifact from early FOLIO, I think

    initialFile = open('loan_tester.csv', newline='', encoding='utf-8-sig')

    # create a python dictionary to store the results with friendly names that you want to put into a file
    friendlyResults = {}

    # turn your file of patron/loan/material type/location into python dictionary that can be
    # used to query the APIs

    testLoanScenarios = csv.DictReader(initialFile, dialect='excel')




    for count, row in enumerate(testLoanScenarios):
        # provides a simple counter and output to know the script is still running
        print(count, row)
    
        # first thing is to pull the UUIDs; you'll need these to look up the friendly names, and to
        # correctly form the API call to see what policy comes back
        patron_type_id, loan_type_id, item_type_id, location_id = row["patron_type_id"], row["loan_type_id"],  row["item_type_id"], row["location_id"]

        # pull patron_type_id friendly name
        #for i in patronGroupsJson['usergroups']:
        # if i['id'] == patron_type_id:
            # friendlyResults['patron_group'] = i['group']

        friendlyResults['patron_group'] = make_friendly(patron_type_id, patronGroupsJson['usergroups'], 'group')
        if not 'patron_group' in friendlyResults:
            friendlyResults['patron_group'] = "Patron group not found"


        # pull loan type friendly name
        #for i in loanTypesJson['loantypes']:
        #    if i['id'] == loan_type_id:
        friendlyResults['loan_type'] = make_friendly(loan_type_id,loanTypesJson['loantypes'], 'name' )
        if not 'loan_type' in friendlyResults:
            friendlyResults['loan_type'] = "Loan type not found"
    

        # pull material type friendly name (API refers to it as item_type_id) 
        #for i in materialTypesJson['mtypes']:
            #if i['id'] == item_type_id:
        friendlyResults['material_type'] = make_friendly(item_type_id,materialTypesJson['mtypes'],'name')
        if not 'material_type' in friendlyResults:
            friendlyResults['material_type'] = "Material type not found"

        # pull location friendly name - using location code since a lot of our location names have commas in them
        # which makes working with CSV a little too messy
        #
        # also pulling library friendly name so that it can be used in sorting/reviewing results in the
        # output file
        for i in locationsJson['locations']:
            if i['id'] == location_id: # once you find the location ....
                for j in librariesJson['loclibs']: # use the location to search your stored copy of the libraries Json
                    if i['libraryId'] == j['id']: # to find the associated library
                        friendlyResults['library_name'] = j['name'] # and pull the name
                friendlyResults['location'] = i['code'] # finally, add the location code so that it shows up in that order in the output file.
        if not 'library_name' in friendlyResults:
            friendlyResults['libraryName'], friendlyResults['location'] = "Library not found", "Location not found"
        if not 'location' in friendlyResults:
            friendlyResults['location'] = "Location not found"


        # now, you'll use the UUID values to query the APIs, get the results back, and then form
        # the full row in friendlyResults with the friendly names
    
        # first, let's make the URLs
    
        urlLoanPolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/loan-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
        urlRequestPolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/request-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
        urlNoticePolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/notice-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
        urlOverduePolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/overdue-fine-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)
        urlLostItemPolicy = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/lost-item-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)

        # now, check all of the policies.
        # 
        # you could make one giant loop for this, but I found that it seemed like I got a bit of a performance improvement by 
        # doing individual loops through the smaller chunks of data / discrete sections

        postLoanPoliciesJson = fetch_json(urlLoanPolicy,s)
        for i in loanPoliciesJson['loanPolicies']:
            if i['id'] == postLoanPoliciesJson['loanPolicyId']:
                friendlyResults['loanPolicy'] = i['name']
    


        postRequestPoliciesJson = fetch_json(urlRequestPolicy, s)
        for i in requestPoliciesJson['requestPolicies']:
            if i['id'] == postRequestPoliciesJson['requestPolicyId']:
                friendlyResults['requestPolicy'] = i['name']
            
    
        postNoticePoliciesJson = fetch_json(urlNoticePolicy,s)
        for i in noticePoliciesJson['patronNoticePolicies']:
            if i['id'] == postNoticePoliciesJson['noticePolicyId']:
                friendlyResults['noticePolicy'] = i['name']
            
    
        postOverduePoliciesJson =fetch_json(urlOverduePolicy, s)
        for i in overduePoliciesJson['overdueFinePolicies']:
            if i['id'] == postOverduePoliciesJson['overdueFinePolicyId']:
                friendlyResults['overduePolicy'] = i['name']
            
        postLostItemPoliciesJson = fetch_json(urlLostItemPolicy,s)
        for i in lostItemPoliciesJson['lostItemFeePolicies']:
            if i['id'] == postLostItemPoliciesJson['lostItemPolicyId']:
                friendlyResults['lostItemPolicy'] = i['name']

        with open("friendlyOutput-%s.csv" % startTime.strftime("%d-%m-%Y-%H%M%S"), 'a', newline='') as output_file:
            test_file = csv.writer(output_file)
            test_file.writerow(friendlyResults.values())

    # when the tester is finally done, give some basic time information so you 
    # know how long it took        
        endTime = datetime.now()
        print("Script started at %s and ended at %s" % (startTime, endTime))

    # close the initial file of scenarios
    initialFile.close()


if __name__ == "__main__":
    main()