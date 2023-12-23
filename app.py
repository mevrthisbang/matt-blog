import glob
import json
import os
import uuid
from datetime import datetime

import contentful_management
import requests
from contentful_management import Link
from flask import Flask, render_template, redirect, request
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
    SPACE_ID = "oexxx"
    ACCESS_TOKEN = "Dxxx"
    MANAGEMENT_TOKEN = "Cxxxx"
    ENVIRONMENT_ID = "xxxx"

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

management_client = contentful_management.Client(app.config['MANAGEMENT_TOKEN'])
environment = management_client.environments(app.config["SPACE_ID"]).find(app.config["ENVIRONMENT_ID"])

def get_categories():
    categories_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("categories")]},
                                        headers=headers)
    categories = json.loads(categories_response.text)["data"]["categoryCollection"]["items"]
    return categories

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
    categories = get_categories()
    return render_template("index.html", welcome_blogs=welcome_blogs, all_blogs=all_blogs, categories=categories)

@app.route('/assets/<string:id>', methods=["GET"])
def get_asset(id):
    asset_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("asset")], "variables": {"id": id}}, headers=headers)
    asset = json.loads(asset_response.text)["data"]["asset"]["url"]
    return redirect(asset)


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
    categories = get_categories()
    return render_template("blog.html", blog=blog, rendered_content=rendered_content, comments=blog["commentsCollection"]["items"], categories=categories)


@app.route('/post-comment', methods=["POST"])
def add_comment():
    comment_attributes = {
        'content_type_id': 'comment',
        'fields': {
            'content': {
                'en-US': request.form.get("content")
            },
            'createrName': {
                'en-US': request.form.get("name")
            }
        }
    }
    new_comment = environment.entries().create(
        str(uuid.uuid4()),
        comment_attributes
    )
    new_comment.publish()
    blog_entry = environment.entries().find(request.form.get("blog_id"))
    new_comment_link = Link({
        "sys": {
            "id": new_comment.sys["id"],
            "linkType": "Entry",
            "type": "Link"
        }})
    try:
        blog_comments = blog_entry.fields('en-US')['comments']
    except:
        blog_comments = []
    blog_comments.append(new_comment_link)
    blog_entry.comments = blog_comments
    blog_entry.save()
    blog_entry.publish()
    blog_comments_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("comments-of-blog")],
                                                  "variables": {"id": request.form.get("blog_id")}}, headers=headers)
    comments = json.loads(blog_comments_response.text)["data"]["blogPageCollection"]["items"][0]["commentsCollection"]["items"]
    return render_template("comment-section.html", comments=comments)

@app.route('/blog/category/<string:slug>', methods=["GET"])
def get_blog_by_category(slug):
    category = None
    all_blogs = None
    if slug == "#":
        all_blogs_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("all-blogs")]},
                                           headers=headers)
        all_blogs = json.loads(all_blogs_response.text)["data"]["blogPageCollection"]["items"]
    else:
        category_response = requests.post(endpoint, json={"query": graphql["{}.graphql".format("category")],
                                                      "variables": {"slug": slug}}, headers=headers)
        category = json.loads(category_response.text)["data"]["categoryCollection"]["items"][0]
    categories = get_categories()
    return render_template("category.html", category=category, blogs=all_blogs, categories=categories)