import json
import requests
import pandas as pd
import numpy as np
from jsonpath_ng import parse
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import time



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
            'api-key': self.api_key
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
                if q['queryType'] == 'semantic':
                #extract the id and search score and store the score in results with the id as key
                    results[qid] = {item['document_id']: item['@search.rerankerScore'] for item in r['value']}
                else:
                    results[qid] = {item['document_id']: item['@search.score'] for item in r['value']}

                    
            except:
                raise
        return results

#retrieve key (dont know if the url/secret_name is considered sensitive but i dont think so , can make it a param in request if needed)
def retrieve_key():
    start_time = time.time()
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    key_vault_url = config['key_vault_url']
    secret_name = config['secret_name']
    max_workers = config['max_workers']

    client = SecretClient(vault_url=key_vault_url, credential=credential)
    retrieved_secret = client.get_secret(secret_name)
    api_key = retrieved_secret.value
    end_time = time.time()
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

        
def write_results_to_json(results, output_filename):
    with open(output_filename, 'w') as json_file:
        json.dump(results, json_file, indent=4)





    
   
    