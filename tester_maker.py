import requests
import csv
import sys
from itertools import product
from datetime import datetime
import tk_token


def fetch_json(server, session, *args):
    if args:
        url = f'{server}{"".join(args)}'
    else:
        url = server
    req = session.get(url)
    return req.json()

def list_maker(arr):
    return [x['id'] for x in  arr]


snapshot2Environment = "https://okapi-fivecolleges-sandbox.folio.ebsco.com"

    # tenant names
snapshot2Tenant = "fs00001006"

    # headers for use with forming API calls

snapshot2PostHeaders = {
        'Content-Type': 'application/json',
        'x-okapi-tenant': snapshot2Tenant,
        'x-okapi-token': tk_token.tk["token"]}

testServer = snapshot2Environment
postHeaders = snapshot2PostHeaders
snapshotToken = tk_token.tk["token"]


s = requests.Session()
s.headers = postHeaders

  # fetch patron groups
patronGroupsJson = fetch_json(testServer, s, '/groups?limit=1000')
patron_group_ids = list_maker(patronGroupsJson['usergroups'])
# fetch loan types
loanTypesJson = fetch_json(testServer, s, '/loan-types?limit=1000')
loan_type_ids = list_maker(loanTypesJson['loantypes'])
# fetch material types
materialTypesJson = fetch_json(testServer, s, '/material-types?limit=1000')

# fetch locations
locationsJson = fetch_json(testServer, s, '/locations?limit=1500')
locations_list_it = list_maker(locationsJson['locations'])
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


x = list(product(patron_group_ids,loan_type_ids, locations_list_it))
print(x, len(x))

