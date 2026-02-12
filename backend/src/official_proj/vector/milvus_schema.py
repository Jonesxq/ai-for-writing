from pymilvus import (
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)

COLLECTION_NAME = "plot_memory"


def create_plot_memory_collection(drop_if_exists: bool = False):
    if utility.has_collection(COLLECTION_NAME):
        if drop_if_exists:
            utility.drop_collection(COLLECTION_NAME)
        else:
            return Collection(COLLECTION_NAME)

    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            max_length=36,
            is_primary=True
        ),
        FieldSchema(
            name="novel_id",
            dtype=DataType.VARCHAR,
            max_length=36
        ),
        FieldSchema(
            name="chapter_number",
            dtype=DataType.INT64
        ),
        FieldSchema(
            name="content",
            dtype=DataType.VARCHAR,
            max_length=2048
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=768
        ),
        FieldSchema(
            name="created_at",
            dtype=DataType.INT64
        )
    ]

    schema = CollectionSchema(
        fields,
        description="Novel plot semantic memory"
    )

    collection = Collection(
        name=COLLECTION_NAME,
        schema=schema
    )

    collection.create_index(
        field_name="embedding",
        index_params={
            "index_type": "HNSW",
            "metric_type": "IP",
            "params": {
                "M": 8,
                "efConstruction": 64
            }
        }
    )

    return collection

