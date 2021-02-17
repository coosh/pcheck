from flask import Flask, request, render_template, Blueprint
import sys, requests, json, re, uuid
from app.item import item
from app.order import order

URL_TypeID="http://www.fuzzwork.co.uk/api/typeid2.php?typename="
URL_EveApraisal="https://evepraisal.com/appraisal/structured.json"
Asteroids = ['Veldspar', 'Scordite', 'Pyroxeres', 'Plagioclase', 'Kernite', 'Jaspet', 'Hemorphite', 'Omber', 'Arkonor', 'Bistot', 'Mercoxit', 'Spodumain']
custom_header = {"User-Agent": "Character, Cuish, Small Flask app to verify buybacks"}

contracts = Blueprint('contracts', __name__, template_folder='templates')

def save_request():
  print("saving")
  f = open(uuid.uuid4(), "a")
  f.write(request.form.get('data'))
  f.close()

def process_items():
  data = request.form.get('data')
  for line in data.splitlines():
    fields = line.split('\t')
    qty = fields[1].replace(',', '')
    if not qty:
      qty = 1
    items.append( item(fields[0].strip(), int(qty)) )

def get_ids():
  url = URL_TypeID
  for i in items:
    url = url + i.name + "|"
    res = any(ele in i.name for ele in Asteroids)
    if res == True:
      url = url + i.alt_name + "|"
  url = url[:-1]
  response = requests.get(url)
  json_data = json.loads(response.text)
  for i in items:
    for d in json_data:
      if i.name == d['typeName']:
        i.typeID = d['typeID']
      if i.alt_name == d['typeName']:
        i.alt_typeID = d['typeID']

def get_alts():
  for i in items:
    res = any(ele in i.name for ele in Asteroids)
    if res == True:
      if 'Compressed' in i.name:
        i.alt_name = i.name.replace('Compressed ', '')
        i.alt_amount = i.amount * 100
      else:
        i.alt_name = "Compressed " + i.name
        i.alt_amount = i.amount / 100
    else:
      i.alt_typeID = i.typeID
      i.alt_name = i.name
      i.alt_amount = i.amount

def get_price():
  ids, names, qty = [], [], []
  for i in items:
    ids.append(i.typeID)
    names.append(i.name)
    qty.append(i.amount)
  request_dict = [{"name": x, "type_id": int(y), "quantity": int(z)} for x, y, z in zip(names, ids, qty)]
  data = "{\"market_name\": \"jita\", \"items\":" + str(request_dict) + "}"
  data = data.replace("'", '"')
  request_json = json.loads(data)
  response = requests.post(URL_EveApraisal, json = request_json, headers = custom_header)
  json_data = json.loads(response.text)
  buy    = json_data['appraisal']['totals']['buy']
  sell   = json_data['appraisal']['totals']['sell']
  volume = json_data['appraisal']['totals']['volume']
  c_buy  = buy * 0.85
  c_sell = sell * 0.85
  orders.append( order("original", buy, sell, volume, c_buy, c_sell) )
  for i in items:
    for d in json_data['appraisal']['items']:
      if i.name in d['name']:
        i.buy_avg        = d['prices']['buy']['avg']
        i.buy_max        = d['prices']['buy']['max']
        i.buy_median     = d['prices']['buy']['median']
        i.buy_min        = d['prices']['buy']['min']
        i.buy_percentile = d['prices']['buy']['percentile']
        i.buy_stddev     = d['prices']['buy']['stddev']
        i.buy_volume     = d['prices']['buy']['volume']
        i.buy_ordercount = d['prices']['buy']['order_count']

        i.sell_avg        = d['prices']['sell']['avg']
        i.sell_max        = d['prices']['sell']['max']
        i.sell_median     = d['prices']['sell']['median']
        i.sell_min        = d['prices']['sell']['min']
        i.sell_percentile = d['prices']['sell']['percentile']
        i.sell_stddev     = d['prices']['sell']['stddev']
        i.sell_volume     = d['prices']['sell']['volume']
        i.sell_ordercount = d['prices']['sell']['order_count']

def get_alt_price():
  ids, names, qty = [], [], []
  for i in items:
    ids.append(i.alt_typeID)
    names.append(i.alt_name)
    qty.append(i.alt_amount)
  request_dict = [{"name": x, "type_id": int(y), "quantity": int(z)} for x, y, z in zip(names, ids, qty)]
  data = "{\"market_name\": \"jita\", \"items\":" + str(request_dict) + "}"
  data = data.replace("'", '"')
  request_json = json.loads(data)

  response = requests.post(URL_EveApraisal, json = request_json, headers = custom_header)
  json_data = json.loads(response.text)
  buy    = json_data['appraisal']['totals']['buy']
  sell   = json_data['appraisal']['totals']['sell']
  volume = json_data['appraisal']['totals']['volume']
  c_buy  = buy * 0.85
  c_sell = sell * 0.85
  orders.append( order("alt", buy, sell, volume, c_buy, c_sell) )
  for i in items:
    for d in json_data['appraisal']['items']:
      if i.alt_name in d['name']:
        i.alt_buy_avg        = d['prices']['buy']['avg']
        i.alt_buy_max        = d['prices']['buy']['max']
        i.alt_buy_median     = d['prices']['buy']['median']
        i.alt_buy_min        = d['prices']['buy']['min']
        i.alt_buy_percentile = d['prices']['buy']['percentile']
        i.alt_buy_stddev     = d['prices']['buy']['stddev']
        i.alt_buy_volume     = d['prices']['buy']['volume']
        i.alt_buy_ordercount = d['prices']['buy']['order_count']

        i.alt_sell_avg        = d['prices']['sell']['avg']
        i.alt_sell_max        = d['prices']['sell']['max']
        i.alt_sell_median     = d['prices']['sell']['median']
        i.alt_sell_min        = d['prices']['sell']['min']
        i.alt_sell_percentile = d['prices']['sell']['percentile']
        i.alt_sell_stddev     = d['prices']['sell']['stddev']
        i.alt_sell_volume     = d['prices']['sell']['volume']
        i.alt_sell_ordercount = d['prices']['sell']['order_count']

@contracts.route('/check', methods = ['POST', 'GET'])
def check():
  # GET Request, supply input!
  if request.method == 'GET':
    return render_template('check.html')

  # Process request
  if request.method == 'POST':
    global items
    global orders
    items = []
    orders = []
    process_items()
    get_alts()
    get_ids()
    get_price()
    get_alt_price()
    return render_template("check_result.html", items = items, orders = orders)

@contracts.route('/buyback', methods = ['POST', 'GET'])
def buyback():
  if request.method == 'GET':
    return render_template('buyback.html')

  if request.method == 'POST':
    global items
    global orders
    items = []
    orders = []
    process_items()
    get_alts()
    get_ids()
    get_price()
    get_alt_price()
    buybackprice=min(int(orders[0].buy_corp), int(orders[1].buy_corp))
    return render_template("buyback_result.html", buybackprice = buybackprice)
