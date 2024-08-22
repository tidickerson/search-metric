Search Metrics Tool / Project Sherlock


Overview
To combat the issue of customers not being able to acertain whether their search systems are relevant or not, the Search Metrics Tool seeks to give customers a way to get quantifiable metrics on how relevant their search system and queries are. Given 3 points of data, ground truth labels, a query term list, and a search template, this tool can give users the nDCG and precision values for given search template(s)

How It Works
From the frontend, the user is able to upload ground truth and search templates, which is used by the backend. The Search Metrics Tool takes in data given by the user. With our query term list, we populate the search template(s) and send the templates to Azure Search. Using MTEB Retrieval Evaluator, we can take the ground truth values and the results from our search and get the metrics at the given k values. We take the average for each search template and then display on the frontend.

Data

Search Template / Payload:
The search template will be expected in the standard Azure Search format, as a list of dictionaries. This is so that we can handle multiple templates in one request.

{
  "requests": [
    	{ 
			 "search": "#search#", 
			 "queryType": "semantic", 
			 "searchFields": "title,content", 
			 "searchMode": "any", 
			 "select": "document_id,content", 	
			 "semanticConfiguration": "default" 
	 },
	{ 
			 "search": "#search#", 
			 "queryType": "simple", 
			 "searchFields": "title", 
			 "searchMode": "any", 
			 "select": "document_id,content", 	
			 "semanticConfiguration": "default" 
	 } 
  ]
}

The field with the value #search# will be populated with the query terms given to the program in queries.json


Query/Search Terms - listed in queries.json, contains the list of queries to populate search template. Here is an example of the format:

{
    "1": <query 1>,
    "2": <query 2>,
    "3": <query 3>
}
To get the average nDCG and precision scores, we iterate through a list of provided queries, populate the given search template with the query terms, and average out the scores.

Ground Truth Values:
Ground truth values are expected in the same format as the response from Azure Search after executing a query. The format of these values are expected as follows 
{
    "1": {
        "005b2j4b": 2,
        "00fmeepz": 1,
        "g7dhmyyo": 2,
        "0194oljo": 1,
        "021q9884": 1,
        "02f0opkr": 1,
        "047xpt2c": 0,
        "04ftw7k9": 0,
        "pl9ht0d0": 0,
        "05vx82oo": 0
    },
    "2": {
        "01goni72": 2,
        "01yc7lzk": 0,
        "02cy1s8x": 0,
        "02f0opkr": 0,
        "vprjbzw8": 2,
        "03id5o2g": 0,
        "03s9spbi": 2,
        "04awj06g": 2,
        "04rbtmmi": 2,
        "084o1dmp": 0
    }
}
Where "1" and "2" represent the query id and the inner elements represent a document id and its associated relevance score from 0-2. 
Note: the 0-2 scale is specific to this dataset's ground truth values. Scales tend to differ based on datasets used.

Dependencies
The necessary dependencies are located in requirements.txt. 'python install_libraries.py' will run a script to install all the necessary dependencies to run this program.

Configuration Files
There are two configuration files. The first, config.json is for our secret management and to indicate number of workers for the ThreadPoolExecutor. To retrieve the key, enter your key vault url and secret name corresponding to your API key in the key_vault_url and secret_name fields respectively. max_workers indicates the number of workers/processes you would like to run.
The azs_config json file contains parameters related to the creation of your Azure Search instance. Needed fields are endpoint, api version, service name, index name

How To Use:
To run the frontend, enter npm start into the terminal from the sherlock-ui folder
To run the backend, enter 'waitress-serve --listen=0.0.0.0:5000 controller:app' from the project-sherlock-demo folder
Follow the UI and enter your ground truth values and submit. Submit your query payload and hit Calculate Metrics

