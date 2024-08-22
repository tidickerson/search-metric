import json
from mteb.evaluation.evaluators import RetrievalEvaluator
import pandas as pd

evaluator = RetrievalEvaluator()


def evaluate(results, qrels_dict):
    
    evaluation_results = evaluator.evaluate(qrels_dict, results, [1, 5, 10])
    ndcg = evaluation_results[0]
    _map = evaluation_results[1]
    recall = evaluation_results[2]
    precision = evaluation_results[3]

    return ndcg,recall,precision

#session param
def calculate_metrics(query_id,query_term,query_payload,ss,index,qrels_dict):
    payload = query_payload.copy()
    #assign to the values of the provided fields which will be null 
    payload['query_id'] = query_id

    payload_str = json.dumps(payload)
    payload_str = payload_str.replace("#search#", query_term)
    payload = json.loads(payload_str)
    
    # Wrap in a list to prep for dataframe
    query_payload_list = [payload]
    #turn to df
    df_queries = pd.DataFrame(query_payload_list)
    # Set 'query_id' as the index
    dict_expanded = df_queries.set_index('query_id').to_dict(orient='index')

    # Get search results for each search term
    results = ss.get_search_results(dict_expanded, index)
    

    #evaluate the information
    ndcg,recall,precision = evaluate(results,qrels_dict)

    ndcg1 = ndcg['NDCG@1']
    ndcg5 = ndcg['NDCG@5']
    ndcg10 = ndcg['NDCG@10']
        
    precision1 = precision['P@1']
    precision5 = precision['P@5']
    precision10 = precision['P@10']
    
    return ndcg1,ndcg5,ndcg10,precision1,precision5,precision10