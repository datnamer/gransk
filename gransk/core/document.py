#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import time
import hashlib
import re

from six import text_type as unicode


class Entities(object):
  """Class for a set of entities found within documents."""

  def __init__(self):
    self.obj = {}
    self.keys = []

  def add(self, offset, entity_type, entity_value):
    """
    Adds a found entity to list. The `offset` parameter is used as key, so
    only one entity can start at the given offset.

    :param offset: Offset in extracted text where the found entity starts.
    :param entity_type: The type of entity that is found.
    :param entity_value: The found entity.
    :type start: ``int``
    :type entity_type: ``unicode``
    :type entity_value: ``unicode``
    """
    self.obj[offset] = {
        'type': entity_type,
        'value': entity_value,
        'entity_id': re.sub('\s', '_', entity_value)
    }

  def get_all(self):
    """
    Get all entities in list.

    :returns: ``tuple``: (``int``, ``dict``)
    """
    return list(self.obj.items())


class Document(object):
  """A document that is being processed."""

  def __init__(self):
    self.docid = None
    self.path = None
    self.ext = None
    self.added = -1
    self.doctype = 'unknown'
    self.parent = None
    self.entities = Entities()
    self.tag = None
    self.meta = {}
    self.status = 'unknown'
    self.text = None
    self.children = 0
    self.magic_hit = False

  def set_type(self, doc_type):
    """
    Set the type of document this is, e.g., diskimage, archive, document.

    :param doc_type: Type of document.
    :type doc_type: ``str``
    """

    self.doctype = doc_type
    self.meta['type'] = doc_type

  def set_size(self, size):
    """
    Set size of document/file.

    :param size: Size of file.
    :type size: ``int``
    """
    self.meta['size'] = size

  def set_id(self, data):
    """
    Set ID of document. To allow multiple files with the same path, the
    digest of supplied data (e.g. first 4KB) is appended to the doc ID.

    :param data: Data to append to docuemnt path.
    :type data: Anything digestable by hashlib.
    """
    digest = hashlib.md5()
    digest.update(self.path.encode('utf-8'))

    if isinstance(data, unicode):
      data = data.encode('utf-8')

    digest.update(data)
    self.docid = digest.hexdigest()

  def as_obj(self):
    """
    Return a dict representation of the document.

    :returns: ``dict``
    """
    parent_obj = None
    if self.parent:
      parent_obj = {
          'path': self.parent.path,
          'id': self.parent.docid,
          'filename': os.path.basename(self.parent.path)
      }

    metaobj = {
        'added': self.added
    }

    meta = self.meta

    for key, value in metaobj.items():
      meta[key] = value

    entities = {}

    for _, entity in self.entities.get_all():
      entities[entity['entity_id']] = entity

    return {
        'ext': self.ext,
        'id': self.docid,
        'path': self.path,
        'doctype': self.doctype,
        'filename': os.path.basename(self.path),
        'parent': parent_obj,
        'tag': self.tag,
        'status': self.status,
        'text': self.text if self.text else u'',
        'meta': meta
    }


def get_document(path, parent=None):
  """
  Create a new document object from the given path.

  :param path: Path to document (does not have to exist on file system).
  :param parent: Parent document (e.g. diskimage or archive).
  :returns: ``gransk.core.Document``
  """
  doc = Document()
  doc.path = path

  if os.path.dirname(path):
    doc.meta['directory'] = os.path.dirname(path)

  digest = hashlib.md5()

  try:
    digest.update(path.encode('utf-8'))
  except UnicodeDecodeError:
    digest.update(path)

  doc.docid = digest.hexdigest()

  if '.' in doc.path:
    doc.ext = os.path.basename(doc.path).split('.')[-1].lower()
  else:
    doc.ext = u'none'

  doc.parent = parent

  try:
    doc.set_size(os.path.getsize(path))
  except OSError:
    doc.set_size(-1)

  doc.added = int(time.time())
  return doc
