===
Gum
===

Gum is a Django for integrate Elasticsearch with Django.

Quick start
-----------

1. Install using pip::

    pip install -e git+git@github.com:marcosgabarda/django-gum.git@master#egg=django-gum

2. Add "gum" to your INSTALLED_APPS settings like this::

       INSTALLED_APPS = (
           ...
           'gum',
       )

3. Add Elasticsearch configuration to your settings like this::

    GUM_ELASTICSEARCH_URLS = ["http://127.0.0.1:9200/"]
    GUM_ELASTICSEARCH_INDEX = ".gum-tests"

4. Create an index.py in your app, with a content like this::

    from gum.indexer import MappingType, indexer

    class PostMappingType(MappingType):

        def document(self, instance):
            tags_text = " ".join(map(lambda x: x.label, instance.tags.all()))
            return {
                "title": instance.title,
                "content": instance.content,
                "text": "{} {} {}".format(instance.title, instance.content, tags_text)
            }

        def mapping(self):
            return {
                "properties": {
                    "title": {
                        "type": "string",
                        "store": True,
                    },
                    "content": {
                        "type": "string",
                        "store": True,
                    },
                    "text": {
                        "type": "string",
                        "store": True,
                    }
                }
            }

    indexer.register(Post, PostMappingType)

5. Update Elasticsearch index::

    ./manage.py update_index

Searching
---------

You can perform Elasticsearch searches (accessing ``_search`` method) using ``elasticseaech`` model
attribute::

    response = Post.elasticsearch.search(body={
        "query": {
            "match_all": {}
        }
    })
