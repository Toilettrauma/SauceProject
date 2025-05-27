from index_controller import IndexingController
from containers.nhentai import NHentaiContainer
import os
import requests
import re
import sqlite3
import signal
import logging

db_results_filepath = "nhentai_results.db"
db_filepath = "images.db"
index_filepath = "images.index"

logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.root.addHandler(logging.FileHandler("downloader.log", mode="a"))
logging.basicConfig(level = logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class NHentaiResultDatabase:
	def __init__(self, filepath):
		self.db = sqlite3.connect(filepath)
		self.cur = self.db.cursor()

		self.cur.execute("""CREATE TABLE IF NOT EXISTS Downloaded (
			item_id TEXT NOT NULL,
			item_index INTEGER NOT NULL
		)""")
		self.cur.execute("""CREATE TABLE IF NOT EXISTS DownloadedPages (
			page_index INTEGER NOT NULL
		)""")
		self.db.commit()
	def save(self):
		self.db.commit()

	def add(self, id, index):
		self.cur.execute("""INSERT INTO Downloaded (item_id, item_index) VALUES (?, ?)""", [
			id,
			index
		])
	def add_page(self, page_index):
		self.cur.execute("""INSERT INTO DownloadedPages (page_index) VALUES (?)""", [
			page_index
		])
	def get_biggest_page(self):
		data = self.cur.execute("""SELECT page_index FROM DownloadedPages ORDER BY page_index DESC""").fetchone()
		if data is None:
			return 1
		return data[0]
	def search(self, id):
		data = self.cur.execute("""SELECT item_id, item_index FROM Downloaded WHERE item_id = ?""", [
			id
		]).fetchone()
		if data is None or len(data) < 2:
			return None
		return {
			"id": data[0],
			"index": data[1]
		}

class NHentaiSearcher:
	def __init__(self):
		self.results_database = NHentaiResultDatabase(db_results_filepath)
		self.index_controller = IndexingController()
		self.index_controller.load(db_filepath, index_filepath)
		self.exiting = False

		self.index_controller.set_log_level(logging.DEBUG)

	def save(self):
		self.index_controller.save(db_filepath, index_filepath)
		self.results_database.save()
	def stop(self):
		self.exiting = True

	def get_page_items(self, page_index):
		resp = requests.get(f"https://nhentai.net/?page={page_index}")
		if resp.status_code != 200:
			return []
		items = list(re.findall(r'href="/g/(\d+)/"', resp.text))
		return items

	def process_items(self, items):
		for item_id in items:
			if self.exiting:
				break
			if self.results_database.search(item_id) is not None:
				logger.warning(f"Trying to index duplicate {item_id}")
				continue

			indexed = self.index_controller.add(item_id, NHentaiContainer.get_name(), save_indexed_images = True)
			for idx in indexed:
				self.results_database.add(item_id, idx)
			logger.info(f"Indexed {item_id}")
			self.save()
			logger.info("Saved index and database")
	def run(self):
		page_index = self.results_database.get_biggest_page()
		while not self.exiting:
			items = self.get_page_items(page_index)
			if not items:
				logger.error(f"Empty page {page_index}")
				page_index += 1
				continue
			self.process_items(items)
			# previous function can interrupt if 'self.exiting' setted. Ignore such cases
			if not self.exiting:
				self.results_database.add_page(page_index)
				logger.info(f"Fully indexed page {page_index}")
				page_index += 1

if __name__ == "__main__":
	searcher = NHentaiSearcher()
	try:
		logger.info("Starting...")
		searcher.run()
	except KeyboardInterrupt as e:
		logger.info(f"Catched interrupt")
		# searcher.save()
	except Exception as e:
		# logger.critical(f"Catched {repr(e)}")
		raise Exception() from e
		# searcher.save()