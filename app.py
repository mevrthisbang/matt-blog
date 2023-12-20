import glob
import json
import os

import requests
from flask import Flask, render_template
from flask_env import MetaFlaskEnv
import contentful

class Configuration(metaclass=MetaFlaskEnv):
    SPACE_ID = "oesxxxx"
    ACCESS_TOKEN = "xxxxx"


app = Flask(__name__)
app.config.from_object(Configuration)

endpoint = "https://graphql.contentful.com/content/v1/spaces/{}".format(app.config["SPACE_ID"])
headers = {"Authorization": "Bearer {}".format(app.config["ACCESS_TOKEN"])}

graphql = {}
graphql_folder = os.getcwd() + "/graphql"
list_graphql_files = glob.glob(os.path.join(graphql_folder, '*.graphql'))
for filename in list_graphql_files:
    with open(os.path.join(graphql_folder, filename), 'r') as f:
        graphql[os.path.basename(filename)] = f.read()


@app.route('/')
def index():  # put application's code here
    # welcome_blogs = client.entries({"content_type": "blogPage", "fields.isWelcomePost": "true", "include": 10})
    welcome_blogs_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("welcome-post")]}, headers=headers)
    welcome_blogs = json.loads(welcome_blogs_response.text)["data"]["blogPageCollection"]["items"]
    all_blogs_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("all-blogs")]}, headers=headers)
    all_blogs = json.loads(all_blogs_response.text)["data"]["blogPageCollection"]["items"]
    return render_template("index.html", welcome_blogs=welcome_blogs, all_blogs=all_blogs)
