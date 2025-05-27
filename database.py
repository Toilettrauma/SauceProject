import sqlite3

class Database:
	def __init__(self):
		self.db = None
		self.cur = None
	def load(self, filepath):
		self.db = sqlite3.connect(filepath)
		self.cur = self.db.cursor()

		self.cur.execute("""CREATE TABLE IF NOT EXISTS Items (
			idx INTEGER PRIMARY KEY,
			container TEXT NOT NULL,
			item_id TEXT NOT NULL,
			item_index INTEGER NOT NULL,
			description TEXT
		)""")
		self.db.commit()
	def save(self, filepath):
		# filepath unused
		self.db.commit()

	def add(self, index, container, item_id, item_index, description = ""):
		self.cur.execute("""INSERT INTO Items (idx, container, item_id, item_index, description) VALUES (?, ?, ?, ?, ?)""", [
			index,
			container,
			item_id,
			item_index,
			description
		])
		# self.db.commit()
	def get(self, index):
		data = self.cur.execute("""SELECT idx, container, item_id, item_index, description FROM Items WHERE idx = ?""", [
			index
		]).fetchone()
		if data is None:
			return None
		return dict(zip(["index", "container", "item_id", "item_index", "description"], data))
