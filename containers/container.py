from typing import BinaryIO, Optional
from PIL import Image

class Container:
	@classmethod
	def get_name(cls) -> str:
		raise NotImplementedError()
	@classmethod
	def query_info(cls, id) -> dict:
		""" return {
			"description": ...,
			"count": ...
		}
		"""
		raise NotImplementedError()
	@classmethod
	def batch_get(cls, id, indexes, lazy = False) -> list[Optional[Image.Image]]:
		raise NotImplementedError()