# coding: utf-8
from collections import defaultdict

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.db.utils import ProgrammingError
from django.dispatch import receiver
from django.utils.text import slugify
from rest_framework.authtoken.models import Token

from realestate.custom_models import CustomMoneyField
from .thumbnail import Thumbnailed


class ParcelManager(models.Manager):
    def distinct_cities_at(self, state):
        """Return a list of one parcel for each city on db for the given
        state """
        queryset = self.get_queryset().filter(
            available=True, city__state__code=state).order_by('city').distinct('city')
        return queryset


class Parcel(models.Model):
    address = models.TextField()
    city = models.ForeignKey('City', null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    bedrooms = models.SmallIntegerField(blank=True, null=True)
    bathrooms_full = models.SmallIntegerField(blank=True, null=True)
    bathrooms_half = models.SmallIntegerField(blank=True, null=True)
    square_feet = models.IntegerField(blank=True, null=True)
    square_feet_lot = models.CharField('Square Feet Lot', max_length=30, blank=True, null=True)
    price = CustomMoneyField(max_length=20, blank=True, null=True)
    description = models.TextField()
    home_type = models.CharField(max_length=250, blank=True, null=True)
    year_built = models.CharField('Year Built', max_length=4, blank=True, null=True)
    price_per_square_foot = models.CharField(max_length=30, blank=True, null=True)
    date_posted = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    longitude = models.CharField(max_length=20)
    latitude = models.CharField(max_length=20)
    meta_keywords = models.TextField(blank=True, null=True)
    meta_description = models.TextField()
    create_date = models.DateField()
    original_url = models.TextField()
    available = models.BooleanField(default=True)
    last_update_available = models.DateField(blank=True, null=True)
    features = models.ManyToManyField('Feature')  # db_table='main_features'
    listing_id = models.BigIntegerField(unique=True)

    objects = ParcelManager()

    class Meta:
        # db_table = 'main'
        ordering = ['-id']

    @property
    def grouped_features(self):
        d = defaultdict(list)

        for feature in self.features.all():
            d[feature.type].append(feature.value)

        return d.items()

    def get_url(self):
        return 'http://seethisproperty.com' + self.get_absolute_url()

    def get_complete_state(self):
        from realestate.us_states import US_STATES
        if self.city.state.code in US_STATES:
            return US_STATES[self.city.state.code]
        else:
            return self.city.state.code

    def get_images(self):
        images = self.local_image.all()
        if images.count() == 0:
            images = self.image.all()
        return images or [{'url': '/static/images/noImage.jpg'}]

    def get_absolute_url(self):
        return '/'.join([
            '/' + str(self.city.state.code), self.city_slug, self.address_slug,
            str(self.pk)])

    def get_image_urls(self):
        images = self.get_images()
        urls = []
        if images != [{'url': '/static/images/noImage.jpg'}]:
            for i in images:
                try:
                    urls.append(i.url)
                except AttributeError or ProgrammingError:
                    urls.append(i.image.url)
        else:
            urls = images
        return urls

    @property
    def city_slug(self):
        return slugify(str(self.city)).title()

    @property
    def address_slug(self):
        return slugify(str(self.address)).title()


class Feature(models.Model):
    """
    Parcel's features objects (M2M relation from Parcel)
    """
    value = models.TextField()
    type = models.CharField(max_length=512)

    # class Meta:
    #     db_table = 'features'


class School(models.Model):
    parcel = models.ForeignKey(Parcel, related_name='school')  # db_column='main_id'
    score = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    grades = models.CharField(max_length=50)
    distance = models.CharField(max_length=50)

    # class Meta:
    #     db_table = 'schools'


class Image(models.Model):
    """
    Images taken from crawler, not privately hosted
    """
    parcel = models.ForeignKey(Parcel, related_name='image')  # db_column='main_id'
    url = models.CharField(max_length=350)
    alt = models.CharField(max_length=200, null=True, blank=True)

    # class Meta:
    #     db_table = 'images'


class State(models.Model):
    code = models.CharField(primary_key=True, max_length=2)
    name = models.CharField(max_length=255)

    # class Meta:
    #     db_table = 'states'

    def __str__(self):
        return self.code


class City(models.Model):
    name = models.CharField(max_length=512, blank=True)
    state = models.ForeignKey(State)  # db_column='state'
    image = models.ForeignKey(Image, related_name='+')

    # class Meta:
    #     db_table = 'cities'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return '/{}/{}'.format(str(self.state.code), str(self.city_slug))

    @property
    def city_slug(self):
        return slugify(str(self.name)).title()


class ParcelRemoved(models.Model):
    """
    Keeps track of Parcel records that have been marked as available=False for the API
    """
    parcel = models.ForeignKey(
        Parcel, related_name='+', on_delete=models.DO_NOTHING)  # db_column='main_id'
    date_removed = models.DateField(auto_now_add=True)

    # class Meta:
    #     db_table = 'realestate_mainremoved'

    @property
    def address(self):
        return self.parcel.address or ''

    @property
    def city(self):
        return self.parcel.city or ''

    @property
    def state(self):
        return self.parcel.city.state.code or ''

    @property
    def zip_code(self):
        return self.parcel.zip_code or ''

    @property
    def mainid(self):
        return self.parcel.id or ''

    @property
    def removed_at(self):
        return self.date_removed.strftime('%Y/%m/%d')

    def get_url(self):
        return self.parcel.get_url() or ''


def image_path(instance, filename):
    return str(instance.parcel.pk) + '/' + filename


class ParcelImage(models.Model):
    """
    Privately hosted Image table fed from gather_images
    """
    image = models.ImageField(verbose_name='Image', upload_to=image_path)
    parcel = models.ForeignKey(Parcel, related_name='local_image')
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def thumbnail_url(self):
        thumbs = Thumbnailed(file=self.image)
        return thumbs.thumb_url

    def save(self, *args, **kwargs):
        thumbs = Thumbnailed(file=self.image)
        thumbs.compress_image()
        thumbs.create_thumbnail()
        super(ParcelImage, self).save(*args, **kwargs)
        thumbs.garbage_collection()

    def delete(self):
        thumbs = Thumbnailed(file=self.image)
        thumbs.delete_thumbnail()
        super(ParcelImage, self).delete()

        # class Meta:
        #     db_table = 'main_image'


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Realtor(models.Model):
    main_id = models.IntegerField()
    realtors_id = models.IntegerField()

    class Meta:
        unique_together = (('main_id', 'realtors_id'),)


class RealtorInfo(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    recent_sales = models.IntegerField(blank=True, null=True)
    street_address = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=64, blank=True, null=True)
    state = models.CharField(max_length=32, blank=True, null=True)
    zip_code = models.CharField(max_length=16, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    facebook = models.CharField(max_length=20000, blank=True, null=True)
    linkedin = models.CharField(max_length=20000, blank=True, null=True)
    screen_name = models.CharField(max_length=50, blank=True, null=True)
    zillow_url = models.CharField(max_length=600, blank=True, null=True)


class CrawlerZipcodes(models.Model):
    zip_code = models.CharField(max_length=5, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    county = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'crawler_zipcodes'