import json
import requests
from flask import Flask, request, jsonify
import time
from concurrent.futures import ThreadPoolExecutor,as_completed
from flask_cors import CORS
from azs import retrieve_key,AzureSearch
from evaluation import calculate_metrics
app = Flask(__name__)
CORS(app)


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
    
    #can remove this code if need be, used to measure processing time of all queries
    #grab key to not expose secret
    key = retrieve_key()

    # Create an instance of AzureSearch
    ss = AzureSearch(endpoint, key, version, service)
    qrels_dict = json.load(open('qrels_dict.json'))
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    num_workers = config['max_workers']
    metrics_list = []
    for payload in query_payload["requests"]:
        template = payload
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(calculate_metrics, query_id, query_term, template, ss, index, qrels_dict): query_id for query_id, query_term in query_list.items()}
            for future in as_completed(futures):
                query_id = futures[future]
                try:
                    n1,n5,n10,p1,p5,p10 = future.result()
                    # Cumulate the scores for each metric
                    ndcg1 += n1
                    ndcg5 += n5
                    ndcg10 += n10
                        
                    precision1 += p1
                    precision5 += p5
                    precision10 += p10
                        
                except Exception as e:
                    print(f"Error processing query {query_id}: {e}")

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

        metrics = {
            "ndcg": ndcg,
            "precision": precision
        }
        print(metrics)
        metrics_list.append(metrics)
    return jsonify(metrics_list)

#endpoint to upload ground truth values
@app.route('/upload_truth', methods=['POST'])
def upload_ground_truth():
    ground_truth = request.get_json()
    write_results_to_json(ground_truth,'qrels_dict.json')
    return ("Upload")


def write_results_to_json(results, output_filename):
    with open(output_filename, 'w') as json_file:
        json.dump(results, json_file, indent=4)

if __name__ == '__main__':
    # Run your Flask app
    app.run(debug=True)
