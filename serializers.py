from rest_framework import serializers

from realestate.models import City, Feature, Parcel, ParcelRemoved


class CitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = City
        fields = ('name',)


class FeatureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Feature
        fields = ('value', 'type')


class ParcelSerializer(serializers.HyperlinkedModelSerializer):
    city = CitySerializer()

    class Meta:
        model = Parcel
        fields = ('id', 'city', 'zip_code', 'address', 'get_url')


class ParcelRemovedSerializer(serializers.HyperlinkedModelSerializer):
    city = CitySerializer()

    class Meta:
        model = ParcelRemoved
        fields = ('parcel', 'city', 'zip_code',
                  'address', 'get_url', 'removed_at')


class ParcelAdvancedSeralizer(serializers.HyperlinkedModelSerializer):
    city = CitySerializer()
    features = FeatureSerializer(many=True)

    class Meta:
        model = Parcel
        fields = (
            'id', 'city', 'zip_code', 'address', 'get_url', 'bedrooms',
            'bathrooms_full', 'bathrooms_half', 'description', 'features',
            'price', 'square_feet', 'square_feet_lot', 'home_type',
            'longitude', 'latitude', 'available', 'date_posted', 'create_date',
            'get_image_urls'
        )
