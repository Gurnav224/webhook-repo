from flask  import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

# mongodb setup
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['webhook_db']
collection = db['events']




app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    event_type = request.headers.get('X-GitHub-Event')
    event = {}

    if data is None:
        return jsonify({'error': 'Invalid or missing JSON'}), 400
    

    if event_type == 'push':
        event['action'] = 'PUSH'
        event['request_id'] = data['head_commit']['id']
        event['author'] = data['pusher']['name']
        event['from_branch'] = ''
        event['to_branch'] = data['ref'].split('/')[-1]
        event['timestamp'] = data['head_commit']['timestamp']

    elif event_type == 'pull_request':
        pr = data['pull_request']
        event['request_id'] =  str(pr['id'])
        event['author'] = pr['user']['login']
        event['from_branch'] = pr['head']['ref']
        event['to_branch'] = pr['base']['ref']
        event['timestamp'] = data['head_commit']['timestamp']

        if pr.get('merged'):
            event['action'] = 'MERGE'
        else:
            event['action'] = 'PULL_REQUEST'

    else:
        return '', 204
    
 #   print('mongodb create event', event)

    collection.insert_one(event)
    return jsonify({'status': 'received', 'event': event_type}), 201

@app.route('/events',methods=['GET'])
def get_events():
    events = list(collection.find({},{'_id':0}))


    return jsonify(events)
    
if __name__ == '__main__':
    app.run(debug=True)
