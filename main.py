from index_controller import IndexingController
from PIL import Image
from argparse import ArgumentParser
import os
import logging
import matplotlib.pyplot as plt

db_filepath = "images.db"
index_filepath = "images.index"

logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level = logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def show_plot_images(image, similar_images, scores):
	fig = plt.figure()
	ax = fig.subplots(4, 3)

	axis_query = ax[0][1]
	axis_query.set_title("query")
	axis_query.imshow(image)
	for i, (axis, im) in enumerate(zip(ax[1:].flatten(), similar_images)):
		axis.set_title(f"score: {scores[i]:.3f}")
		axis.imshow(im)

	for axis in ax.flatten():
		axis.axis("off")
	plt.show()
def get_and_show_images(indexing, base_image, results):
	images = []
	scores = []
	for res in results:
		info = indexing.get_info(res.index)
		id = info["item_id"]
		index = info["item_index"]
		container_name = info["container"]

		images.append(indexing.get(id, index, container_name))
		scores.append(res.score)

	show_plot_images(base_image, images, scores)
def show_results(indexing, results):
	for i, result in enumerate(results):
		if result.index < 0:
			continue
		db_info = indexing.get_info(result.index)
		if db_info is None:
			print(f"Failed to get info for {result.index}")
			continue
		print(f'{i + 1}: {db_info.get("item_id", "?")}/{db_info.get("item_index", "?")} (score: {result.score:.3f})')


def query_image(image_filepath, show_plot = False):
	indexing_controller = IndexingController()
	indexing_controller.load(db_filepath, index_filepath)
	# indexing_controller.set_log_level(logging.DEBUG)
	image = Image.open(image_filepath)

	results = indexing_controller.search(image, k=10)
	show_results(indexing_controller, results)
	if show_plot:
		get_and_show_images(indexing_controller, image, results)


def add_dir_images(directory):
	indexing_controller = IndexingController()
	indexing_controller.load(db_filepath, index_filepath)
	for root, _, filenames in os.walk(directory):
		for filename in filenames:
			filepath = os.path.join(root, filename)
			indexing_controller.add(filepath, "LocalFilesContainer")
			print(f"Added {filepath} to index")

	indexing_controller.save(db_filepath, index_filepath)

def main():
	parser = ArgumentParser()
	parser.add_argument("-q", help="query by image", type=str, metavar="image")
	parser.add_argument("-a", help="add all directory images to index", type=str, metavar="dir")
	parser.add_argument("-p", help="show plot in query", action="store_true", default=False)
	args = parser.parse_args()
	if args.q:
		query_image(args.q, args.p)
	if args.a:
		add_dir_images(args.a)

if __name__ == "__main__":
	main()