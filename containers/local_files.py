from .container import Container
from typing import BinaryIO, Optional
from PIL import Image
import os

class LocalFilesContainer(Container):
	@classmethod
	def get_name(cls):
		return "LocalFilesContainer"
	@classmethod
	def query_info(cls, id) -> dict:
		filepath = id
		return {
			"count": 1, # just one file
			"description": None
		}
	@classmethod
	def batch_get(cls, id, indexes, lazy = False) -> list[Optional[Image.Image]]:
		filepath = id
		if not os.path.isfile(filepath):
			return None
		return [Image.open(filepath)]