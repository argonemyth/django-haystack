import datetime
from django.db import models


class Checkin(models.Model):
    username = models.CharField(max_length=255)
    # We're going to do some non-GeoDjango action, since the setup is
    # complex enough. You could just as easily do:
    #
    #   location = models.PointField()
    #
    # ...and your ``search_indexes.py`` could be less complex.
    latitude = models.FloatField()
    longitude = models.FloatField()
    comment = models.CharField(max_length=140, blank=True, default='', help_text='Say something pithy.')
    created = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        ordering = ['-created']

    # Again, with GeoDjango, this would be unnecessary.
    def get_location(self, obj):
        pnt = Point(obj.longitude, obj.latitude)
        return pnt
        # pnt_lng, pnt_lat = pnt.get_coords()
        #return "%s,%s" % (pnt_lat, pnt_lng)
