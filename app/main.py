import datetime
import os

import pymongo
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask.helpers import url_for
from flask_restful import Api, Resource, abort

import app.painters as painters
import app.utils as utils

load_dotenv()
akey = os.environ.get("API_KEY")
MONGODB_URI = os.environ.get("MONGODB_URI")
client = pymongo.MongoClient(MONGODB_URI)
db = client["Mint"]
app = Flask(__name__)
api = Api(app)


@app.errorhandler(401)
def custom_401(e):
    return "Access denied", 401

class Gelbooru(Resource):
    def get(self):
        query = request.args.get("q")
        raw_data = requests.get(f"https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=1000&tags={query}")
        return raw_data.json()
    
class Painters(Resource):
    def get(self):
        img_type = request.args.get("type")
        gid = request.args.get("gid")
        uid = int(request.args.get("uid"))
        pfp = request.args.get("asset")
        key = request.args.get("k")
        
        if not key or key != akey:
            abort(401)
            
        utils.image_check(pfp)
        guild_db = db[f"{gid}"]
        global_db = db["global"]
        user_guild = guild_db.find_one({"_id": uid})
        user_global = global_db.find_one({"_id": uid})
        lvl = user_guild["level"]
        dt = int(datetime.datetime.now().timestamp())
        
        if img_type == "level":
            painters.draw_lvlup(uid, lvl, dt)
            response = jsonify({
                "image": request.host_url + url_for("return_image", path=f"lvlups/{dt}.png")
            })
            
            return response
        elif img_type == "profile":
            name = request.args.get("name")
            place = utils.calculate_place(db, uid, gid)
            curr_exp = user_guild["exp"]
            next_lvl_exp = user_guild["nextLevelExp"]
            reps = user_global["rep"]
            desc = user_global["desc"]
            
            painters.draw_profile(uid, name, lvl, curr_exp, next_lvl_exp, place, reps, desc, dt)
            response = jsonify({
                "image": request.host_url + url_for("return_image", path=f"profiles/{dt}.png")
            })
            
            return response
        
@app.route("/image/<path:path>")
def return_image(path):
    return send_file(f"images/{path}", mimetype="image/gif")

     
api.add_resource(Gelbooru, "/api/gelbooru")
api.add_resource(Painters, "/api/draw")
