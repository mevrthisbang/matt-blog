import glob
import json
import os
from datetime import datetime
import requests
from flask import Flask, render_template, redirect
from flask_env import MetaFlaskEnv
from rich_text_renderer.block_renderers import HeadingOneRenderer, HeadingTwoRenderer, HeadingThreeRenderer, \
    HeadingFourRenderer, HeadingFiveRenderer, HeadingSixRenderer, BlockQuoteRenderer, HyperlinkRenderer, \
    ListItemRenderer, OrderedListRenderer, UnorderedListRenderer, HrRenderer, \
    ParagraphRenderer, TableCellRenderer, TableRowRenderer, TableHeaderCellRenderer, \
    TableRenderer
from rich_text_renderer.document_renderers import DocumentRenderer
from rich_text_renderer.null_renderer import NullRenderer
from rich_text_renderer.text_renderers import TextRenderer, BoldRenderer, CodeRenderer, SuperscriptRenderer, \
    SubscriptRenderer, ItalicRenderer, UnderlineRenderer

from custom_renderer import CustomAssetBlockRenderer


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

@app.template_filter()
def format_datetime(value, format="%d %b, %Y"):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").strftime(format)

@app.route('/')
def index():  # put application's code here
    # welcome_blogs = client.entries({"content_type": "blogPage", "fields.isWelcomePost": "true", "include": 10})
    welcome_blogs_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("welcome-post")]}, headers=headers)
    welcome_blogs = json.loads(welcome_blogs_response.text)["data"]["blogPageCollection"]["items"]
    all_blogs_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("all-blogs")]}, headers=headers)
    all_blogs = json.loads(all_blogs_response.text)["data"]["blogPageCollection"]["items"]
    return render_template("index.html", welcome_blogs=welcome_blogs, all_blogs=all_blogs)

@app.route('/assets/<string:id>', methods=["GET"])
def get_asset(id):
    asset_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("asset")], "variables": {"id": id}}, headers=headers)
    assest = json.loads(asset_response.text)["data"]["asset"]["url"]
    return redirect(assest)
@app.route('/blog/<string:slug>', methods=["GET"])
def get_blog(slug):
    blog_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("single-blog")], "variables": {"slug": slug}}, headers=headers)
    blog = json.loads(blog_response.text)["data"]["blogPageCollection"]["items"][0]
    renderer = DocumentRenderer({
        "document": DocumentRenderer,
        "heading-1": HeadingOneRenderer,
        "heading-2": HeadingTwoRenderer,
        "heading-3": HeadingThreeRenderer,
        "heading-4": HeadingFourRenderer,
        "heading-5": HeadingFiveRenderer,
        "heading-6": HeadingSixRenderer,
        "blockquote": BlockQuoteRenderer,
        "hyperlink": HyperlinkRenderer,
        "list-item": ListItemRenderer,
        "ordered-list": OrderedListRenderer,
        "unordered-list": UnorderedListRenderer,
        "hr": HrRenderer,
        "embedded-asset-block": CustomAssetBlockRenderer,
        "paragraph": ParagraphRenderer,
        "text": TextRenderer,
        "bold": BoldRenderer,
        "code": CodeRenderer,
        "superscript": SuperscriptRenderer,
        "subscript": SubscriptRenderer,
        "italic": ItalicRenderer,
        "underline": UnderlineRenderer,
        "table-cell": TableCellRenderer,
        "table-row": TableRowRenderer,
        "table-header-cell": TableHeaderCellRenderer,
        "table": TableRenderer,
        None: NullRenderer,
    })
    rendered_content = renderer.render(blog["body"]["json"])
    return render_template("blog.html", blog=blog, rendered_content=rendered_content)
