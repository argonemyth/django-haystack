.. _ref-spatial:

==============
Spatial search
==============

Spatial filtering example using Solr's SpatialSearch_::

>>> from haystack.query import SearchQuerySet
>>> sq = SearchQuerySet()
>>> sq.spatial(lat=38.898748, lon=77.037684, sfield='location', distance=5)
>>> sq.order_by_distance(lat=38.898748, long=77.037684, sfield='location', filter='bbox').order_by('id')

# TODO this sucks!

.. _SpatialSearch: http://wiki.apache.org/solr/SpatialSearch
