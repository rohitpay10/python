from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from pprint import pprint
import base64
import string
import hashlib
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
import json
import binascii

BLOCK_SIZE = 16

pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]


def encode(to_encode, iv, key):
    to_encode = pad(to_encode)
    c = AES.new(key, AES.MODE_CBC, iv)
    to_encode = c.encrypt(to_encode)
    to_encode = base64.b64encode(to_encode)
    return to_encode.decode("UTF-8")


def decode(enc):
    enc = base64.b64decode(enc)
    #key will merchant hosted key and iv will be first 16 characters of merchant hosted key
    iv = b'D9C6C86443383ACE'
    key = b'D9C6C86443383ACEA888E2B9F2F90D74'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    to_decode = cipher.decrypt(enc)
    string_response = unpad(to_decode).decode('utf-8')
    string_response = string_response.split("~")
    return string_response


# 
# Entry point of application
# 
def index(request):
	if request.method == 'POST':
		# Generate post data from transaction data
		data = generatePostVars(request.POST)
		return render(request, "redirect.html", {'data':data, 'settings':settings})
	else:
		data = {}
		return render(request, "index.html", {'data':data, 'settings':settings})

# Process response
def response(request):
	if request.method == 'POST':
	  
		data = request.POST
		encdata = data['ENCDATA']
		name = encdata
		name = decode(name)
		
		return render(request, "response.html", {'data':data,'name':name,'settings':settings})

		# check = validateResponse(data)
		# if check:
		# 	return render(request, "response.html", {'data':data, 'settings':settings})
		# else:
		# 	return HttpResponse('<h1>Checksum Validation Failed</h1>')
	else:
		return HttpResponse('<h1>NO RESPONSE FROM GATEWAY</h1>')

def generatePostVars(params):
	data = {}
	data["PAY_ID"] = params["PAY_ID"]
	data["ORDER_ID"] = params["ORDER_ID"]
	data["RETURN_URL"] = params["RETURN_URL"]
	data["CUST_EMAIL"] = params["CUST_EMAIL"]
	data["CUST_NAME"] = params["CUST_NAME"]
	data["CUST_STREET_ADDRESS1"] = params["CUST_STREET_ADDRESS1"]
	data["CUST_CITY"] = "NA"
	data["CUST_STATE"] = "NA"
	data["CUST_COUNTRY"] = "NA"
	data["CUST_ZIP"] = params["CUST_ZIP"]
	data["CUST_PHONE"] = params["CUST_PHONE"]
	data["CURRENCY_CODE"] = settings.PG_CURRENCY_CODE
	data["AMOUNT"] = int(float(params["AMOUNT"]) * 100)
	data["PRODUCT_DESC"] = "Test Transaction"
	data["CUST_SHIP_STREET_ADDRESS1"] = params["CUST_STREET_ADDRESS1"]
	data["CUST_SHIP_CITY"] = "NA"
	data["CUST_SHIP_STATE"] = "NA"
	data["CUST_SHIP_COUNTRY"] = "NA"
	data["CUST_SHIP_ZIP"] = params["CUST_ZIP"]
	data["CUST_SHIP_PHONE"] = params["CUST_PHONE"]
	data["CUST_SHIP_NAME"] = params["CUST_NAME"]
	data["TXNTYPE"] = settings.PG_TXNTYPE

	if "MERCHANT_PAYMENT_TYPE" in params:
		data["MERCHANT_PAYMENT_TYPE"] = params["MERCHANT_PAYMENT_TYPE"]

	data["HASH"] = generateHash(data)
	return data
# 
# Generate Hash for post data
# 
def generateHash(params):
	params_string = []
	for key in sorted(params.keys()):
		value = '='.join([str(key), str(params[key])])
		params_string.append('' if value == 'null' else str(value))

	# Join all values in single string
	params_string = '~'.join(params_string)

	# Add Salt
	final_string = '%s%s' % (params_string, settings.PG_SALT)

	# Generate 256 hash
	hasher = hashlib.sha256(final_string.encode())
	hash_string = hasher.hexdigest().upper()
	return hash_string


    

# Validate transaction response from gateway
def validateResponse(params):
	data = {}
	data["AMOUNT"] = params["AMOUNT"]
	data["CURRENCY_CODE"] = params["CURRENCY_CODE"]
	data["CUST_EMAIL"] = params["CUST_EMAIL"]
	data["CUST_NAME"] = params["CUST_NAME"]
	data["CUST_PHONE"] = params["CUST_PHONE"]
	data["ORDER_ID"] = params["ORDER_ID"]
	data["PAY_ID"] = params["PAY_ID"]
	data["PRODUCT_DESC"] = params["PRODUCT_DESC"]
	data["RESPONSE_CODE"] = params["RESPONSE_CODE"]
	data["RESPONSE_DATE_TIME"] = params["RESPONSE_DATE_TIME"]
	data["RESPONSE_MESSAGE"] = params["RESPONSE_MESSAGE"]
	data["RETURN_URL"] = params["RETURN_URL"]
	data["STATUS"] = params["STATUS"]
	data["TXNTYPE"] = params["TXNTYPE"]
	data["TXN_ID"] = params["TXN_ID"]
	if "ACQ_ID" in params:
		data["ACQ_ID"] = params["ACQ_ID"]
	if "CARD_MASK" in params:
		data["CARD_MASK"] = params["CARD_MASK"]
	if "DUPLICATE_YN" in params:
		data["DUPLICATE_YN"] = params["DUPLICATE_YN"]
	if "MOP_TYPE" in params:
		data["MOP_TYPE"] = params["MOP_TYPE"]
	if "RRN" in params:
		data["RRN"] = params["RRN"]
	if "ORIG_TXN_ID" in params:
		data["ORIG_TXN_ID"] = params["ORIG_TXN_ID"]
	if "PAYMENT_TYPE" in params:
		data["PAYMENT_TYPE"] = params["PAYMENT_TYPE"]
	
	# Generate transaction response hash
	transaction_hash = generateHash(data)

	# Check and return
	if params["HASH"] == transaction_hash:
		return True
	else:
		return False