from flask import Flask, session, redirect, url_for, request, render_template, jsonify
from markupsafe import escape
import sys, requests, json, re, uuid

app = Flask(__name__)

URL_TypeID="http://www.fuzzwork.co.uk/api/typeid2.php?typename="
URL_EveApraisal="https://evepraisal.com/appraisal/structured.json"
Asteroids = ['Veldspar', 'Scordite', 'Pyroxeres', 'Plagioclase', 'Kernite', 'Jaspet', 'Hemorphite', 'Omber', 'Arkonor', 'Bistot', 'Mercoxit', 'Spodumain']
custom_header = {"User-Agent": "Character, Cuish, Small Flask app to verify buybacks"}

class order:
  def __init__(self, name, buy, sell, volume, buy_corp, sell_corp):
    self.name      = name
    self.buy       = buy
    self.sell      = sell
    self.volume    = volume
    self.buy_corp  = buy_corp
    self.sell_corp = sell_corp
  

class item:
  alt_name   = ""
  typeID     = "0"
  alt_typeID = "0"
  def __init__(self, name, amount, name_type, category):
    self.name     = name
    self.amount   = amount
    self.type     = name_type
    self.category = category

def save_request():
  print("saving")
  f = open(uuid.uuid4(), "a")
  f.write(request.form.get('data'))
  f.close()

def process_items_contract():
  data = request.form.get('data')
  for line in data.splitlines():
    fields = line.split('\t')
    qty = fields[1].replace(',', '')
    items.append( item(fields[0].strip(), int(qty), fields[2], fields[3]) )

def process_items_buyback():
  data = request.form.get('data')
  for line in data.splitlines():
    fields = line.split('\t')
    qty = fields[1].replace(',', '')
    items.append( item(fields[0].strip(), int(qty), fields[2], fields[3]) )

def get_ids():
  url = URL_TypeID
  for i in items:
    url = url + i.name + "|"
    if i.category == "Asteroid":
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
    if 'Ice' not in i.type and 'Moon' not in i.type and 'Asteroid' in i.category:
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
  data = "{\"market_name\": \"jita\", \"items\":"
  for i in items:
    ids.append(i.typeID)
    names.append(i.name)
    qty.append(i.amount)
  request_dict = [{"name": x, "type_id": int(y), "quantity": int(z)} for x, y, z in zip(names, ids, qty)]
  data = data + str(request_dict)
  data = data + "}"
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
  data = "{\"market_name\": \"jita\", \"items\":"
  for i in items:
    ids.append(i.alt_typeID)
    names.append(i.alt_name)
    qty.append(i.alt_amount)
  request_dict = [{"name": x, "type_id": int(y), "quantity": int(z)} for x, y, z in zip(names, ids, qty)]
  data = data + str(request_dict)
  data = data + "}"
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

@app.route('/check', methods = ['POST', 'GET'])
def index():
  # GET Request, supply input!
  if request.method == 'GET':
    return render_template('form.html')

  # Process request
  if request.method == 'POST':
    global items
    global orders
    items = []
    orders = []
    process_items_contract()
    get_alts()
    get_ids()
    get_price()
    get_alt_price()
    return render_template("result.html", items = items, orders = orders)

@app.route('/buyback', methods = ['POST', 'GET'])
def buyback():
  if request.method == 'GET':
    return render_template('form.html')

  if request.method == 'POST':
    global items
    global orders
    items = []
    orders = []
    save_request()
    process_items_buyback()
    get_alts()
    get_ids()
    get_price()
    get_alt_price()
    return render_template("buyback.html", items = items, orders = orders)
