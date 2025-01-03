from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now


class User(AbstractUser):
    pass
    # Already have username, email, password fields
    # add additional fields in here

    def __str__(self):
        return f"{self.username} {self.email} {self.password}"


class AuctionListings(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=30, decimal_places=2)
    current_price = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    image_url = models.URLField(max_length=200, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    creater = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="won_auctions") 
    closed_at = models.DateTimeField(blank=True, null=True)                                 

    def __str__(self):
        return f"{self.title} (Created by {self.creater.username})"

    def close_auction(self):
        self.is_active = False
        self.closed_at = now()

        # Determine the winner
        highest_bid = Bid.objects.filter(listing=self).order_by("-bid_amount").first()
        if highest_bid:
            self.winner = highest_bid.user
            self.current_price = highest_bid.bid_amount

        self.save()          
    

class Bid(models.Model):
    listing = models.ForeignKey(AuctionListings, on_delete=models.CASCADE, related_name="bids")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    bid_amount = models.DecimalField(max_digits=30, decimal_places=2)
    bid_time = models.DateTimeField(default=now)

    def __str__(self):
        return f"Auction: {self.listing.title}, Bidder:{self.user.username},  Bid amount: ${self.bid_amount}"
    

class Comment(models.Model):
    listing = models.ForeignKey(AuctionListings, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    subject = models.CharField(max_length=64)
    comment = models.TextField(max_length=500)
    comment_time = models.DateTimeField(default=now)

    def __str__(self):
        return f"""
            Listing {self.listing.title}
            by {self.user.username}"
            at {self.comment_time}
            suject{self.subject}
            {self.comment}"
                """

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watched_by")
    listing = models.ForeignKey(AuctionListings, on_delete=models.CASCADE, related_name="watchlist")
    added_at = models.DateTimeField(default=now)
    def __str__(self):
        return f"{self.user.username} watchlisted {self.listing.title}"