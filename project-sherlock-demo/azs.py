import json
import requests
import pandas as pd
import numpy as np
from jsonpath_ng import parse
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import configparser
from mteb.evaluation.evaluators import RetrievalEvaluator
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
import time


app = Flask(__name__)
CORS(app)
credential = DefaultAzureCredential()



class AzureSearch:
    def __init__(self, endpoint, api_key, api_version, service, query_payload =None, vectorizer=None):
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version
        self.service_name = service
        self.base_url = f"https://{self.service_name}.search.windows.net"

        self.headers = {
            'Content-Type' : 'application/json',
            'api-key':self.api_key
        }
        
    
    def url(self,path):
        return f"{self.base_url}/{path}?api-version={self.api_version}"


    def search(self, index, q):
        headers = {
            'Content-Type': 'application/json',
            'api-key': retrieve_key()  
        }
        params = {
            'api-version': self.api_version  
        }
        url = f"https://{self.service_name}.search.windows.net/indexes/{index}/docs/search"

        try:
            response = requests.post(url, json=q, headers=headers, params=params)
            response.raise_for_status()  

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Unexpected status code: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error requesting data: {e}")
            return None


    def get_search_results(self, queries, index_name):
        results = {}
        for qid in queries.keys():
            #skip processed queries
            if qid in results:
                continue
            #retrieve the query and run search 
            q = queries[qid]
            r = self.search(index_name, q)
            try:
                #extract the id and search score and store the score in results with the id as key
                results[qid] = {item['document_id']: item['@search.rerankerScore'] for item in r['value']}
            except:
                raise
        return results

#retrieve key (dont know if the url/secret_name is considered sensitive but i dont think so , can make it a param in request if needed)
def retrieve_key():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    
    key_vault_url = config['key_vault_url']
    secret_name = config['secret_name']

    client = SecretClient(vault_url=key_vault_url, credential=credential)
    retrieved_secret = client.get_secret(secret_name)
    api_key = retrieved_secret.value
    
    return api_key
    


def convert_ndarray_to_list(value):
    if isinstance(value,np.ndarray):
        return value.tolist()
    return value

def select_and_rename_columns(df,columns):
    if isinstance(columns,list):
        new_df = df[columns]
    elif isinstance(columns,dict):
        new_df = pd.DataFrame()
        for key,value in columns.items():
            if isinstance(value,list):
                for v in value:
                    new_df[v] = df[key]
            else:
                new_df[value] = df[key]
    else:
        raise ValueError("Columns must either be a list or dicitonary")
    return new_df


        
@app.route('/search', methods=['POST'])
def search_advanced():
    #get parameters and json template from request
    endpoint = request.args.get('endpoint')
    version = request.args.get('version')
    service = request.args.get('service')
    index = request.args.get('index')
    result_file = request.args.get('result_file')
    query_payload = request.get_json()

    #grab the query list
    with open('queries.json', 'r') as file:
        query_list = json.load(file)

    #iterate through the k,v pair of query id and term
    ndcg1,ndcg5,ndcg10 = 0,0,0
    precision1,precision5,precision10 = 0,0,0
    #for printing iteration number (debug purposes)
    count = 1
    
    #can remove this code if need be, used to measure processing time of all queries
    #grab key to not expose secret
    key = retrieve_key()
    # Create an instance of AzureSearch
    ss = AzureSearch(endpoint, key, version, service)
    qrels_dict = json.load(open('qrels_dict.json'))


    for key,values in query_list.items():
        payload = query_payload.copy()
        #assign to the values of the provided fields which will be null 
        payload['document_id'] = key
        payload['search'] = values
        #wrap in a list to prep for dataframe

        payload_str = json.dumps(payload)
        payload_str = payload_str.replace("#search#", values)
        payload = json.loads(payload_str)
    
        # Wrap in a list to prep for dataframe
        query_payload_list = [payload]
        #turn to df
        df_queries = pd.DataFrame(query_payload_list)
        # Set 'document_id' as the index
        dict_expanded = df_queries.set_index('document_id').to_dict(orient='index')

        # Get search results for each search term
        results = ss.get_search_results(dict_expanded, index)

        #evaluate the information
        ndcg,precision = evaluate(results,qrels_dict)

        #cumulate the scores for each metric
        ndcg1 += ndcg['NDCG@1']
        ndcg5 += ndcg['NDCG@5']
        ndcg10 += ndcg['NDCG@10']
        
        precision1 += precision['P@1']
        precision5 += precision['P@5']
        precision10 += precision['P@10']
 

    #get length of query list
    num_queries = len(query_list)

    #compute average scores for all queries
    ndcg1,ndcg5,ndcg10 =  ndcg1/num_queries , ndcg5/num_queries , ndcg10/num_queries
    precision1,precision5,precision10 =  precision1/num_queries , precision5/num_queries , precision10/num_queries

    #package for frontend to recieve
    ndcg = {
        'NDCG@1': ndcg1,
        'NDCG@5': ndcg5,
        'NDCG@10': ndcg10
    }

    precision = {
        'P@1' : precision1,
        'P@5': precision5,
        'P@10': precision10
    }

 
    print(ndcg, precision)

        
    metrics = {
        "ndcg": ndcg,
        "precision": precision
    }
      
    return jsonify(metrics)

#endpoint to upload ground truth values
@app.route('/upload_truth', methods=['POST'])
def upload_ground_truth():
    ground_truth = request.get_json()
    write_results_to_json(ground_truth,'qrels_dict.json')
    return ("Upload")


def write_results_to_json(results, output_filename):
    with open(output_filename, 'w') as json_file:
        json.dump(results, json_file, indent=4)
    # print(f'Results have been written to {output_filename}')

evaluator = RetrievalEvaluator()


def evaluate(results, qrels_dict):
    
    evaluation_results = evaluator.evaluate(qrels_dict, results, [1, 5, 10])
    ndcg = evaluation_results[0]
    _map = evaluation_results[1]
    recall = evaluation_results[2]
    precision = evaluation_results[3]

    return ndcg,recall,precision

if __name__ == '__main__':
    # Run your Flask app
    app.run(debug=True)


    
   
    