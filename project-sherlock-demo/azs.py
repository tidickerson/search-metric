import json
import requests
import pandas as pd
import numpy as np
from jsonpath_ng import parse
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from datasets import load_dataset
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
        self.query_payload = query_payload
        self.vectorizer = vectorizer
    
    def url(self,path):
        return f"{self.base_url}/{path}?api-version={self.api_version}"


    def index(self, index, documents):
        for d in documents:
            print(d)
            if '_id' in d:
                d['_id'] = d.pop('_id')
            d['@search.action'] = "mergeOrUpload"
        data = {"value":documents}
        response = requests.post(self.url(f'indexes/{index}/docs/index'), json=data, headers=self.headers, verify=False)
        return response.json()
    
    def search(self, index, q):
        headers = {
            'Content-Type': 'application/json',
            'api-key': retrieve_key()  
        }
        params = {
            'api-version': self.api_version  
        }
        url = f"https://{self.service_name}.search.windows.net/indexes/{index}/docs/search"
        print(url)

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
    key_vault_url = "https://tidickerson-kv.vault.azure.net/"
    secret_name = "apikey"
    client = SecretClient(vault_url=key_vault_url, credential=credential)
    retrieved_secret = client.get_secret(secret_name)
    api_key = retrieved_secret.value
    return api_key

        

def batch_dataframe(df, batch_size=100):
    total_rows = len(df)
    for start in range(0, total_rows, batch_size):
        end = min(start+batch_size,total_rows)
        yield df.iloc[start:end]
    
def create_index(endpoint, key, version, service, name, output, data=None, dimensions=None):
    ss = AzureSearch(endpoint,key,version,service)
    if data is not None:
        with open(data,'r') as f:
            data = json.load(f)
    
    if dimensions is not None:
        for field in data['fields']:
            if 'dimensions' in field:
                field['dimension'] = dimensions
    
    json_path_expr = parse('$.name')
    for match in json_path_expr.find(data):
        match.full_path.update(data,name)
    
    r = ss.create_index(name,data=data)
    with open(output,'w') as f:
        f.write(json.dumps(r))
    return r

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

def index_data(endpoint, key, version, service, index, data, output, columns=None):
    df = pd.read_feather(data)
    df = df.applymap(convert_ndarray_to_list)

    ss = AzureSearch(endpoint,key,version,service)

    for batch in batch_dataframe(df):
        data = batch.to_dict(orient='records')
        r = ss.index(index, data)
        print(r)
    
    print("Indexed %d data successfully"%len(df))
    with open(output,'w') as f:
        f.write("Indexed %d data successfully"%len(df))

        
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
    recall1,recall5,recall10 = 0,0,0
    #for printing iteration number (debug purposes)
    count = 1
    
    #can remove this code if need be, used to measure processing time of all queries
    start_time = time.perf_counter()
    #grab key to not expose secret
    key = retrieve_key()
    # Create an instance of AzureSearch
    ss = AzureSearch(endpoint, key, version, service)

    for key,values in query_list.items():
        payload = query_payload.copy()
        #assign to the values of the provided fields which will be null 
        payload['document_id'] = key
        payload['search'] = values
        #wrap in a list to prep for dataframe
        query_payload_list = [payload]
        #turn to df
        df_queries = pd.DataFrame(query_payload_list)
        # Set 'document_id' as the index
        dict_expanded = df_queries.set_index('document_id').to_dict(orient='index')

        # Get search results for each search term
        results = ss.get_search_results(dict_expanded, index)

        # Write the results to the result file (used for evaluation)
        with open(result_file, 'w') as f:
            json.dump(results, f, indent=4)

        #evaluate the information
        ndcg,recall,precision = evaluate(result_file,'result_file.txt','mteb/trec-covid')

        #debug purposes
        print("iteration ",count, "values = ", ndcg['NDCG@1'],ndcg['NDCG@5'],ndcg['NDCG@10'])
        count+=1

        #cumulate the scores for each metric
        ndcg1 += ndcg['NDCG@1']
        ndcg5 += ndcg['NDCG@5']
        ndcg10 += ndcg['NDCG@10']
        
        precision1 += precision['P@1']
        precision5 += precision['P@5']
        precision10 += precision['P@10']

        recall1 += recall['Recall@1']
        recall5 += recall['Recall@5']
        recall10 += recall['Recall@10']

    #get length of query list
    num_queries = len(query_list)

    #compute average scores for all queries
    ndcg1,ndcg5,ndcg10 =  ndcg1/num_queries , ndcg5/num_queries , ndcg10/num_queries
    precision1,precision5,precision10 =  precision1/num_queries , precision5/num_queries , precision10/num_queries
    recall1,recall5,recall10 = recall1/num_queries , recall5/num_queries , recall10/num_queries

    end_time = time.perf_counter()
    elapsed_time = end_time-start_time

    print("TIME TO PROCESS QUERIES = ", elapsed_time)

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

    recall = {
        'Recall@1': recall1,
        'Recall@5': recall5,
        'Recall@10': recall10
    }
    print(ndcg, precision, recall)

        
    metrics = {
        "ndcg": ndcg,
        "recall": recall,
        "precision": precision
    }
    
  
    
    return jsonify(metrics)

#endpoint to upload ground truth values
@app.route('/upload_truth', methods=['POST'])
def upload_ground_truth():
    ground_truth = request.get_json()
    write_results_to_json(ground_truth,'qrels_dict.json')
    return ("Upload")



def search(endpoint, key, version, service, index, query_file, vector_column, field, k, result_file, oversampling=None):
    #read feather file to a data frame
    df_queries = pd.read_feather(query_file)
    #convert the numpy arrays to lists
    df_queries[vector_column] = df_queries[vector_column].map(lambda x: x.tolist())
    #convert df to dictionary
    queries = df_queries.set_index('_id').to_dict(orient='index')

    #constructs the payload based on if oversampling is None or not, conditional based on oversampling since it is an optional param
    if oversampling is None:
        query_payload = """{{
                "select": "id",
                "vectorQueries": [{{
                    "kind": "vector",
                    "vector": {%s},
                    "fields": "%s",
                    "k":%d
                }}]
            }}""" % (vector_column, field, k)
    else:
        query_payload = """{{
                "select": "id",
                "vectorQueries": [{{
                    "kind": "vector",
                    "vector": {%s},
                    "fields": "%s",
                    "k":%d,
                    "oversampling": %f
                }}]
            }}""" % (vector_column, field, k, oversampling)

    #same function as in advanced search

    ss = AzureSearch(endpoint, key, version, service, query_payload=query_payload)
    r = ss.get_search_results(queries, index)

    with open(result_file, 'w') as f:
        f.write(json.dumps(r, indent=4))
    evaluate(result_file,)


#assesses the performance of retrieval models, determining how well they retrieve and rank relevant item
evaluator = RetrievalEvaluator()

#all of the data sets in a list
mteb_datasets = [
    "mteb/arguana", "mteb/climate-fever", "mteb/cqadupstack-android", "mteb/cqadupstack-english",
    "mteb/cqadupstack-gaming", "mteb/cqadupstack-gis", "mteb/cqadupstack-mathematica", "mteb/cqadupstack-physics",
    "mteb/cqadupstack-programmers", "mteb/cqadupstack-stats", "mteb/cqadupstack-tex", "mteb/cqadupstack-unix",
    "mteb/cqadupstack-webmasters", "mteb/cqadupstack-wordpress", "mteb/dbpedia", "mteb/fever", "mteb/fiqa",
    "mteb/hotpotqa", "mteb/msmarco", "mteb/nfcorpus", "mteb/nq", "mteb/quora", "mteb/scidocs", "mteb/scifact",
    "mteb/touche2020", "mteb/trec-covid"
]

#get rid of mteb/ in all of the datasets
s = "mteb/trec-covid"
mteb_name_set = set(s.replace("mteb/", ""))

#function takes in arels and makes a qrel dict
def get_labels(qrels):
    qrels_dict = defaultdict(dict)
    #maps the score to the query id and corpus id
    def qrels_dict_init(row):
        qrels_dict[row["query-id"]][row["corpus-id"]] = int(row["score"])
    
    #then if test or dev keys exist in the input, apply qrels_dict_init function
    if 'test' in qrels:
        qrels['test'].map(qrels_dict_init)
        
    if 'dev' in qrels:
        qrels['dev'].map(qrels_dict_init)
    return qrels_dict


#remove labels not in the corpus ids set
def clean_labels(qrels_dict, corpus_ids):
    corpus_ids_set = set(corpus_ids)
    for q in qrels_dict:
        ds = list(qrels_dict[q].keys())
        for d in ds:
            if not d in corpus_ids_set:
                qrels_dict[q].pop(d)
    return qrels_dict


#create new kv pair filtered dict that only includes values from result if they are in qrels_dict
def clean_result(qrels_dict, result):
    filtered_dict = {k: result[k] for k in qrels_dict if k in result}
    # print("Filtered Dictionary:", filtered_dict)
    return filtered_dict




def write_results_to_json(results, output_filename):
    with open(output_filename, 'w') as json_file:
        json.dump(results, json_file, indent=4)
    # print(f'Results have been written to {output_filename}')


def evaluate(result_file, output, dataset_name=None, qrel_path=None, corpus_ids=None):
    #if there is a dataset name print a message for it
    if dataset_name:
        print("loading dataset: %s" % dataset_name)
        #if it is in the mteb_name_set, add mteb/ back to it
        if dataset_name in mteb_name_set:
            dataset_name = "mteb/" + dataset_name



    #else if we get a qrel file path, load that instead
    elif qrel_path:
        print("loading qrel file: %s" % qrel_path)
        qrels = load_dataset(qrel_path)
    else:
        raise ValueError("Dataset name or path to qrel file must be provided")
    
    #output/result from search
    results = json.load(open(result_file))
    
    
    #assign the labels from qrels to qrels_dict
    qrels_dict = json.load(open('qrels_dict.json'))

    #code for cleaning provided with the pipeline but has no impact on results
    
    # qrels_dict = clean_labels(qrels_dict, corpus_ids)
    # results = clean_result(qrels_dict, results)
    # write_results_to_json(results,'cleaned_labels.json')
    # check_corpus_ids(corpus_ids, qrels_dict, results)


    evaluation_results = evaluator.evaluate(qrels_dict, results, [1, 5, 10])
    ndcg = evaluation_results[0]
    _map = evaluation_results[1]
    recall = evaluation_results[2]
    precision = evaluation_results[3]


    
    return ndcg,recall,precision

@app.route('/create', methods=['POST'])
def create_index():
        endpoint = request.args.get('endpoint')
        version = request.args.get('version')
        service = request.args.get('service')
        index_name = request.args.get('index')
    
        query_payload = request.get_json()

         
        key = retrieve_key()
        # Create an instance of AzureSearch
        azure_search = AzureSearch(endpoint, key, version, service)

        # Create the index
        create_index_response = azure_search.create_index(index_name, query_payload)
        return create_index_response

@app.route('/index', methods=['POST'])
def index_documents():
    # Load dataset, transform, and save as Feather file\

    df = pd.read_json("hf://datasets/mteb/trec-covid/corpus.jsonl", lines=True)    
    new_column_names = {
        '_id': 'document_id',
        'title': 'title',
        'text': 'content'
    }
    new_df = select_and_rename_columns(df, new_column_names)
    new_df.to_feather('input.feather')
    print("DataFrame Columns:", df.columns)
    endpoint = request.args.get('endpoint')
    version = request.args.get('version')
    service = request.args.get('service')
    index_name = request.args.get('index')
    key = retrieve_key()


    # Index documents
    index_data(endpoint, key, version, service, index_name, 'input.feather', 'output.txt')
    return jsonify("Indexing documents is complete")


if __name__ == '__main__':
    # Run your Flask app
    app.run(debug=True)


    
   
    