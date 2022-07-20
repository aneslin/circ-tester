import requests
import csv
import inquirer
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
    return [x['id'] for x in arr]


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
librariesJson = fetch_json(testServer, s, '/location-units/libraries?limit=32')
library_list = [(x['name'], x['id']) for x in librariesJson["loclibs"]]

# fetch patron groups
patronGroupsJson = fetch_json(testServer, s, '/groups?limit=1000')
#patron_group_ids = list_maker(patronGroupsJson['usergroups'])
# fetch locations
locationsJson = fetch_json(testServer, s, '/locations?limit=1500')
#loc_list = [(x['name'], x['id'])for x in locationsJson['locations'] if x['libraryId'] == "d7ec037d-a08e-4ef1-9d4b-bee6cb7edffa"]
# print(loc_list)


materialTypesJson = fetch_json(testServer, s, '/material-types?limit=1000')


q = [
    inquirer.List('chooseLibrary',
                  message="Select Library to use",
                  choices=library_list

                  )
]

answers = inquirer.prompt(q)
print(answers)
q2 = [
    inquirer.Checkbox('chooseLoc',
                      message="choose locations to use",
                      choices=[(x['name'], x['id'])for x in locationsJson['locations'] if x['libraryId'] == answers['chooseLibrary']]),

    inquirer.List('chooseGroup',
                  message='Choose Patron Group',
                  choices=[(x['group'], x['id']) for x in patronGroupsJson['usergroups']]),

    inquirer.Checkbox('chooseMaterials',
                      message='Select Material types',
                      choices=[(x['name'], x['id']) for x in materialTypesJson['mtypes']])
]

answers2 = inquirer.prompt(q2)
print(answers2)


# fetch loan types
loanTypesJson = fetch_json(testServer, s, '/loan-types?limit=1000')
loan_type_ids = list_maker(loanTypesJson['loantypes'])

# fetch material types


x = list(product(answers2['chooseGroup'],
         answers2['chooseMaterials'], loan_type_ids, answers2['chooseLoc']))
print(x, len(x))
