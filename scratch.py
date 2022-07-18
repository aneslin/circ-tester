def makeUrl(*kwargs):
    [z]=[x for x in kwargs]
    return ''.join(z)

testServer = 'a'

loan_type_id ='b'
patron_type_id = 'c'
location_id = "d"
item_type_id = 'e'
urlLoanPolicy_1 = '{}{}{}{}{}{}{}{}{}{}'.format(testServer, '/circulation/rules/loan-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)


print(makeUrl((testServer, '/circulation/rules/loan-policy?' , 'loan_type_id=', loan_type_id, '&item_type_id=', item_type_id, '&patron_type_id=', patron_type_id, '&location_id=', location_id)))