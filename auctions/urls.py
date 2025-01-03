from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("closedlist",views.closedlist, name="closedlist"),
    path("listing/<int:auction_id>", views.listing, name="listing"),
    path("listing/<int:auction_id>/close", views.close_listing, name="close_listing"),
    path("listing/<int:auction_id>/bid", views.bid, name="bid"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("categories", views.categories, name="categories"),
    path("categories/<str:category_name>", views.category_listings, name="category_listings"),
    path("listing/<int:auction_id>/create_comment", views.create_comment, name="create_comment")
]