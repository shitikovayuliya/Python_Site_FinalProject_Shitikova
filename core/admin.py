from django.contrib import admin
from .models import Category, Listing, RentalRequest, ListingImage, Booking, Review

admin.site.register(Category)
admin.site.register(Listing)
admin.site.register(RentalRequest)
admin.site.register(ListingImage)
admin.site.register(Booking)
admin.site.register(Review)
