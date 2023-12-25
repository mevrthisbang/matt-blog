import glob
import json
import math
import os
import uuid
from datetime import datetime
from functools import wraps

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
    PAGE_SIZE = "5"

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

def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(str(e))
            return render_template("errors.html")
    return wrapper

def call_graph_api(graphql_query, variables=None):
    data = {
        "query": graphql["{}.graphql".format(graphql_query)]
    }
    if variables:
        data["variables"] = variables
    result = requests.post(endpoint, json=data, headers=headers)
    response_data = json.loads(result.text)
    return response_data


def get_categories():
    categories_response = call_graph_api("categories")
    categories = categories_response["data"]["categoryCollection"]["items"]
    return categories


@app.template_filter()
def format_datetime(value, format="%d %b, %Y"):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").strftime(format)


@app.template_filter()
def remove_keys(query_params_dict, keys):
    return {x: query_params_dict[x] for x in query_params_dict if x not in keys}


@app.route('/')
@error_handler
def index():  # put application's code here
    page_size = int(app.config["PAGE_SIZE"])
    page = request.args.get("page")
    if page:
        page = int(page)
        offset = (page - 1) * page_size
    else:
        page = 1
        offset = 0
    welcome_blogs_response = call_graph_api("welcome-post")
    welcome_blogs = welcome_blogs_response["data"]["blogPageCollection"]["items"]
    all_blogs_response = call_graph_api("all-blogs", {"limit": page_size, "skip": offset})
    all_blogs = all_blogs_response["data"]["blogPageCollection"]
    all_blogs["total_page"] = math.ceil(all_blogs["total"] / page_size)
    all_blogs["current_page"] = page
    categories = get_categories()
    return render_template("index.html", welcome_blogs=welcome_blogs, all_blogs=all_blogs, categories=categories)


@app.route('/assets/<string:id>', methods=["GET"])
def get_asset(id):
    asset_response = call_graph_api("asset", {"id": id})
    asset = asset_response["data"]["asset"]["url"]
    return redirect(asset)


@app.route('/blog/<string:slug>', methods=["GET"])
@error_handler
def get_blog(slug):
    blog_response = call_graph_api("single-blog", {"slug": slug})
    blog = blog_response["data"]["blogPageCollection"]["items"][0]
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
    return render_template("blog.html", blog=blog, rendered_content=rendered_content,
                           comments=blog["commentsCollection"]["items"], categories=categories)


@app.route('/post-comment', methods=["POST"])
def add_comment():
    content = request.form.get("content")
    name = request.form.get("name")
    blog_id = request.form.get("blog_id")
    if not content or not name or not blog_id:
        return None
    comment_attributes = {
        'content_type_id': 'comment',
        'fields': {
            'content': {
                'en-US': content
            },
            'createrName': {
                'en-US': name
            }
        }
    }
    new_comment = environment.entries().create(
        str(uuid.uuid4()),
        comment_attributes
    )
    new_comment.publish()
    blog_entry = environment.entries().find(blog_id)
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
    blog_comments_response = call_graph_api("comments-of-blog", {"id": blog_id})
    comments = blog_comments_response["data"]["blogPageCollection"]["items"][0]["commentsCollection"]["items"]
    return render_template("comment-section.html", comments=comments)


@app.route('/blog/search', methods=["GET"])
@error_handler
def search_blogs():
    category = request.args.get('category')
    tag = request.args.get("tag")
    keyword = request.args.get("keyword")
    page_size = int(app.config["PAGE_SIZE"])
    page = request.args.get("page")
    if page:
        page = int(page)
        offset = (page - 1) * page_size
    else:
        page = 1
        offset = 0
    categories = get_categories()
    if category:
        category_response = call_graph_api("category", {"slug": category, "limit": page_size, "skip": offset})
        blogs_by_category = category_response["data"]["categoryCollection"]["items"][0]
        blogs_by_category["linkedFrom"]["blogPageCollection"]["total_page"] = math.ceil(
            blogs_by_category["linkedFrom"]["blogPageCollection"]["total"] / page_size)
        blogs_by_category["linkedFrom"]["blogPageCollection"]["current_page"] = page
        return render_template("search_blogs.html", blogs_by_category=blogs_by_category, categories=categories)
    if tag:
        tag_response = call_graph_api("tag", {"slug": tag, "limit": page_size, "skip": offset})
        blogs_by_tag = tag_response["data"]["tagCollection"]["items"][0]
        blogs_by_tag["linkedFrom"]["blogPageCollection"]["total_page"] = math.ceil(
            blogs_by_tag["linkedFrom"]["blogPageCollection"]["total"] / page_size)
        blogs_by_tag["linkedFrom"]["blogPageCollection"]["current_page"] = page
        return render_template("search_blogs.html", blogs_by_tag=blogs_by_tag, categories=categories)
    if keyword:
        search_response = call_graph_api("search_blogs", {"keyword": keyword, "limit": page_size,
                                                                      "skip": offset})
        blogs_by_keyword = search_response["data"]["blogPageCollection"]
        blogs_by_keyword["total_page"] = math.ceil(
            blogs_by_keyword["total"] / page_size)
        blogs_by_keyword["current_page"] = page
        return render_template("search_blogs.html", blogs_by_keyword=blogs_by_keyword, keyword=keyword,
                               categories=categories)

    all_blogs_response = call_graph_api("all-blogs", {"limit": page_size, "skip": offset})
    all_blogs = all_blogs_response["data"]["blogPageCollection"]
    all_blogs["total_page"] = math.ceil(all_blogs["total"] / page_size)
    all_blogs["current_page"] = page
    return render_template("search_blogs.html", all_blogs=all_blogs, categories=categories)
