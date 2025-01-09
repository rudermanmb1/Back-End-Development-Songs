from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=["GET"])
def health():
    return {"status":"OK"}

@app.route("/count")
def count():
    """return length of data"""
    count = db.songs.count_documents({})

    return {"count": count}, 200

@app.route("/song")
def song():
    song_set = db.songs.find({})
    list_of_songs = json.loads(json_util.dumps(song_set))
    return {"songs": list_of_songs}, 200

@app.route("/song/<int:id>", methods = ["GET"])
def get_song_by_id(id):
    song_of_note = None
    song_of_note = db.songs.find_one({'id':id})
    if not song_of_note:
        return {"message": f"song with id {id} not found"}, 404
    
    song_of_note = json_util.dumps(song_of_note)
    return song_of_note,200

@app.route("/song", methods = ["POST"])
def create_song():
    song = request.json
    
    resp_id = json_util.dumps(song["id"])
    resp_id = int(resp_id)
    song_of_note = db.songs.find_one({'id':resp_id})
    if song_of_note is not None:
        return {"Message": f"song with id {resp_id} already present"}, 302
    
    result = db.songs.insert_one(song)
    return {"inserted id":json.loads(json_util.dumps(result.inserted_id))}, 201

@app.route("/song/<int:id>", methods = ["PUT"])
def update_song(id):
    song = request.json
    song_of_note = db.songs.find_one({'id':id})
    if song_of_note is not None:
        changes = {"$set":song}
        result = db.songs.update_one({'id':id},changes)
        if result.modified_count == 0:
            return {"message":"song found, but nothing updated"},200

        return json_util.dumps(db.songs.find_one(result.upserted_id)), 201
    
    return {"message": "song not found"},404

@app.route("/song/<int:id>", methods = ["DELETE"])
def delete_song(id):
    result = db.songs.delete_one({"id":id})
    if result.deleted_count == 0:
        return {"message": "song not found"}, 404

    return "", 204

