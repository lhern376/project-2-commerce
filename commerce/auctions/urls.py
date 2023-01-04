from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    ## List views
    path("categories", views.categories, name="categories"),
    path(
        "categories/<str:category>",
        views.ListingsByCategoryListView.as_view(),
        name="listings-by-category",
    ),
    path("listings/", views.ListingsListView.as_view(), name="listings"),
    path(
        "listings/<int:pk>", views.ListingDetailView.as_view(), name="listing-details"
    ),
    ## Watchlist
    path("watchlist", views.WatchlistListView.as_view(), name="listings-watchlist"),
    path("watchlist/add/<int:id>", views.watchlist_add, name="watchlist-add"),
    path("watchlist/remove/<int:id>", views.watchlist_remove, name="watchlist-remove"),
    ## Create/Edit
    path("listing/new", views.listing_new, name="listing-new"),
    path("listing/<int:pk>/edit", views.listing_edit, name="listing-edit"),
    ## Comments and Replies
    # id of a listing
    path(
        "listing/comment/<int:listing_id>",
        views.listing_comment,
        name="listing-comment",
    ),
    # id of a comment
    path("listing/reply/<int:comment_id>", views.listing_reply, name="listing-reply"),
    ## Listings owned
    path("my-listings", views.ListingsOwnedListView.as_view(), name="listings-owned"),
    ## Bidding
    # get min bid amount and current price
    path(
        "listing/<int:listing_id>/get-min-bid",
        views.listing_get_min_bid,
        name="listing-get-min-bid",
    ),
    # set bid amount
    path(
        "listing/<int:listing_id>/set-bid",
        views.listing_set_bid,
        name="listing-set-bid",
    ),
    # close listing
    path(
        "listing/<int:listing_id>/close-listing",
        views.listing_close,
        name="listing-close",
    ),
    ## Bid History
    path(
        "listing/<int:listing_id>/bid-history",
        views.listing_bid_history,
        name="listing-bid-history",
    ),
    ## Login/Logout/Register urls
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
]
