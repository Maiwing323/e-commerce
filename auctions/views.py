from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

from decimal import Decimal

from .models import User, AuctionListings, Bid, Comment, Watchlist


def index(request):
    auctions = AuctionListings.objects.filter(is_active=True).order_by('-created_at')
    paginator = Paginator(auctions, 10) # Show 10 listings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "auctions/index.html",{
        "page_obj": page_obj
    })
    

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def create(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        starting_bid = request.POST.get("starting_bid")
        image_url = request.POST.get("image_url", None) # defualt is None
        delivery_fee = request.POST.get("delivery_fee", None)
        category = request.POST.get("category", None)
          
        if not delivery_fee or delivery_fee.strip() == "":
            delivery_fee = Decimal("0.00")
        else:
            delivery_fee = Decimal(delivery_fee)
        try:
            auction = AuctionListings(
                title = title,
                description = description,
                starting_bid = starting_bid,
                image_url = image_url,
                delivery_fee = delivery_fee,
                category = category,
                created_at = timezone.now(),
                creater = request.user,
            )
            auction.save()
            return redirect("index")
        except Exception as e:
            return render(request, "auctions/create.html", {
                "message": f"An error occurred: {e}"
            })

    return render(request, "auctions/create.html")


def listing(request, auction_id):
    auction = get_object_or_404(AuctionListings, id=auction_id)
    # Get all the comments of the auction
    comments = auction.comments.all()
    # Count the number of bids for the listing
    bid_count = auction.bids.count()
    highest_bid = Bid.objects.filter(listing=auction).order_by('-bid_amount').first()
    current_price = highest_bid.bid_amount if highest_bid else auction.starting_bid
    
    is_in_watchlist = (
        Watchlist.objects.filter(user=request.user, listing=auction).exists() 
        if request.user.is_authenticated 
        else False
        )
    if request.method == "POST":
        if "add_watchlist" in request.POST:
            Watchlist.objects.get_or_create(user=request.user, listing=auction)
            messages.success(request, "Added to your watchlist.")
        elif "remove_watchlist" in request.POST:
            Watchlist.objects.filter(user=request.user, listing=auction).delete()
            messages.success(request, "Removed from your watchlist.")  
        return redirect("listing", auction_id=auction.id) 
    
    if not auction.is_active and auction.winner == request.user: 
        messages.success(request, 
                         f"Congratulation {request.user.username}. You won this auction on {auction.current_price}!")
                             
    return render(request, "auctions/listing.html",{
        "auction": auction,
        "comments" : comments,
        "is_in_watchlist": is_in_watchlist,
        "bid_count": bid_count,
        "current_price": current_price
    })
    

def categories(request):
    # flat=True returns a flat list instead of a list of tuples
    raw_cate = set(AuctionListings.objects.values_list('category', flat=True))

    # Create a set(cate) by {}
    # for cat in raw_cate
    # if cat, ingore the empty string or None
    # remove the leading/trailing space .strip(), then capitalizes and adds to the set
    cate = {cat.strip().capitalize() for cat in raw_cate if cat}

    return render(request, "auctions/categories.html",{
        "categories": cate
    })

def category_listings(request, category_name):
    auctions = AuctionListings.objects.filter(category=category_name, is_active=True)
    paginator = Paginator(auctions, 10) # Show 10 listings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "auctions/index.html",{
        "page_obj": page_obj
    })


@login_required
def watchlist(request):
    # Get the auctions that the user has added to their watchlist
    watchlists = Watchlist.objects.filter(user=request.user).select_related('listing').order_by('-added_at')
    auction_listings = [watchlist.listing for watchlist in watchlists]
    
    paginator = Paginator(auction_listings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "auctions/watchlist.html", {
        "page_obj": page_obj
    })


@login_required
def closedlist(request):
    closed_auctions = AuctionListings.objects.filter(is_active=False).order_by('-closed_at')
    paginator = Paginator(closed_auctions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"auctions/close_listing.html",{
        "page_obj": page_obj
    })

@login_required
def close_listing(request, auction_id):
    # Get the listing
    auction = get_object_or_404(AuctionListings, id=auction_id)
    auction.close_auction() # Handle the AuctionListing model close_auction

    if auction.winner:
        messages.success(request, 
                         f"The auction has been close. The winner is {auction.winner.username} with  ${auction.current_price}."
                        )
    else:
        messages.success(request, "The auction has been closed. No bids were placed.")

    return redirect("listing", auction_id=auction.id)


@login_required
def bid(request, auction_id):
    if request.method == "POST":
        auction = get_object_or_404(AuctionListings, id=auction_id)
        
        # Check auction.is_active
        if not auction.is_active:
            messages.error(request, "This auction is no longer active.")
        
        highest_bid = Bid.objects.filter(listing=auction).order_by("-bid_amount").first()
        if highest_bid:
            auction.current_price = highest_bid.bid_amount
        else:
            auction.current_price = auction.starting_bid
        auction.save()
        # Get the bid amount from the POST data
        bid_amount = request.POST.get("place_bid")
        try:
            bid_amount = Decimal(bid_amount)
        except (ValueError, TypeError):
            messages.error(request, "Invalid bid_amount")
            return redirect("listing", auction_id=auction.id)
        
        # Validate the bid amount
        if bid_amount <= auction.current_price:
            messages.error(request, "Your bid must be greater than the current price.", extra_tags="warning")
            return redirect("listing", auction_id=auction.id)
        
        # Save the bid
        new_bid = Bid.objects.create(
            user = request.user,
            listing = auction,
            bid_amount = bid_amount
        )
        # Update the current price in the AuctionListings
        auction.current_price = new_bid.bid_amount
        auction.save()

        messages.success(request, "Your bid has been placed successfully.")
        return redirect("listing", auction_id=auction.id)
    # Redirect to the auction listing page if the method is not POST
    return redirect("listing", auction_id=auction.id)


@login_required
def create_comment(request, auction_id):
    if request.method == "POST":
        auction = get_object_or_404(AuctionListings, id=auction_id)

        # Get the subject and comment from the POST data
        subject = request.POST.get("subject")
        comment_text = request.POST.get("comment-text")
        
        # Save the comment
        comment = Comment.objects.create(
            user = request.user,
            listing = auction,
            subject = subject,
            comment = comment_text,
            comment_time = timezone.now()
        )
        comment.save()
        messages.success(request, "Your comment has been created successfully.")
        return redirect("listing", auction_id=auction.id)
    
    comments = Comment.objects.filter(listing=auction)
    return render(request, 'auctions/listing.html', {
        'auction': auction,
        'comments': comments,
    })