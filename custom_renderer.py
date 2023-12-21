from flask import url_for
from rich_text_renderer.base_node_renderer import BaseNodeRenderer


class CustomAssetBlockRenderer(BaseNodeRenderer):
    IMAGE_HTML = '<img src="{0}"/>'
    def render(self, node):
        entry = node['data']['target']

        return self.__class__.IMAGE_HTML.format(url_for("get_asset", id=entry["sys"]["id"]))