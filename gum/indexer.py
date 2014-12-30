# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.base import ModelBase

from gum.utils import elasticsearch_connection
from gum.settings import ELASTICSEARCH_INDICES


class AlreadyRegistered(Exception):
    pass


class MappingType(object):

    # Index to apply this mapping type
    index = None

    def __init__(self, model):
        """Initialize a MappingType instance for a given
         `model`.

        :param model:
        :return:
        """
        self.model = model
        # If ``index`` is not defined, use settings
        if not self.index:
            self.index = ELASTICSEARCH_INDICES
        super(MappingType, self).__init__()

    def get_id(self, instance):
        """Gets the internal Elasticsearch id for instance."""
        return instance.pk

    def get_type(self):
        """Gets a strings that represents the type for the model."""
        return "%s_%s" % (
            self.model._meta.app_label, self.model._meta.model_name
        )

    def mapping(self):
        """Gets the mapping of a given model. Only uses the model class, not
        the instance.

        TODO: By the moment, it must be implemented by subclasses.
        """
        raise NotImplementedError()

    def document(self, instance):
        """Logic to convert an instance of the model into a document for indexing.

        TODO: By the moment, it must be implemented by subclasses.

        :param instance:
        :return:
        """
        raise NotImplementedError()

    def create_mapping_type(self):
        """Creates the Elasticsearch type."""
        es = elasticsearch_connection()
        print es.indices.put_mapping(
            index=self.index,
            doc_type=self.get_type(),
            body=self.mapping(),
            ignore=409
        )

    def index_document(self, instance):
        """Indexes an instance of the model.

        :param instance:
        :return:
        """
        es = elasticsearch_connection()
        es.index(
            index=self.index,
            doc_type=self.get_type(),
            id=self.get_id(instance),
            body=self.document(instance)
        )


class Indexer(object):
    """Allows to register a model with its mapper class."""

    def __init__(self):
        self._registry = {}

    def register(self, model_or_iterable, mapping_type_class=None):
        """Register a given model(s) with the given mapping type class.

        The model(s) should be Model classes, not instances.

        If a model is already registered, this will raise AlreadyRegistered.
        """
        if not mapping_type_class:
            mapping_type_class = MappingType
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model in self._registry:
                raise AlreadyRegistered('The model %s is already registered for indexing' % model.__name__)
            self._registry[model] = mapping_type_class(model)

    def get_registered_models(self):
        """Returns a list of all registered models, or just concrete
        registered models.
        """
        return [model for (model, mapping_type_class) in self._registry.items()]

    def initialize_index(self):
        """Creates and initialize index.

        TODO: Add settings configuration of the index.
        """
        es = elasticsearch_connection()
        es.indices.create(index=ELASTICSEARCH_INDICES, ignore=400)
        for _, mapping_type in self._registry.iteritems():
            if mapping_type.index != ELASTICSEARCH_INDICES:
                es.indices.create(index=mapping_type.index, ignore=400)

    def update_index(self):
        """Update index for all registered models."""
        for model, mapping_type in self._registry.iteritems():
            instances = model.objects.all()
            mapping_type.create_mapping_type()
            for instance in instances:
                mapping_type.index_document(instance)


# This global object represents the singleton indexer object
indexer = Indexer()