from time import sleep

import redis
from redis.commands.search.query import Query
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from sentence_transformers import SentenceTransformer
import numpy as np
import json

# Configuration
#REDIS_URL = "redis://default:blablabla@redis-<...>.rlrcp.com:<...>"
INDEX_NAME = "gabsIdxTest"
VECTOR_DIMENSION = 384
VECTOR_DATA_TYPE = "FLOAT32"
DISTANCE_METRIC = "COSINE"

# Connect to Redis
conn = redis.Redis.from_url(REDIS_URL, decode_responses=True)
print("Connected to Redis:", conn.ping())

# Load the model
model = SentenceTransformer('all-MiniLM-L6-v2')


def create_index():
    """ Create an index if it does not exist. """
    try:
        indexes = conn.execute_command("FT._LIST")
        if INDEX_NAME not in indexes:
            index_definition = IndexDefinition(prefix=["product-docs:"], index_type=IndexType.JSON)
            schema = [
                TextField("$.title", as_name="title"),
                VectorField("$.titleVector", "HNSW", {
                    "TYPE": VECTOR_DATA_TYPE, "DIM": VECTOR_DIMENSION, "DISTANCE_METRIC": DISTANCE_METRIC
                }, as_name="titleVector")
            ]
            conn.ft(INDEX_NAME).create_index(fields=schema, definition=index_definition)
            print("Index created.")
        else:
            print("Index already exists.")
    except Exception as e:
        print("Error creating index:", e)


def vectorize_question(question):
    """ Convert the question to a vector. """
    return model.encode(question).astype(np.float32).tobytes()


def knn_search(query_vector):
    """ Perform a KNN search using a vector. """
    try:
        #vector_bytes = np.array(query_vector, dtype=np.float32).tobytes()
        vector_bytes = query_vector
        q = Query("*=>[KNN 5 @titleVector $vec AS score]").sort_by("score", asc=True).dialect(2).paging(0, 10)
        results = conn.ft(INDEX_NAME).search(q, query_params={"vec": vector_bytes})
        print("KNN Search Results:")
        print_results(results)
    except Exception as e:
        print("Error during KNN search:", e)


def range_search(query_vector):
    """ Perform a vector range search. """
    try:
        #vector_bytes = np.array(query_vector, dtype=np.float32).tobytes()
        vector_bytes = query_vector
        radius = 3  # Adjust radius based on your use case
        q = Query("@titleVector:[VECTOR_RANGE $radius $vec]=>{$YIELD_DISTANCE_AS: score}") \
            .sort_by("score", asc=True) \
            .paging(0, 5) \
            .dialect(2)
        results = conn.ft(INDEX_NAME).search(q, query_params={"radius": radius, "vec": vector_bytes})
        print("Range Search Results:")
        print_results(results)
    except Exception as e:
        print("Error during range search:", e)


def print_results(results):
    """ Print search results. """
    for doc in results.docs:
        try:
            doc_data = json.loads(doc.json)
            title = doc_data.get('title', 'No title available')
        except json.JSONDecodeError:
            title = "Invalid JSON data"
        print(f"Document ID: {doc.id}")
        print(f"Title: {title}")
        print(f"Score: {doc.score}")
        print("----------------------")


def add_document(title):
    """ Add a document with a vectorized title to Redis. """
    try:
        title_vector = model.encode(title, convert_to_numpy=True).tolist()  # Convert the vector to a list of floats
        document_id = "product-docs:gabs"
        data = {
            "title": title,
            "titleVector": title_vector  # Store as a list of floats
        }
        conn.json().set(document_id, '$', data)
        print(f"Document added with ID: {document_id}")
    except Exception as e:
        print("Error adding document:", e)


def main():
    create_index()

    # Adding a document with the title "Camisa do Palmeiras Abel Ferreira"
    #add_document("Camisa do Palmeiras Abel Ferreira")
    #sleep(5)

    question = "Camisa do Palmeiras Abel Ferreira"
    question_vector = vectorize_question(question)

    # Perform KNN search
    knn_search(question_vector)
    print("\n" + "-" * 30 + "\n")  # Separator between searches

    # Perform range search
    range_search(question_vector)


if __name__ == "__main__":
    main()
