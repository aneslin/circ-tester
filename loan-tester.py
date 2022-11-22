# This is a very basic tool to allow you to provide FOLIO with a CSV file of settings UUIDs
# which FOLIO then sends back and tells you what circulation policies would be applied.
##
# It should function in FOLIO for the Lotus release and later - in Kiwi, there is a permission
# issue that prevents the overdue and lost item policies from being retrieved.
##
# Your input file should be in CSV format like so:
##
# patron_type_id,loan_type_id,item_type_id,location_id
# patrontypeUUID,loantypeUUID,itemtypeUUID,locationUUID
# ...
# ...
# ...
##
# "item_type" in this script is referring to what appears as "material type" in the UI - the API calls it
# item type, I think that is tech debt from very early project decisions.
##
# You must run this as a user who has the following specific permissions:
##
# circulation.rules.loan-policy.get
# circulation.rules.overdue-fine-policy.get
# circulation.rules.lost-item-policy.get
# circulation.rules.request-policy.get
# circulation.rules.notice-policy.get
##
# These permissions are hidden by default, so you will need administrator access to assign these permissions to a user.

from ast import arg
import requests
import csv
import sys
from time import perf_counter
from datetime import datetime
import tk_token


def fetch_json(server, session, *args):
    
    if args:
        url = f'{server}{"".join(args)}'
        
    else:
        url = server
        
    req = session.get(url)
    
    return req.json()


def make_friendly(id, json_list, key):
    for i in json_list:
        if i['id'] == id:
            return i[key]


def loc_dict_maker(loc_array):
    output = {}
    for i in loc_array:
        output[i['id']] = {'code': i['code'], 'libloc': i['libraryId']}
    return output


def makeUrl(base_url, endpoint, loan_type, item_type, patron_type, location_type):
    return f"{base_url}{endpoint}loan_type_id={loan_type}&item_type_id={item_type}&patron_type_id={patron_type}&location_id={location_type}"


def main():
    # Set up variables for use in the script
    # If you are repurposing this for another institution, you'll want to add the
    # appropriate okapi URLs, tenant names, tokens, etc. and make sure
    # that the appropriate points throughout the script have your variables.

    # okapi environments that can be used
    snapshotEnvironment = "https://folio-snapshot-okapi.dev.folio.org"
    snapshot2Environment = "https://okapi-fivecolleges.folio.ebsco.com"

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

    # Now you can start asking for input from the person running the script
    # They need to specify the name of the server they want to test on
    ##
    # Again, if you are tweaking for another environment, you need to make appropriate
    # updates here.

    environment = input(
        "What server do you want to test on? (snapshot, snapshot2)  ")

    if environment == 'snapshot':
        testServer = snapshotEnvironment
        postHeaders = snapshotPostHeaders
        snapshotToken = input("provide the token for snapshot ")
    elif environment == 'snapshot2':
        testServer = snapshot2Environment
        postHeaders = snapshot2PostHeaders
        snapshotToken = tk_token.tk["token"]

    # Print start time for script -

    # fetch settings files to query in the script; makes things faster

    s = requests.Session()
    s.headers = postHeaders

    # fetch patron groups
    patronGroupsJson = fetch_json(testServer, s, '/groups?limit=1000')

    # fetch loan types
    loanTypesJson = fetch_json(testServer, s, '/loan-types?limit=1000')

    # fetch material types
    materialTypesJson = fetch_json(testServer, s, '/material-types?limit=1000')

    # fetch locations
    locationsJson = fetch_json(testServer, s, '/locations?limit=1500')
    locdict = loc_dict_maker(locationsJson['locations'])
    # fetch loan policies
    loanPoliciesJson = fetch_json(
        testServer, s, '/loan-policy-storage/loan-policies?limit=500')

    # fetch notice policies
    noticePoliciesJson = fetch_json(
        testServer, s, '/patron-notice-policy-storage/patron-notice-policies?limit=100')

    # fetch request policies
    requestPoliciesJson = fetch_json(
        testServer, s, '/request-policy-storage/request-policies?limit=50')

    # fetch overdue policies
    overduePoliciesJson = fetch_json(
        testServer, s, '/overdue-fines-policies?limit=100')

    # fetch lost item policies
    lostItemPoliciesJson = fetch_json(
        testServer, s, '/lost-item-fees-policies?limit=100')

    # fetch libraries
    librariesJson = fetch_json(
        testServer, s, '/location-units/libraries?limit=100')

    # open the file with test information - assumes name of file is loan_tester.csv but that's easy to change
    #
    # encoding = 'utf-8-sig' tells Python to compensate for Excel encoding
    # first row should have four values - patron_type_id,	item_type_id,	loan_type_id,	location_id
    # then you put in the values for each loan scenario as a row in the file
    #
    # values are specified in UUIDs, but output will be in friendly name.
    # the API calls the material type id the "item type id" - tech debt artifact from early FOLIO, I think

    initialFile = open('loan_tester2.csv', newline='', encoding='utf-8')

    # create a python dictionary to store the results with friendly names that you want to put into a file
    
    final_output = []
    # turn your file of patron/loan/material type/location into python dictionary that can be
    # used to query the APIs

    testLoanScenarios = csv.DictReader(initialFile)
    pftime = perf_counter()
    startTime = datetime.now()
    count=0
    for count, row in enumerate(testLoanScenarios):
        friendlyResults = {}
        # provides a simple counter and output to know the script is still running
        print(count, row)

        # first thing is to pull the UUIDs; you'll need these to look up the friendly names, and to
        # correctly form the API call to see what policy comes back
        
        patron_type_id, loan_type_id, item_type_id, location_id = row[
            "patron_type_id"], row["loan_type_id"],  row["item_type_id"], row["location_id"]

        # pull patron_type_id friendly name
        friendlyResults['patron_group'] = make_friendly(
                patron_type_id, patronGroupsJson['usergroups'], 'group')
        if 'patron_group' not in friendlyResults:
                friendlyResults['patron_group'] = "Patron group not found"

            # pull loan type friendly name
        friendlyResults['loan_type'] = make_friendly(
                loan_type_id, loanTypesJson['loantypes'], 'name')
        if 'loan_type' not in friendlyResults:
                friendlyResults['loan_type'] = "Loan type not found"

        # pull material type friendly name (API refers to it as item_type_id)

        friendlyResults['material_type'] = make_friendly(
            item_type_id, materialTypesJson['mtypes'], 'name')
        if 'material_type' not in friendlyResults:
            friendlyResults['material_type'] = "Material type not found"

        # pull location friendly name - using location code since a lot of our location names have commas in them
        # which makes working with CSV a little too messy+df
        #
        # also pulling library friendly name so that it can be used in sorting/reviewing results in the
        # output file

        # lookup location id in locdict and return code and library Id

        friendlyResults['locations'] = locdict[location_id]["code"]
        libloc = locdict[location_id]['libloc']

        friendlyResults['libraryName'] = make_friendly(
            libloc, librariesJson['loclibs'], 'name')  # and pull the name

        if 'libraryName' not in friendlyResults:
            friendlyResults['libraryName'], friendlyResults['location'] = "Library not found", "Location not found"
        if 'locations' not in friendlyResults:
            friendlyResults['locations'] = "Location not found"

        # now, you'll use the UUID values to query the APIs, get the results back, and then form
        # the full row in friendlyResults with the friendly names

        # first, let's make the URLs

        urlLoanPolicy = makeUrl(testServer, '/circulation/rules/loan-policy?',
                                loan_type_id, item_type_id, patron_type_id, location_id)
        urlRequestPolicy = makeUrl(testServer, '/circulation/rules/request-policy?',
                                   loan_type_id,  item_type_id, patron_type_id, location_id)
        urlNoticePolicy = makeUrl(testServer,  '/circulation/rules/notice-policy?',
                                  loan_type_id,  item_type_id,  patron_type_id, location_id)
        urlOverduePolicy = makeUrl(testServer, '/circulation/rules/overdue-fine-policy?',
                                   loan_type_id, item_type_id,  patron_type_id, location_id)
        urlLostItemPolicy = makeUrl(testServer, '/circulation/rules/lost-item-policy?',
                                    loan_type_id,  item_type_id, patron_type_id, location_id)

        # now, check all of the policies.
        #
        # you could make one giant loop for this, but I found that it seemed like I got a bit of a performance improvement by
        # doing individual loops through the smaller chunks of data / discrete sections
        
        postLoanPoliciesJson = fetch_json(urlLoanPolicy, s)
        
        friendlyResults['loanPolicy'] = make_friendly(
            postLoanPoliciesJson['loanPolicyId'], loanPoliciesJson['loanPolicies'], 'name')

        postRequestPoliciesJson = fetch_json(urlRequestPolicy, s)
        friendlyResults['requestPolicy'] = make_friendly(
        postRequestPoliciesJson['requestPolicyId'], requestPoliciesJson['requestPolicies'], 'name')

        postNoticePoliciesJson = fetch_json(urlNoticePolicy, s)
        friendlyResults['noticePolicy'] = make_friendly(
        postNoticePoliciesJson['noticePolicyId'], noticePoliciesJson['patronNoticePolicies'], 'name')

        postOverduePoliciesJson = fetch_json(urlOverduePolicy, s)
        friendlyResults['overduePolicy'] = make_friendly(
        postOverduePoliciesJson['overdueFinePolicyId'], overduePoliciesJson['overdueFinePolicies'], 'name')

        postLostItemPoliciesJson = fetch_json(urlLostItemPolicy, s)
        friendlyResults['lostItemPolicy'] = make_friendly(
        postLostItemPoliciesJson['lostItemPolicyId'], lostItemPoliciesJson['lostItemFeePolicies'], 'name')

        print(friendlyResults)
        final_output.append(friendlyResults)
        

  

    with open("friendlyOutput-%s.csv" % startTime.strftime("%d-%m-%Y-%H%M%S"), 'w', newline='') as output_file:
        headers = ['loan_type', 'patron_group',  'libraryName','locations', 'material_type', 'loanPolicy',  'overduePolicy','noticePolicy','lostItemPolicy','requestPolicy'     ]
        writer = csv.DictWriter(output_file, fieldnames=list(headers))
        writer.writeheader()
        for row in final_output:
            writer.writerow(row)

    # when the tester is finally done, give some basic time information so you
    # know how long it took

    # close the initial file of scenarios
    initialFile.close()
    etime = perf_counter()
    print(f"{count+1} records processed in {etime - pftime:0.4f} seconds")


if __name__ == "__main__":
    main()
