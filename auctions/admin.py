from django.contrib import admin

from .models import User, AuctionListings, Bid, Comment, Watchlist

# Register your models here.
admin.site.register(User)
admin.site.register(AuctionListings)
admin.site.register(Bid)
admin.site.register(Comment)
admin.site.register(Watchlist)
