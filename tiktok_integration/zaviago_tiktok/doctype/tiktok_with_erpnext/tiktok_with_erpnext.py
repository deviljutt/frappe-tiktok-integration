# Copyright (c) 2023, Zaviago and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
# from tiktok_integration.tiktok_integration.zaviago_tiktok.create_client import CreateTiktokClient
from tiktok_integration.zaviago_tiktok.create_client import CreateTiktokClient
import webbrowser
from tiktok_integration.zaviago_tiktok.save_data import saveTiktokData
import json
import unicodedata
import calendar;
import time;
import hashlib
import hmac
import binascii
from datetime import datetime


class TiktokwithERPnext(Document):
	# def validate(self):
		 
	# 	meta = frappe.get_meta('SAL-ORD-2023-00228')
	# 	meta.has_field('status') # True
	# 	fields = meta.get_custom_fields() # [field1, field2, ..]
	# 	print( f" here are custom fields {fields}" )
	pass

class handleTiktokRequests:
	next_cursor=False
	limit = 10
	added_orders=0
	
	# def validate(self):
	# 	print(f"host is  {} ")


		# doc='SAL-ORD-2023-00020'
		# doc = frappe.get_doc("Sales Order",doc)
		# # meta = frappe.get_meta('Sales Order')
		#  # True
		# if( doc.tiktok_order_id):
		# 	print(f"\n\n have tiktok order id ")
		# 	print({doc.tiktok_order_id})
		# else:
		# 	print(f"\n\n dont have tiktok order id ")
		# return
		# self.fetch_orders()
		# count= 1 
		# while( self.next_cursor and self.limit>count ):
		# 	count=count+1
		# 	print(f"\n\n next cursor is set {count} added orders are {self.added_orders}")
		# 	self.fetch_orders()
		# return
		# if( self.app_key!='' and self.app_secret != '' and self.enable_tiktok ):
		# 	connect = CreateTiktokClient()	
		# 	url = connect.start_connecting ( self.app_key,self.app_secret,self.is_sandbox )
		# 	if( url ):
		# 		webbrowser.open( url )   
	def save_tiktok_order(self,orders):
		for o in orders: 

			prev_order = frappe.db.exists({"doctype": "Sales Order", "tiktok_order_id": o['order_id']})
			if( prev_order ):
				print(f"\n\n Order is already saved {prev_order}: {o['order_id']} \n\n")
				continue
			new_order = frappe.new_doc('Sales Order')
			# if o.get("shipping_provider") is not None:
			# 	return
			# print(f"Please Check Order Details {o}")
			customer_flag = frappe.db.exists("Customer", o['recipient_address']['name'] )
			if( customer_flag ==None ):
				self.create_customer( o['recipient_address'],o['recipient_address']['name'] )
			new_order.title=o['recipient_address']['name']
			new_order.customer=o['recipient_address']['name']
			new_order.order_type="Sales"
			date = o['create_time']
			
			date = int(date)/1000
			date = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d') 
			new_order.delivery_date=date
			new_order.tiktok_order_id=o['order_id']
			
			new_order.price_list_currency=o['payment_info']['currency']
			# create property setter for length

			for product in o['item_list']:
				item_code = product['seller_sku']
				Item = frappe.db.exists("Item", str(item_code))
				if( Item == None ):
					self.create_product(product['product_name'],product['seller_sku'],"By-product")
				new_order.append("items",{
					"item_code": product['seller_sku'],
					"item_name": product['product_name'],
					"uom": "Kg",
					# "description": "item description",
					# "conversion_factor": 1,
					"qty": product['quantity'],
					"price_list_rate": product['sku_original_price'],
					"rate": product['sku_original_price'],
					"amount": product['sku_sale_price'],
					"stock_uom_rate": product['sku_original_price'],
					"net_rate": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
					"net_amount": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
					"billed_amt": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
					"valuation_rate": product['sku_sale_price']-product['sku_seller_discount']-product['sku_platform_discount_total'],
					# "gross_profit": "600.00",
					# "projected_qty": 1,
					# "actual_qty": 42,
					# "delivered_qty": 1,
					# "ordered_qty": 0,
					# "work_order_qty": 0,
					})	
			response = new_order.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_if_duplicate=True, # dont insert if DuplicateEntryError is thrown
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
			new_order.submit()
			# frappe.msgprint("Created order")
			self.added_orders=self.added_orders+1
			print("Created order is")
			print(f"\n\n {response} ")
		return
	
	def create_customer(self,order_address,customer_name):
		new_customer = frappe.new_doc('Customer')
		new_customer.customer_name=customer_name
		response = new_customer.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		# frappe.msgprint("Created customer")
		
		country = zav_country_map.get(order_address["region_code"])
		address_type = "Billing"
		also_shipping=False
		frappe.get_doc(
		{
			"address_line1": order_address["full_address"] or "Not provided",
			"address_line2": '',
			"address_type": address_type,
			"city": order_address["city"],
			"country": country,
			"county": order_address["district"],
			"doctype": "Address",
			
			"phone": order_address["phone"],
			 
			 
			"links": [{"link_doctype": "Customer", "link_name": customer_name}],
			"is_primary_address": int(address_type == "Billing"),
			"is_shipping_address": int(also_shipping or address_type == "Shipping"),
		}
		).insert(ignore_mandatory=True)

	def create_product(self,item_name,item_code,item_group):
		Item = frappe.new_doc('Item')
		Item.item_name=item_name
		Item.item_code=item_code
		Item.item_group=item_group
		response = Item.insert(
				ignore_permissions=True, # ignore write permissions during insert
				ignore_links=True, # ignore Link validation in the document
				ignore_mandatory=True # insert even if mandatory fields are not set
			)
		
		print(f"\n\n {Item} ")
		return
	@frappe.whitelist( )
	def fetch_orders(self):
		print("function called")
		path='/api/orders/search'
		app_details = frappe.get_doc('Tiktok with ERPnext')
		access_token = app_details.get_password('access_token')
		app_secret = app_details.get_password('app_secret')
		gmt = time.gmtime()
		timestamp = calendar.timegm(gmt)    
		query = {
			"app_key":app_details.app_key,
			'access_token':access_token,
			'limit':20,
			'timestamp':timestamp,
		}
		params_for_sign = query
		del params_for_sign['access_token']
		##################################
		signature = self.getSignature(path,params_for_sign,app_secret)
		##################################
		if( app_details.is_sandbox ):
			uri = 'https://open-api-sandbox.tiktokglobalshop.com'
		else:
			uri = 'https://open-api.tiktokglobalshop.com'
		url = uri+"/api/orders/search?app_key="+str(app_details.app_key)+"&access_token="+str(access_token)+"&limit=20&sign="+str(signature)+"&timestamp="+str(timestamp)
		if( self.next_cursor ):
			json_params={
				'cursor':self.next_cursor,
				"page_size": 50
			}
		else:
			json_params={
				"page_size": 50
			}
		payload = json.dumps( json_params )
		headers = {
		'Content-Type': 'application/json'
		}
		response = requests.request("POST", url, headers=headers, data=payload)
		data = response.json()
		if( data['code']==0 ):
			print(f"\n\n {data['data']} ")
			order_list=[]
			for order in data['data']['order_list']:
				order_list.append(order['order_id'])
			self.fetchOrderDetails(order_list)
			if( data['data']['more']==True ):
				print(f"\n\n next cursor is {data['data']['next_cursor']} \n\n")
				self.next_cursor=data['data']['next_cursor']
			else:
				self.next_cursor=False
		else:
			print(f"\n\n {data} ")
		return

	def fetchOrderDetails(self,orderIDs):
		############################### get order details
		path='/api/orders/detail/query'
		app_details = frappe.get_doc('Tiktok with ERPnext')
		access_token = app_details.get_password('access_token')
		app_secret = app_details.get_password('app_secret')
		gmt = time.gmtime()
		timestamp = calendar.timegm(gmt)    
		# string_to_sign
		query = {
			"app_key":app_details.app_key,
			'access_token':access_token,
			'limit':20,
			'timestamp':timestamp,
		}
		params_for_sign = query
		del params_for_sign['access_token']
	
		##################################
		signature = self.getSignature(path,params_for_sign,app_secret)
		##################################
		if( app_details.is_sandbox ):
			uri = 'https://open-api-sandbox.tiktokglobalshop.com'
		else:
			uri = 'https://open-api.tiktokglobalshop.com'
		url = uri+path+"?app_key="+str(app_details.app_key)+"&access_token="+str(access_token)+"&limit=20&sign="+str(signature)+"&timestamp="+str(timestamp)

		payload = json.dumps({
		#"order_id_list": ['577463955647466245']
		"order_id_list": orderIDs
		})
		headers = {
		'Content-Type': 'application/json'
		}
		response = requests.request("POST", url, headers=headers, data=payload)
		#################################
		data = response.json()
		print( f"\n\n showing single order \n\n" ) 
		if( data['code']==0 ):
			order = data['data']['order_list']
			self.save_tiktok_order(data['data']['order_list'])
		return 


	def getSignature( self,path,params,app_secret ):
		signature = ''
		string_to_sign=''
		params_for_sign = params
		myKeys = list(params_for_sign.keys())
		myKeys.sort()
		sorted_params_for_sign = {i: params_for_sign[i] for i in myKeys}
		for k,v in sorted_params_for_sign.items():
			string_to_sign=string_to_sign+str(k)+str(v)
		string_to_sign = path+string_to_sign
		string_to_sign = app_secret+string_to_sign+app_secret
		signature=hmac.new(bytes(app_secret, 'UTF-8'), string_to_sign.encode(), hashlib.sha256).hexdigest()
		return signature

@frappe.whitelist( )
def ajax_init_fetch_orders():
	 
	tiktok = handleTiktokRequests()
	tiktok.fetch_orders( )
	count= 1 
	while( tiktok.next_cursor ):
		count=count+1
		print(f"\n\n next cursor is set {count} added orders are {tiktok.added_orders}")
		tiktok.fetch_orders()
	url = frappe.utils.get_url()+"app/sales-order"
	print(f"\n\n url is {url} ")
	webbrowser.open( url,new=0 )
	return

zav_country_map = {
	"AD": "Andorra",
	"AE": "United Arab Emirates",
	"AF": "Afghanistan",
	"AG": "Antigua and Barbuda",
	"AI": "Anguilla",
	"AL": "Albania",
	"AM": "Armenia",
	"AO": "Angola",
	"AQ": "Antarctica",
	"AR": "Argentina",
	"AS": "American Samoa",
	"AT": "Austria",
	"AU": "Australia",
	"AW": "Aruba",
	"AZ": "Azerbaijan",
	"BA": "Bosnia and Herzegovina",
	"BB": "Barbados",
	"BD": "Bangladesh",
	"BE": "Belgium",
	"BF": "Burkina Faso",
	"BG": "Bulgaria",
	"BH": "Bahrain",
	"BI": "Burundi",
	"BJ": "Benin",
	"BM": "Bermuda",
	"BR": "Brazil",
	"BS": "Bahamas",
	"BT": "Bhutan",
	"BV": "Bouvet Island",
	"BW": "Botswana",
	"BY": "Belarus",
	"BZ": "Belize",
	"CA": "Canada",
	"CF": "Central African Republic",
	"CH": "Switzerland",
	"CI": "Ivory Coast",
	"CK": "Cook Islands",
	"CL": "Chile",
	"CM": "Cameroon",
	"CN": "China",
	"CO": "Colombia",
	"CR": "Costa Rica",
	"CU": "Cuba",
	"CV": "Cape Verde",
	"CX": "Christmas Island",
	"CY": "Cyprus",
	"CZ": "Czech Republic",
	"DE": "Germany",
	"DJ": "Djibouti",
	"DK": "Denmark",
	"DM": "Dominica",
	"DO": "Dominican Republic",
	"DZ": "Algeria",
	"EC": "Ecuador",
	"EE": "Estonia",
	"EG": "Egypt",
	"EH": "Western Sahara",
	"ER": "Eritrea",
	"ES": "Spain",
	"ET": "Ethiopia",
	"FI": "Finland",
	"FJ": "Fiji",
	"FK": "Falkland Islands",
	"FM": "Micronesia",
	"FO": "Faroe Islands",
	"FR": "France",
	"GA": "Gabon",
	"GB": "United Kingdom",
	"GD": "Grenada",
	"GE": "Georgia",
	"GF": "French Guiana",
	"GG": "Guernsey",
	"GH": "Ghana",
	"GI": "Gibraltar",
	"GL": "Greenland",
	"GM": "Gambia",
	"GN": "Guinea",
	"GP": "Guadeloupe",
	"GQ": "Equatorial Guinea",
	"GR": "Greece",
	"GS": "South Georgia and the South Sandwich Islands",
	"GT": "Guatemala",
	"GU": "Guam",
	"GW": "Guinea-Bissau",
	"GY": "Guyana",
	"HK": "Hong Kong",
	"HM": "Heard Island and McDonald Islands",
	"HN": "Honduras",
	"HR": "Croatia",
	"HT": "Haiti",
	"HU": "Hungary",
	"ID": "Indonesia",
	"IE": "Ireland",
	"IL": "Israel",
	"IM": "Isle of Man",
	"IN": "India",
	"IO": "British Indian Ocean Territory",
	"IQ": "Iraq",
	"IR": "Iran",
	"IS": "Iceland",
	"IT": "Italy",
	"JE": "Jersey",
	"JM": "Jamaica",
	"JO": "Jordan",
	"JP": "Japan",
	"KE": "Kenya",
	"KG": "Kyrgyzstan",
	"KH": "Cambodia",
	"KI": "Kiribati",
	"KM": "Comoros",
	"KN": "Saint Kitts and Nevis",
	"KR": "Korea, Republic of",
	"KW": "Kuwait",
	"KY": "Cayman Islands",
	"KZ": "Kazakhstan",
	"LB": "Lebanon",
	"LC": "Saint Lucia",
	"LI": "Liechtenstein",
	"LK": "Sri Lanka",
	"LR": "Liberia",
	"LS": "Lesotho",
	"LT": "Lithuania",
	"LU": "Luxembourg",
	"LV": "Latvia",
	"LY": "Libya",
	"MA": "Morocco",
	"MC": "Monaco",
	"MD": "Moldova, Republic of",
	"ME": "Montenegro",
	"MG": "Madagascar",
	"MH": "Marshall Islands",
	"MK": "Macedonia",
	"ML": "Mali",
	"MM": "Myanmar",
	"MN": "Mongolia",
	"MO": "Macao",
	"MP": "Northern Mariana Islands",
	"MQ": "Martinique",
	"MR": "Mauritania",
	"MS": "Montserrat",
	"MT": "Malta",
	"MU": "Mauritius",
	"MV": "Maldives",
	"MW": "Malawi",
	"MX": "Mexico",
	"MY": "Malaysia",
	"MZ": "Mozambique",
	"NA": "Namibia",
	"NC": "New Caledonia",
	"NE": "Niger",
	"NF": "Norfolk Island",
	"NG": "Nigeria",
	"NI": "Nicaragua",
	"NL": "Netherlands",
	"NO": "Norway",
	"NP": "Nepal",
	"NR": "Nauru",
	"NU": "Niue",
	"NZ": "New Zealand",
	"OM": "Oman",
	"PA": "Panama",
	"PE": "Peru",
	"PF": "French Polynesia",
	"PG": "Papua New Guinea",
	"PH": "Philippines",
	"PK": "Pakistan",
	"PL": "Poland",
	"PM": "Saint Pierre and Miquelon",
	"PN": "Pitcairn",
	"PR": "Puerto Rico",
	"PT": "Portugal",
	"PW": "Palau",
	"PY": "Paraguay",
	"QA": "Qatar",
	"RO": "Romania",
	"RS": "Serbia",
	"RU": "Russian Federation",
	"RW": "Rwanda",
	"SA": "Saudi Arabia",
	"SB": "Solomon Islands",
	"SC": "Seychelles",
	"SD": "Sudan",
	"SE": "Sweden",
	"SG": "Singapore",
	"SI": "Slovenia",
	"SJ": "Svalbard and Jan Mayen",
	"SK": "Slovakia",
	"SL": "Sierra Leone",
	"SM": "San Marino",
	"SN": "Senegal",
	"SO": "Somalia",
	"SR": "Suriname",
	"ST": "Sao Tome and Principe",
	"SV": "El Salvador",
	"SY": "Syria",
	"SZ": "Swaziland",
	"TC": "Turks and Caicos Islands",
	"TD": "Chad",
	"TF": "French Southern Territories",
	"TG": "Togo",
	"TH": "Thailand",
	"TJ": "Tajikistan",
	"TK": "Tokelau",
	"TM": "Turkmenistan",
	"TN": "Tunisia",
	"TO": "Tonga",
	"TR": "Turkey",
	"TT": "Trinidad and Tobago",
	"TV": "Tuvalu",
	"TW": "Taiwan",
	"TZ": "Tanzania",
	"UA": "Ukraine",
	"UG": "Uganda",
	"UM": "United States Minor Outlying Islands",
	"US": "United States",
	"UY": "Uruguay",
	"UZ": "Uzbekistan",
	"VC": "Saint Vincent and the Grenadines",
	"VE": "Venezuela, Bolivarian Republic of",
	"VN": "Vietnam",
	"VU": "Vanuatu",
	"WF": "Wallis and Futuna",
	"WS": "Samoa",
	"YE": "Yemen",
	"YT": "Mayotte",
	"ZA": "South Africa",
	"ZM": "Zambia",
	"ZW": "Zimbabwe",
}
