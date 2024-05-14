import redis
from rejson import Client, Path

# Configuration
JSON_DATA_FOR_DEMO = [
{"docId": "gf0gc9ag0d", "title": "Livro - Pocket - O tempo entre costuras - 2º edição", "titleVector": [-0.04301461577415466,<...>
]

# Connect to Redis using the ReJSON wrapper
rj = Client(host='redis-11424<...>', port=11424,
            password='nada', decode_responses=True)
print("Connected to Redis:", rj.ping())


def add_documents(json_list):
    """ Loop over the JSON list and add each document to Redis. """
    for item in json_list:
        doc_id = item['docId']
        data = {
            "title": item['title'],
            "titleVector": item['titleVector']  # Store as a list of floats
        }
        redis_key = f"product-docs:{doc_id}"
        try:
            rj.jsonset(redis_key, Path.rootPath(), data)
            print(f"Document added with ID: {redis_key}")
        except Exception as e:
            print(f"Failed to add document with ID {doc_id} to Redis: {e}")


if __name__ == "__main__":
    add_documents(JSON_DATA_FOR_DEMO)
