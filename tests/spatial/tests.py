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

        self.downtown_pnt = Point(-95.23592948913574, 38.97127105172941)
        self.downtown_bottom_left = Point(-95.23947, 38.9637903)
        self.downtown_top_right = Point(-95.23362278938293, 38.973081081164715)
        self.lawrence_bottom_left = Point(-95.345535, 39.002643)
        self.lawrence_top_right = Point(-95.202713, 38.923626)

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
        # Make sure we've got a proper ``Point`` object.
        self.assertAlmostEqual(sqs[0].location.get_coords()[0], first.longitude)
        self.assertAlmostEqual(sqs[0].location.get_coords()[1], first.latitude)

        # Double-check, to make sure there was nothing accidentally copied
        # between instances.
        second = Checkin.objects.get(pk=2)
        self.assertNotEqual(second.latitude, first.latitude)
        sqs = SearchQuerySet().models(Checkin).filter(django_id=second.pk)
        self.assertEqual(sqs.count(), 1)
        self.assertEqual(sqs[0].username, second.username)
        self.assertAlmostEqual(sqs[0].location.get_coords()[0], second.longitude)
        self.assertAlmostEqual(sqs[0].location.get_coords()[1], second.latitude)

    def test_default_within(self):
        self.assertEqual(SearchQuerySet().all().count(), 10)

        sqs = SearchQuerySet().within('location', self.downtown_bottom_left, self.downtown_top_right)
        self.assertEqual(sqs.count(), 7)

        sqs = SearchQuerySet().within('location', self.lawrence_bottom_left, self.lawrence_top_right)
        self.assertEqual(sqs.count(), 9)

    def test_default_dwithin(self):
        self.assertEqual(SearchQuerySet().all().count(), 10)

        sqs = SearchQuerySet().dwithin('location', self.downtown_pnt, D(mi=0.1))
        self.assertEqual(sqs.count(), 5)

        sqs = SearchQuerySet().dwithin('location', self.downtown_pnt, D(mi=0.5))
        self.assertEqual(sqs.count(), 7)

        sqs = SearchQuerySet().dwithin('location', self.downtown_pnt, D(mi=100))
        self.assertEqual(sqs.count(), 10)

    def test_default_distance_added(self):
        sqs = SearchQuerySet().within('location', self.downtown_bottom_left, self.downtown_top_right).distance('location', self.downtown_pnt)
        self.assertEqual(sqs.count(), 7)
        self.assertAlmostEqual(sqs[0].distance.mi, 0.01985226)
        self.assertAlmostEqual(sqs[1].distance.mi, 0.03385863)
        self.assertAlmostEqual(sqs[2].distance.mi, 0.04539100)
        self.assertAlmostEqual(sqs[3].distance.mi, 0.04831436)
        self.assertAlmostEqual(sqs[4].distance.mi, 0.41116546)
        self.assertAlmostEqual(sqs[5].distance.mi, 0.25098114)
        self.assertAlmostEqual(sqs[6].distance.mi, 0.04831436)

        sqs = SearchQuerySet().dwithin('location', self.downtown_pnt, D(mi=0.1)).distance('location', self.downtown_pnt)
        self.assertEqual(sqs.count(), 5)
        self.assertAlmostEqual(sqs[0].distance.mi, 0.01985226)
        self.assertAlmostEqual(sqs[1].distance.mi, 0.03385863)
        self.assertAlmostEqual(sqs[2].distance.mi, 0.04539100)
        self.assertAlmostEqual(sqs[3].distance.mi, 0.04831436)
        self.assertAlmostEqual(sqs[4].distance.mi, 0.04831436)

    def test_default_order_by_distance(self):
        sqs = SearchQuerySet().within('location', self.downtown_bottom_left, self.downtown_top_right).distance('location', self.downtown_pnt).order_by('distance')
        self.assertEqual(sqs.count(), 7)
        self.assertEqual([result.pk for result in sqs], ['8', '9', '6', '3', '1', '2', '5'])
        self.assertEqual(["%0.04f" % result.distance.mi for result in sqs], ['0.0199', '0.0339', '0.0454', '0.0483', '0.0483', '0.2510', '0.4112'])

        sqs = SearchQuerySet().dwithin('location', self.downtown_pnt, D(mi=0.1)).distance('location', self.downtown_pnt).order_by('distance')
        self.assertEqual(sqs.count(), 5)
        self.assertEqual([result.pk for result in sqs], ['8', '9', '6', '3', '1'])
        self.assertEqual(["%0.04f" % result.distance.mi for result in sqs], ['0.0199', '0.0339', '0.0454', '0.0483', '0.0483'])

        sqs = SearchQuerySet().dwithin('location', self.downtown_pnt, D(mi=0.1)).distance('location', self.downtown_pnt).order_by('-distance')
        self.assertEqual(sqs.count(), 5)
        self.assertEqual([result.pk for result in sqs], ['3', '1', '6', '9', '8'])
        self.assertEqual(["%0.04f" % result.distance.mi for result in sqs], ['0.0483', '0.0483', '0.0454', '0.0339', '0.0199'])

    def test_default_complex(self):
        sqs = SearchQuerySet().auto_query('coffee').within('location', self.downtown_bottom_left, self.downtown_top_right).distance('location', self.downtown_pnt).order_by('distance')
        self.assertEqual(sqs.count(), 5)
        self.assertEqual([result.pk for result in sqs],['8', '6', '3', '1', '2'])
        self.assertEqual(["%0.04f" % result.distance.mi for result in sqs], ['0.0199', '0.0454', '0.0483', '0.0483', '0.2510'])

        sqs = SearchQuerySet().auto_query('coffee').dwithin('location', self.downtown_pnt, D(mi=0.1)).distance('location', self.downtown_pnt).order_by('distance')
        self.assertEqual(sqs.count(), 4)
        self.assertEqual([result.pk for result in sqs], ['8', '6', '3', '1'])
        self.assertEqual(["%0.04f" % result.distance.mi for result in sqs], ['0.0199', '0.0454', '0.0483', '0.0483'])

        sqs = SearchQuerySet().auto_query('coffee').dwithin('location', self.downtown_pnt, D(mi=0.1)).distance('location', self.downtown_pnt).order_by('-distance')
        self.assertEqual(sqs.count(), 4)
        self.assertEqual([result.pk for result in sqs], ['3', '1', '6', '8'])
        self.assertEqual(["%0.04f" % result.distance.mi for result in sqs], ['0.0483', '0.0483', '0.0454', '0.0199'])

        sqs = SearchQuerySet().auto_query('coffee').within('location', self.downtown_bottom_left, self.downtown_top_right).distance('location', self.downtown_pnt).order_by('-created')
        self.assertEqual(sqs.count(), 5)
        self.assertEqual([result.pk for result in sqs], ['8', '6', '3', '2', '1'])

        sqs = SearchQuerySet().auto_query('coffee').dwithin('location', self.downtown_pnt, D(mi=0.1)).distance('location', self.downtown_pnt).order_by('-created')
        self.assertEqual(sqs.count(), 4)
        self.assertEqual([result.pk for result in sqs], ['8', '6', '3', '1'])
