from .container import Container
from typing import BinaryIO, Optional
from PIL import Image
import requests
import re
import json
from io import BytesIO

class NHentaiContainer(Container):
	QUERY_URL = "https://nhentai.net/g/{id}"
	DIRECT_IMAGE_URL = "https://{subdomain}.nhentai.net/galleries/{id}/{index}.{ext}"
	TYPES = {
		"w": "webp",
		"j": "jpg",
		"g": "gif",
		"p": "png"
	}

	@classmethod
	def query_gallery_info(cls, id):
		resp = requests.get(cls.QUERY_URL.format(id = id))
		if resp.status_code != 200:
			return None
		info_json_match = re.search(r"JSON\.parse\(\"(.*)\"\)", resp.text)
		if info_json_match is None:
			return None
		json_string = info_json_match.group(1).encode().decode('unicode-escape')
		info_json = json.loads(json_string)
		return info_json
	@classmethod
	def types_from_info(cls, info_json):
		pages = info_json.get("images", {}).get("pages", [])
		if not pages:
			return None

		results = []
		for page in pages:
			results.append(cls.TYPES.get(page.get("t")))
		return results
	@classmethod
	def iterate_images(cls, media_id, indexes, image_types):
		for idx in indexes:
			if len(image_types) <= idx:
				yield None
				continue
			resp = requests.get(cls.DIRECT_IMAGE_URL.format(
				subdomain ="i1",
				id = media_id,
				index = idx + 1,
				ext = image_types[idx]
			))
			if resp.status_code != 200:
				yield None
			else:
				yield Image.open(BytesIO(resp.content))

	@classmethod
	def get_name(cls):
		return "NHentaiContainer"
	@classmethod
	def query_info(cls, id) -> dict:
		info_json = cls.query_gallery_info(id)
		return {
			"count": info_json.get("num_pages", 0),
			"description": info_json.get("title", {}).get("english")
		}
	@classmethod
	def batch_get(cls, id, indexes, lazy = False) -> list[Optional[Image.Image]]:
		info_json = cls.query_gallery_info(id)
		image_types = cls.types_from_info(info_json)
		media_id = info_json.get("media_id")
		if media_id is None:
			return [None] * len(indexes)

		images_iterator = cls.iterate_images(media_id, indexes, image_types)
		return images_iterator if lazy else list(images_iterator)