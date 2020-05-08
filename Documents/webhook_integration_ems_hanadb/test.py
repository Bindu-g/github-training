from flask import Flask, request, jsonify
import requests
import json
import rq
import os
from keras.models import Sequential
from keras.models import model_from_json
import h5py
import numpy as np
import pandas as pd
from pandas.io.json import json_normalize
import keras
import tensorflow as tf
import time
import datetime
from json import JSONEncoder
from tensorflow.python.keras.backend import set_session



from json import dumps

from json import loads
from keras.models import model_from_yaml
from cfenv import AppEnv
app = Flask(__name__)

port = int(os.getenv("PORT"))
env = AppEnv()
global graph
global out_prob 
global non_out_prob 
global d_timestamp
global sess





@app.route('/')
def started():
    return 'Hello from python!!!'
tasks = {
        'id': 1,
        'title': u'created a new event',
        'description': u' ', 
        'done': False
         }


with open("model/hung_cats_v1_1.yml", "r") as f:
    yaml_file = f.read()
loaded_model = model_from_yaml(yaml_file)
loaded_model.load_weights("model/hung_cats_v1_1.h5")
# tf_config = '1.14.0'
session = tf.compat.v1.Session(graph=tf.compat.v1.Graph())
graph = tf.get_default_graph()


@app.route('/todo', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': tasks})


@app.route('/publish', methods=['POST'])
def webhook():
    
    test = request.get_data()
    test = test.decode('utf8')  #converting bytes to string 
    test= json.loads(test) #converting string to dict
#     for key in test.keys():
#         # if isinstance(test[key], dict)== True:
# #         print(dct[key])
#         if isinstance(test[key], dict)== False:
#             mod_test=test[key]
    arr = []
    # print(test)
    for key in test.keys():
        if isinstance(test[key], dict)== False:
            if key == 'AVG_PING_MS':
                arr.append(test[key])
            elif key == 'AVG_HOST_CPU_PCT':
                arr.append(test[key])
            elif key == 'AVG_TOT_CPU_PCT':
                arr.append(test[key])
            elif key == 'AVG_BLK_TRANS':
                arr.append(test[key])
            elif key == 'AVG_PEND_SESS':
                arr.append(test[key])  
            elif key == 'BEGIN_TIME':
                d_timestamp= test[key]

    # print(arr)            
    # print(type(arr))
    arr = [arr]*5
    df = pd.DataFrame(arr)
    df = df.values.reshape([1, 5, 5])
    # print(keras.__version__)
    # print(tf.__version__)
    
    with graph.as_default():
        set_session(session)
        result = loaded_model.predict(df)
    print(result)
    prediction = result.tolist()
    out_prob = prediction[0][0]
    non_out_prob = prediction[0][1]
    payload = {
    "timestamp" : datetime.datetime.now(),
    "value0" : out_prob,
    "value1" : non_out_prob,
    "dataTimestamp" : d_timestamp
    }
    class DateTimeEncoder(JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
    print(DateTimeEncoder().encode(payload))
    payload = json.dumps(payload, indent=1, cls=DateTimeEncoder)
    print(payload)
    print(type(payload))
    headers = {'Content-type':'application/json', 'Accept':'application/json'}
    url = 'https://pas-util-srv.cfapps.sap.hana.ondemand.com/api/v1/pasutil/Results'
    x = requests.post(url,data = payload,json= payload, headers=headers)
    print(x.text)
    # print(payload)
    return '{"success":"true"}'
     

        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
    # app.run(debug = True)
    

    