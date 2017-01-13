from django import forms
from django.core.urlresolvers import reverse_lazy

from realestate.us_states import US_STATES


class ContactForm(forms.Form):
    name = forms.CharField()
    phone = forms.CharField()
    email = forms.CharField()


class ContactUsForm(forms.Form):
    name = forms.CharField()
    phone = forms.CharField()
    email = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)


def get_sorted_states():
    states = [(state, US_STATES[state]) for state in US_STATES]
    return sorted(states, key=lambda x: x[1])

class PropertySearchForm(forms.Form):
    address = forms.CharField(label='Street Name', widget=forms.TextInput(attrs={'placeholder': 'Street Name...'}))
    state = forms.ChoiceField(
        choices=get_sorted_states(),
        required=True)
    city = forms.CharField(widget=forms.TextInput(attrs={
        'data-target-url': reverse_lazy('cities_by_name')
    }))
    zip_code = forms.CharField()
    bedrooms = forms.ChoiceField(
        label='Bedrooms',
        choices=[('', '----')] + [(x, x) for x in range(1, 11)])
    bathrooms_full = forms.ChoiceField(
        label='Bathrooms',
        choices=[('', '----')] + [(x, x) for x in range(1, 11)])
    square_feet_start = forms.CharField()
    square_feet_end = forms.CharField()
    price_start = forms.CharField()
    price_end = forms.CharField()
    miles = forms.ChoiceField(label='',
                              required=True,
                              choices=[('', '----')] + [(x, x) for x in [0.5, 1, 2, 5, 10, 20, 50, 75, 100, 150, 200, 300]])  #miles=forms.CharField(initial=20)
    user_address = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Address'}))
