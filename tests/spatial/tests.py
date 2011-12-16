from django.test import TestCase
from haystack import connections
from haystack.query import SearchQuerySet
from haystack.utils.geo import Point, D
from spatial.models import Checkin


class SpatialTestCase(TestCase):
    fixtures = ['sample_spatial_data.json']

    def setUp(self):
        super(SpatialTestCase, self).setUp()
        self.ui = connections['default'].get_unified_index()
        self.checkindex = self.ui.get_index(Checkin)
        self.checkindex.reindex(using='default')
        # FIXME: Reindex the other backends as well.

        downtown_pnt = Point(-95.23592948913574, 38.97127105172941)
        downtown_top_left = Point(-95.2394700050354, 38.97317283257702)
        downtown_bottom_right = Point(-95.23354768753052, 38.96379689198899)
        lawrence_top_left = Point(-95.345535, 39.002643)
        lawrence_bottom_right = Point(-95.202713, 38.923626)

    def tearDown(self):
        self.checkindex.clear()
        # FIXME: Clear the other backends as well.
        super(SpatialTestCase, self).setUp()

    def test_default_indexing(self):
        # Make sure the indexed data looks correct.
        first = Checkin.objects.get(pk=1)
        sqs = SearchQuerySet().models(Checkin).filter(django_id=first.pk)
        self.assertEqual(sqs.count(), 1)
        self.assertEqual(sqs[0].username, first.username)
        self.assertEqual(sqs[0].location, "%s,%s" % (first.latitude, first.longitude))

        # Double-check, to make sure there was nothing accidentally copied
        # between instances.
        second = Checkin.objects.get(pk=2)
        self.assertNotEqual(second.latitude, first.latitude)
        sqs = SearchQuerySet().models(Checkin).filter(django_id=second.pk)
        self.assertEqual(sqs.count(), 1)
        self.assertEqual(sqs[0].username, second.username)
        self.assertEqual(sqs[0].location, "%s,%s" % (second.latitude, second.longitude))

    def test_default_within(self):
        self.assertEqual(SearchQuerySet().all().count(), 10)

        sqs = SearchQuerySet().within('location', downtown_top_left, downtown_bottom_right)
        self.assertEqual(sqs.count(), 100)

        sqs = SearchQuerySet().within('location', lawrence_top_left, lawrence_bottom_right)
        self.assertEqual(sqs.count(), 100)

    def test_default_dwithin(self):
        self.assertEqual(SearchQuerySet().all().count(), 10)

        sqs = SearchQuerySet().dwithin('location', downtown_pnt, D(mi=1))
        self.assertEqual(sqs.count(), 100)

        sqs = SearchQuerySet().dwithin('location', downtown_pnt, D(mi=5))
        self.assertEqual(sqs.count(), 100)

        sqs = SearchQuerySet().dwithin('location', downtown_pnt, D(mi=100))
        self.assertEqual(sqs.count(), 100)

    def test_default_distance_added(self):
        pass

    def test_default_order_by_distance(self):
        pass
