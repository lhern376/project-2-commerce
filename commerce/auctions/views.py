# views imports
from django.contrib.auth import authenticate, login, logout
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    Http404,
    JsonResponse,
)
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import list, detail
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

# models, forms, files, utility imports
from .models import User, Category, Listing, Bid, Comment
from .forms import LoginUserForm, RegisterUserModelForm, ListingModelForm
from django.db import IntegrityError
from django.core.files.storage import default_storage
from django.utils import timezone
from . import util
import datetime
import time
import json


## Constants
# pagination
PAGINATE_BY = 6
ON_ENDS = 2
ON_EACH_SIDE = 1

## Helper function for closing listings if they are expired but remain active
# - Applies to following views:
# edit, comment, get_min_bid, set_bid, listing-details, bid_history, active-listings, watchlist, my-listings
# - Active-listings returns only active listings
# - Watchlist and my-listings return both closed and active listings
def close_listing_if_expired(listing):
    if listing.status == "active" and listing.is_expired:
        listing.status = "closed"
        listing.bidding_ended = timezone.now()
        listing.save()


## Helper function for redirecting back to details page if a listing is already closed
# Applies to following views: edit, comment, get_min_bid, set_bid
def redirect_if_listing_has_closed(listing) -> bool:
    return listing.status == "closed"


## Helper function to redirect if listing was edited
def redirect_if_listing_was_edited(user_date_str, listing):
    user_date = timezone.datetime.fromisoformat(user_date_str)
    return user_date != listing.bidding_starts


def index(request):
    return HttpResponseRedirect(reverse("listings"))


# all other listing views will inherit from this one
class ListingsListView(list.ListView):
    context_object_name = "listings"
    template_name = "auctions/listings_active_all.html"
    # paginate_by = PAGINATE_BY  # not using paginate_by to use my own custom paginator

    ## NOTES:
    # - method call order:
    #   1. get_queryset
    #   2. get_context_data
    def get_queryset(self):
        listings = (
            Listing.objects.filter(status="active")
            .filter(bidding_starts__lt=timezone.now())
            .order_by("-bidding_starts")
        )
        for listing in listings:
            close_listing_if_expired(listing)
        return listings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for setting visual cue in navigation (override this in the child classes)
        context["cue"] = "all"
        # defaults to 'results by: latest'
        context["search_criteria"] = {"criteria": "Latest"}
        return context

    ## NOTES:
    # - When defining .post() or .get(), .get_queryset and .get_context_data are not called implicitly
    # - As a result, self.object_list has to be initialized within .get() and .post() at the beginning of the call
    def get(self, request, *args, **kwargs) -> HttpResponse:
        # Avoids 'ListingsByCategoryListView' object has no attribute 'object_list'
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        # condition set here so that the below processing occurs only on form submission or directly specifying sort_by param in url
        if request.GET.get("sort_by"):

            listings = self.object_list
            min = request.GET.get("min", "")
            max = request.GET.get("max", "")
            criteria = request.GET.get("sort_by", "")

            context["listings"], context["search_criteria"] = util.helper_listView_sort(
                listings, min, max, criteria
            )

            context["min"] = min
            context["max"] = max
            context["sort_by"] = criteria

        context["results_count"] = context["listings"].count()

        # track gallery view activation
        context["is_gallery_active"] = request.GET.get("is_gallery_active", "")

        ## Custom Paginator
        page = request.GET.get("page", "1")
        paginator = Paginator(context["listings"], PAGINATE_BY)
        page = util.helper_validate_page_number(page, paginator.num_pages)

        context["elided_page_range"] = paginator.get_elided_page_range(
            number=page, on_each_side=ON_EACH_SIDE, on_ends=ON_ENDS
        )

        context["listings"] = paginator.get_page(page)
        context["paginator"] = paginator
        if paginator.num_pages != 1:
            context["is_paginated"] = True

        # setting them equal so that object_list does not send extra data
        context["object_list"] = context["listings"]
        # setting page_obj because it is being used in the template (alternatively could have changed template to use 'listings' instead)
        context["page_obj"] = context["listings"]

        # print(f"\nCONTEXT ON REGULAR GET:\n{context}\n")
        return render(request, self.template_name, context)


class ListingsByCategoryListView(ListingsListView):
    template_name = "auctions/listings_by_category.html"

    def get_queryset(self):
        self.category = Category.objects.get(category_string=self.kwargs["category"])
        listings = (
            Listing.objects.filter(category=self.category)
            .filter(status="active")
            .filter(bidding_starts__lt=timezone.now())
            .order_by("-bidding_starts")
        )
        for listing in listings:
            close_listing_if_expired(listing)
        return listings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["cue"] = "no cue"  # this view wont higlight navigation
        context["category"] = self.category
        return context


## Listing Details


class ListingDetailView(detail.DetailView):
    model = Listing
    context_object_name = "listing"
    template_name = "auctions/listing_details.html"

    def get_object(self):
        listing = super().get_object()
        close_listing_if_expired(listing)
        return listing

    def get(self, request, *args, **kwargs) -> HttpResponse:
        # Avoids exception: object has no attribute 'object_list'
        self.object = self.get_object()
        context = self.get_context_data()

        # redirect to info page if bidding_starts is in the future (info page will be bid_history)
        if context["listing"].bidding_starts > timezone.now():
            return HttpResponseRedirect(
                reverse("listing-bid-history", kwargs={"listing_id": self.object.pk})
            )

        return render(request, "auctions/listing_details.html", context)


## Listing Comments and Replies


@login_required
def listing_comment(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    close_listing_if_expired(listing)
    if redirect_if_listing_has_closed(listing):
        # has to be a json response as the request was sent through a js script which is expecting back a json response
        return JsonResponse(
            {
                "message": "Comment did not go through. Listing was closed.",
            }
        )

    if request.method == "POST":

        # check that listing has not been edited by checking if bidding_starts changed
        print(f"\n{request.POST['bidding_starts']}\n")
        if redirect_if_listing_was_edited(
            user_date_str=request.POST["bidding_starts"], listing=listing
        ):
            return JsonResponse(
                {
                    "message": "Could not resolve action. Listing was edited.",
                    "reload": "this is a switch",
                }
            )

        comment_text = request.POST["comment"].strip()
        if comment_text:
            try:
                comment = Comment(
                    user=request.user,
                    listing=listing,
                    comment=comment_text,
                )
                comment.save()

            except IntegrityError:
                return Http404("Error saving comment.")

            return JsonResponse({"message": "Comment saved."})

        else:
            return JsonResponse({"message": "Empty comment. Not saved."})
    else:
        return Http404("Invalid request.")


@login_required
def listing_reply(request, comment_id):
    # comment_id is the id of the parent comment not the id of a reply
    try:
        comment = get_object_or_404(Comment, pk=comment_id)
    except Http404:
        return JsonResponse(
            {
                "message": "Could not resolve action. Listing was edited.",
                "reload": "this is a switch",
            }
        )

    close_listing_if_expired(comment.listing)
    if redirect_if_listing_has_closed(comment.listing):
        return JsonResponse(
            {
                "message": "Comment did not go through. Listing was closed.",
            }
        )

    if request.method == "POST":

        # check that listing has not been edited by checking if bidding_starts changed
        if redirect_if_listing_was_edited(
            user_date_str=request.POST["bidding_starts"], listing=comment.listing
        ):
            return JsonResponse(
                {
                    "message": "Could not resolve action. Listing was edited.",
                    "reload": "this is a switch",
                }
            )

        reply_text = request.POST["reply"].strip()
        reply_to = request.POST.get("reply_to", "")
        # the username will only return when a reply is made to a reply, not a reply to a comment.
        # When there is a reply to a comment, my javascript sends 'null' as the value of reply_to,
        # so here I set it back to "" so that it is not saved in the model's reply_to field
        if reply_to == "null":
            reply_to = ""
        if reply_text:
            try:
                reply = Comment(
                    user=request.user,
                    listing=comment.listing,
                    comment=reply_text,
                    status="reply",
                    reply_to=reply_to,
                )
                reply.save()
                # add to the manytomany relationship and save comment
                comment.comment_replies.add(reply)
                comment.save()

            except IntegrityError:
                return Http404("Error saving reply.")

            return JsonResponse({"message": "Reply saved."})

        else:
            return JsonResponse({"message": "Empty reply. Not saved."})
    else:
        return Http404("Invalid request.")


@login_required
def listing_get_min_bid(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(Listing, pk=listing_id)

        close_listing_if_expired(listing)
        if redirect_if_listing_has_closed(listing):
            return JsonResponse(
                {
                    "message": "Could not resolve action. Listing was closed.",
                    "reload": "this is a switch",
                }
            )

        if listing.seller == request.user:
            raise Http404("Action not allowed. Owner cannot bid on owned listing.")
        time.sleep(0.5)

        # get json
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)

        # check that listing has not been edited by checking if bidding_starts changed
        if redirect_if_listing_was_edited(
            user_date_str=body["bidding_starts"], listing=listing
        ):
            return JsonResponse(
                {
                    "message": "Could not resolve action. Listing was edited.",
                    "reload": "this is a switch",
                }
            )

        return JsonResponse(
            {
                "current_price": listing.current_price,
                "min_bid": f"{listing.get_min_bid_amount():.2f}",
            }
        )

    else:
        raise Http404("Get request not allowed.")


@login_required
def listing_set_bid(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(Listing, pk=listing_id)

        close_listing_if_expired(listing)
        if redirect_if_listing_has_closed(listing):
            return JsonResponse(
                {
                    "message": "Could not resolve action. Listing was closed.",
                    "reload": "this is a switch",
                }
            )

        if listing.seller == request.user:
            raise Http404("Action not allowed. Owner cannot bid on owned listing.")
        time.sleep(0.5)

        # get json
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        bid_amount = body["bid"]

        # check that listing has not been edited by checking if bidding_starts changed
        if redirect_if_listing_was_edited(
            user_date_str=body["bidding_starts"], listing=listing
        ):
            return JsonResponse(
                {
                    "message": "Could not resolve action. Listing was edited.",
                    "reload": "this is a switch",
                }
            )

        # validate bid_amount and send appropriate error message
        try:
            util.helper_validate_bid_amount(bid_amount)
        except ValueError as e:
            return JsonResponse(
                {
                    "current_price": listing.current_price,
                    "min_bid": f"{listing.get_min_bid_amount():.2f}",
                    "error": f"Your bid did not go through. {e}",
                }
            )

        # check current price is not updated
        if float(bid_amount) < listing.get_min_bid_amount():
            return JsonResponse(
                {
                    "current_price": listing.current_price,
                    "min_bid": f"{listing.get_min_bid_amount():.2f}",
                    "error": f"Your bid did not go through. Bid (${bid_amount}) is less than current minimun possible bid (${listing.get_min_bid_amount()}).",
                }
            )

        # create bid and update listing.winner and listing.bid_count (bid_count acts as a flag, very important)
        bid = Bid(bidder=request.user, listing=listing, amount=bid_amount)
        bid.save()

        listing.current_price = bid_amount
        listing.winner = request.user
        listing.bid_count += 1
        listing.save()

        return JsonResponse(
            {
                "current_price": listing.current_price,
                "min_bid": f"{listing.get_min_bid_amount():.2f}",
                # empty error triggers success message in browser
                "error": "",
            }
        )

    else:
        raise Http404("Get request not allowed.")


## Bid History


def listing_bid_history(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    close_listing_if_expired(listing)

    # for the bids table
    bids = listing.listing_bids.order_by("-date")

    # count bidders
    bidders_count = 0
    bidders_usernames = []
    for bid in bids:
        if bid.bidder not in bidders_usernames:
            bidders_usernames.append(bid.bidder)
            bidders_count += 1

    context = {
        "listing": listing,
        "bids": bids,
        "bidders_count": bidders_count,
    }

    # redirect to info page if bidding_starts is in the future (info page will be bid_history as well)
    if listing.bidding_starts > timezone.now():
        context["listing_has_not_started"] = "this is a switch"
        return render(request, "auctions/listing_bid_history.html", context)

    return render(request, "auctions/listing_bid_history.html", context)


## Close listing manually (seller only)


@login_required
def listing_close(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    # proceed only if active, otherwise redirect
    if listing.status == "active":
        if listing.seller != request.user:
            raise Http404("Access denied.")

        listing.status = "closed"
        # timezone aware
        listing.bidding_ended = timezone.now()
        listing.save()

    return HttpResponseRedirect(reverse("listing-details", kwargs={"pk": listing.pk}))


## Listing Categories


def categories(request):
    categories = Category.objects.all()
    # go over each category and check whether there is at least one listing available
    category_list = []
    for category in categories:
        category_dict = {}
        listing = Listing.objects.filter(category=category).first()
        if listing:
            if listing.status == "active" and (listing.bidding_starts < timezone.now()):
                available = True
            else:
                available = False
        else:
            available = False

        category_dict["category"] = category
        category_dict["available"] = available
        category_list.append(category_dict)

    context = {"categories": category_list}
    context["cue"] = "category"  # see ListingsListView
    return render(request, "auctions/listings_categories.html", context)


## Watchlist


class WatchlistListView(LoginRequiredMixin, ListingsListView):
    template_name = "auctions/listings_watchlist.html"

    def get_queryset(self):
        listings = self.request.user.watchlist.all().order_by("-bidding_starts")
        for listing in listings:
            close_listing_if_expired(listing)
        return listings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["cue"] = "watchlist"
        return context


@login_required
def watchlist_add(request, id):
    listing = get_object_or_404(Listing, pk=id)

    if listing in request.user.watchlist.all():
        raise Http404("watchlist already contains this listing")

    # the watchlist.add refers to the related name of the ManyToMany field, not to the ManyToMany field itself
    request.user.watchlist.add(listing)
    request.user.watchlist_item_count += 1
    request.user.save()

    listing.watcher_count += 1
    listing.save()

    return HttpResponse("ok")


@login_required
def watchlist_remove(request, id):
    listing = get_object_or_404(Listing, pk=id)

    if listing not in request.user.watchlist.all():
        raise Http404("watchlist does not contain this listing")

    request.user.watchlist.remove(listing)
    request.user.watchlist_item_count -= 1
    request.user.save()

    listing.watcher_count -= 1
    listing.save()

    return HttpResponse("ok")


## Owned Listings


class ListingsOwnedListView(LoginRequiredMixin, ListingsListView):
    template_name = "auctions/listings_owned.html"

    def get_queryset(self):
        listings = (
            Listing.objects.all()
            .filter(seller=self.request.user)
            .order_by("-bidding_starts")
        )
        for listing in listings:
            close_listing_if_expired(listing)
        return listings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["cue"] = "owned"
        # add context to flag 'active' or 'closed' listing sort-by
        return context


## Create/Edit listing


@login_required
def listing_new(request):
    # date values to initialize the template's date input fields
    date = {
        "starts_min": datetime.datetime.now().isoformat()[:16],
        "ends_max": (
            datetime.datetime.fromisoformat(
                (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
            )
            + datetime.timedelta(hours=23, minutes=59)
        ).isoformat()[:16],
        "lasts_min": 1,
        "lasts_max": 3,
    }
    context = {"date": date}
    # visual indication that user is in the create page
    context["cue"] = "create"

    if request.method == "POST":
        # this part of the context is only to send back the user input

        context["title"] = request.POST["title"].strip()
        context["description"] = request.POST["description"].strip()
        context["category"] = request.POST["category"].strip()
        context["starting_price"] = request.POST["starting_price"].strip()
        context["bidding_starts"] = request.POST["bidding_starts"].strip()
        context["duration"] = request.POST["duration"].strip()
        if request.FILES:
            context["imageReminder"] = "Re-enter the image."

        # extracting post data because I need to modify some values before passing it to the form
        # so wont be doing: form = ListingModelForm(request.POST, request.FILES)
        data = {
            "title": request.POST["title"].strip(),
            "description": request.POST["description"].strip(),
            "category": request.POST["category"],
            "starting_price": request.POST["starting_price"].strip(),
            "bidding_starts": request.POST["bidding_starts"],
            "duration": request.POST["duration"].strip(),
        }

        # giving duration 0 value if it comes empty
        if data["duration"] == "":
            data["duration"] = "0 00:00:00"
        else:
            data["duration"] = data["duration"] + " 00:00:00"

        # giving bidding_starts .now() value if it comes empty
        if data["bidding_starts"] == "":
            data["bidding_starts"] = datetime.datetime.now()

        form = ListingModelForm(data, request.FILES)
        if form.is_valid():

            listing = form.save(commit=False)
            listing.seller = request.user
            listing.current_price = form.cleaned_data["starting_price"]
            listing.save()

            return HttpResponseRedirect(
                reverse("listing-details", kwargs={"pk": listing.pk})
            )

    else:
        context["form"] = ListingModelForm()
        return render(request, "auctions/listing_form_new.html", context)

    context["form"] = form
    return render(request, "auctions/listing_form_new.html", context)


# parts that differ from create view are marked 'DIFFERENT' to aid with possible refactoring in the future
@login_required
def listing_edit(request, pk):
    # (DIFFERENT) >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # check that user accessing view is the listing seller
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user:
        raise Http404("Access denied.")

    close_listing_if_expired(listing)
    if redirect_if_listing_has_closed(listing):
        return HttpResponseRedirect(
            reverse("listing-details", kwargs={"pk": listing.pk})
        )

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # date values to initialize the template's date input fields
    date = {
        "starts_min": datetime.datetime.now().isoformat()[:16],
        "ends_max": (
            datetime.datetime.fromisoformat(
                (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
            )
            + datetime.timedelta(hours=23, minutes=59)
        ).isoformat()[:16],
        "lasts_min": 1,
        "lasts_max": 3,
    }
    context = {"date": date}

    if request.method == "POST":
        # this part of the context is only to send back the user input
        context["title"] = request.POST["title"].strip()
        context["description"] = request.POST["description"].strip()
        context["category"] = request.POST["category"].strip()
        context["starting_price"] = request.POST["starting_price"].strip()
        context["bidding_starts"] = request.POST["bidding_starts"].strip()
        context["duration"] = request.POST["duration"].strip()
        if request.FILES:
            context["imageReminder"] = "Re-enter the image."

        # extracting post data because I need to modify some values before passing it to the form
        # so wont be doing: form = ListingModelForm(request.POST, request.FILES)
        data = {
            "title": request.POST["title"].strip(),
            "description": request.POST["description"].strip(),
            "category": request.POST["category"],
            "starting_price": request.POST["starting_price"].strip(),
            "bidding_starts": request.POST["bidding_starts"],
            "duration": request.POST["duration"].strip(),
        }

        # giving duration 0 value if it comes empty
        if data["duration"] == "":
            data["duration"] = "0 00:00:00"
        else:
            data["duration"] = data["duration"] + " 00:00:00"

        # giving bidding_starts .now() value if it comes empty
        if data["bidding_starts"] == "":
            data["bidding_starts"] = datetime.datetime.now()

        form = ListingModelForm(data, request.FILES)
        if form.is_valid():

            # (DIFFERENT) >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # save the new values, erase old image if new one is provided
            listing.title = form.cleaned_data["title"]
            listing.description = form.cleaned_data["description"]
            listing.category = form.cleaned_data["category"]
            listing.starting_price = form.cleaned_data["starting_price"]
            listing.current_price = form.cleaned_data["starting_price"]
            listing.bidding_starts = form.cleaned_data["bidding_starts"]
            listing.duration = form.cleaned_data["duration"]
            # if new pic sent, erase old one
            if request.FILES:
                # by default any pic name will be 'product_pics/filename' unless user did not provide a pic, in which case it is 'default.jpg'
                if listing.image.name != "default.jpg":
                    current_filename = listing.image.name
                    if default_storage.exists(current_filename):
                        default_storage.delete(current_filename)

                listing.image = form.cleaned_data["image"]

            # Reset bids, bid_count, comments
            # Mark was_edited, and increase edit_count

            listing.was_edited = True
            listing.edit_count += 1
            listing.listing_bids.all().delete()
            listing.listing_comments.all().delete()
            listing.bid_count = 0

            listing.save()

            return HttpResponseRedirect(
                reverse("listing-details", kwargs={"pk": listing.pk})
            )

    else:
        # (DIFFERENT) >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # this part of the context is for sending back the user data to be edited
        context["title"] = listing.title
        context["description"] = listing.description
        context["starting_price"] = listing.starting_price

        # for the category (input type=select), and image link (through the listing object) and name
        context["form"] = ListingModelForm(instance=listing)
        context["listing"] = listing
        if listing.image.name == "default.jpg":
            context["imageName"] = listing.image.name
        else:
            context["imageName"] = listing.image.name[13:]
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        return render(request, "auctions/listing_form_edit.html", context)

    context["form"] = form
    # (DIFFERENT) >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    context["listing"] = listing
    if listing.image.name == "default.jpg":
        context["imageName"] = listing.image.name
    else:
        context["imageName"] = listing.image.name[13:]
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    return render(request, "auctions/listing_form_edit.html", context)


## Login/Logout/Register Views


def login_view(request):
    if request.method == "POST":

        # These two variables are only used to send back the exact data the user sent for display
        username = request.POST["username"].strip()
        password = request.POST["password"].strip()

        form = LoginUserForm(request.POST)

        # if not valid, 'form' passed to the 'context' will include the error messages
        if form.is_valid():

            cleaned_username = form.cleaned_data["username"]
            cleaned_password = form.cleaned_data["password"]

            user = authenticate(
                request, username=cleaned_username, password=cleaned_password
            )

            # Check if authentication successful
            if user is not None:
                login(request, user)
                if request.GET.get("next"):
                    return HttpResponseRedirect(request.GET.get("next"))
                else:
                    return HttpResponseRedirect(reverse("index"))
            else:
                return render(
                    request,
                    "auctions/login.html",
                    {
                        "message": "Invalid username and/or password.",
                        "username": username,
                        "password": password,
                        "next": request.GET.get("next", ""),
                    },
                )
    else:
        # logic so that user is not sent back to /login or /register after login in
        next_val = request.GET.get("next", "")
        if next_val:
            if next_val == "/login" or next_val == "/register" or next_val == "/logout":
                context = {}
            else:
                context = {"next": next_val}

        return render(request, "auctions/login.html", context)

    # if POST but form.is_valid() failed:
    context = {
        "form": form,
        "username": username,
        "password": password,
        "next": request.GET.get("next", ""),
    }
    return render(request, "auctions/login.html", context)


# @login_required
def logout_view(request):
    logout(request)
    return render(
        request, "auctions/login.html", context={"logout": "this is a switch"}
    )


def register(request):
    if request.method == "POST":

        # These four variables are only used to send back the exact data the user sent for display
        username = request.POST["username"].strip()
        email = request.POST["email"].strip()
        password = request.POST["password"].strip()
        confirmation = request.POST["confirmation"].strip()

        context = {
            "username": username,
            "email": email,
            "password": password,
            "confirmation": confirmation,
        }

        if not (username and email and password and confirmation):
            context["message"] = "All fields are required."
            return render(request, "auctions/register.html", context)

        if password != confirmation:
            context["message"] = "Passwords must match."
            return render(request, "auctions/register.html", context)

        form = RegisterUserModelForm(request.POST)

        # if not valid, 'form' passed to the 'context' will include the error messages
        if form.is_valid():

            cleaned_username = form.cleaned_data["username"]
            cleaned_email = form.cleaned_data["email"]
            cleaned_password = form.cleaned_data["password"]

            # Attempt to create new user
            try:
                user = User.objects.create_user(
                    cleaned_username, cleaned_email, cleaned_password
                )
                user.save()
            except IntegrityError:
                # because modelform has been implemented, it is possible the code below never gets executed as modelform already checks this
                context["message"] = "Username already taken."
                return render(request, "auctions/register.html", context)

            login(request, user)
            return render(request, "auctions/register_success.html")

    else:
        return render(request, "auctions/register.html", {"on_get": "this is a switch"})

    # if POST but form.is_valid() failed, add 'form' to 'context'
    context["form"] = form
    context["focus"] = "js-focus"  # also a switch
    return render(request, "auctions/register.html", context)
