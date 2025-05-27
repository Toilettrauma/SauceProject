from indexer import Indexer
from PIL import Image
import time

def main():
    indexer = Indexer()
    
    image = Image.open("test2.png")
    indexer.add_embeddings(indexer.encode_query_image(image))

    indexer.save_index()

    print("\nTesting image search...")
    image_results = indexer.search_by_image(image, k=10)
        
    for i, result in enumerate(image_results):
        if result.index < 0:
            continue
        print(f"{i+1}. {result.index} ({result.score:.3f})")

if __name__ == "__main__":
    main()