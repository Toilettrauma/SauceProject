from database import Database
from indexer import Indexer, IndexerResult
from containers import all_containers
from PIL import Image
import os
import logging

class IndexingController:
	def __init__(self):
		self.indexer = Indexer()
		self.database = Database()
		self.containers = all_containers

		self.logger = logging.getLogger(__name__)
	def set_log_level(self, log_level = logging.NOTSET):
		self.logger.setLevel(log_level)
	def load(self, db_filepath = "images.db", index_filepath="images.index"):
		self.indexer.load_index(index_filepath)
		self.database.load(db_filepath)
	def save(self, db_filepath = "images.db", index_filepath="images.index"):
		self.indexer.save_index(index_filepath)
		self.database.save(db_filepath)

	def get_container(self, container_name):
		for container in self.containers:
			if container.get_name() == container_name:
				return container
		return None
	def encode_and_index(self, image, container_name, item_id, item_index, item_desc, save_path = None) -> int:
		embeddings = self.indexer.encode_query_image(image)
		indexer_index = self.indexer.add_embeddings(embeddings)
		self.database.add(
			indexer_index,
			container_name,
			item_id,
			item_index,
			item_desc
		)
		if save_path is not None:
			filepath = os.path.join(save_path, str(item_index) + ".png")
			image.save(filepath)
		return indexer_index

	def add(self, id, container_name, save_indexed_images = False) -> list[int]:
		# query all info
		container = self.get_container(container_name)
		info = container.query_info(id)
		item_count = info.get("count")
		item_desc = info.get("description")
		if item_desc is None:
			item_desc = ""

		# get all images
		indexes = list(range(item_count))
		images = container.batch_get(id, indexes, lazy = True)

		# encode and add to index all images
		indexed_indexes = []
		save_path = None
		if save_indexed_images:
			save_path = os.path.join(
				"index_root",
				container_name,
				id.replace(":", "_").replace(".", "_").replace("\\", "")
			)
			os.makedirs(save_path, exist_ok=True)
		for i, image in enumerate(images):
			idx = indexes[i]
			if image is None:
				self.logger.error(f"Failed to get image ({id}/{idx})")
				continue
			self.encode_and_index(image, container_name, id, idx, item_desc, save_path = save_path)
			indexed_indexes.append(idx)
			self.logger.debug(f"Indexed {id}/{idx}")
		return indexed_indexes

	def get(self, id, index, container_name):
		# query all info
		container = self.get_container(container_name)
		info = container.query_info(id)
		item_count = info.get("count")
		if item_count <= index:
			return None

		# if cached indexed grad that
		indexed_filepath = os.path.join(
			"index_root",
			container_name,
			id.replace(":", "_").replace(".", "_").replace("\\", ""),
			str(index) + ".png"
		)
		if os.path.isfile(indexed_filepath):
			self.logger.debug(f"Reading cached {id}/{index}")
			return Image.open(indexed_filepath)

		image = container.batch_get(id, [index])[0]
		self.logger.debug(f"Downloaded image {id}/{index}")
		return image

	def get_info(self, index):
		return self.database.get(index)
	def search(self, image : Image.Image, k=10) -> list[IndexerResult]:
		return self.indexer.search_by_image(image, k=k)





