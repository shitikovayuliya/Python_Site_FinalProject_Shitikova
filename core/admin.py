from django.contrib import admin
from .models import Category, Listing, RentalRequest, ListingImage, Review

admin.site.register(Category)
admin.site.register(Listing)
admin.site.register(RentalRequest)
admin.site.register(ListingImage)
admin.site.register(Review)
