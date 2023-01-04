from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse  # Used to generate URLs by reversing the URL patterns
from django.utils import timezone

from PIL import Image


class User(AbstractUser):

    ## usage:
    #   user.watchlist.add(listing_id)
    #   user.watchlist.remove(listing_id)
    #   user.watchlist.clear()  --> removes all the watchlist for a given user
    watchlist = models.ManyToManyField(
        "Listing", blank=True, related_name="user_watchlist"
    )

    watchlist_item_count = models.IntegerField(default=0)

    def __str__(self):
        return self.username

    def get_watchlist(self):
        return self.watchlist.all()

    def get_watchlist_by_recently_added(self):
        return self.watchlist.all().reverse()


class Category(models.Model):
    """Model representing an Auction Listing category"""

    category_string = models.CharField(
        max_length=300,
        unique=True,
        help_text="Enter dashed representation of the category name",
        null=True,
        blank=True,
    )

    category_name = models.CharField(
        max_length=200, unique=True, help_text="Enter listing category"
    )

    def __str__(self):
        return self.category_name

    class Meta:
        ordering = ["category_string"]


class Listing(models.Model):
    """Model representing an Auction Listing"""

    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="seller_listings"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Select a category for this listing",
    )

    title = models.CharField(max_length=300)

    description = models.TextField(
        max_length=1000, help_text="Enter a brief description of the listing"
    )

    starting_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    # remember to set current_price to starting_price in the views
    current_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    date_created = models.DateTimeField(default=timezone.now)

    listing_status = [
        ("active", "Active listing"),
        ("closed", "Closed listing"),
    ]

    status = models.CharField(
        max_length=6,
        choices=listing_status,
        default="active",
        help_text="Listing status",
    )

    was_edited = models.BooleanField(default=False)

    edit_count = models.IntegerField(default=0)

    bidding_starts = models.DateTimeField(default=timezone.now, blank=True, null=True)

    # set manually upon closing the listing
    bidding_ended = models.DateTimeField(blank=True, null=True)

    duration = models.DurationField(
        default=timezone.timedelta(days=0),
        null=True,
        blank=True,
        help_text="Enter the duration of the listing",
    )

    bid_count = models.IntegerField(default=0)

    watcher_count = models.IntegerField(default=0)

    winner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="won_listings",
    )

    # imageURL = models.URLField(
    #     max_length=500, blank=True, help_text="Enter an image URL"
    # )

    image = models.ImageField(
        default="default.jpg", upload_to="product_pics", null=True
    )

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this listing."""
        # return reverse("listing-detail", args=[str(self.id)])
        return reverse("listing-detail", kwargs={"pk": self.pk})

    ## Used formatting directly in template instead: <Posted on {{ value|date:"N d, Y - h:i A (T)" }}>
    # def get_readable_date(self):
    #     """Returns human readable creation date"""
    #     est = tz("US/Eastern")
    #     date = self.date_created.astimezone(est)
    #     format = "%b. %d, %Y - %I:%M %p (%Z)"
    #     return f"Posted on {date.strftime(format)}"

    class Meta:
        ordering = ["status", "-date_created"]

    # re-do this based on bidding_starts, duration, and current date
    @property
    def is_expired(self):
        """Determines if the listing is expired based on date_created, duration and current date."""
        # Note: whether duration is 0 is being verified. If duration is 0 the listing will be closed manually, so it is never expired
        if self.duration > timezone.timedelta(minutes=0):
            return bool(timezone.now() > (self.bidding_starts + self.duration))
        else:
            return False

    @property
    def listing_ends(self):
        """Returns when it ends or, if it does not end, returns 'No date set.'"""
        if self.duration > timezone.timedelta(minutes=0):
            return self.bidding_starts + self.duration
        else:
            return "No date set"

    # resizing the image on save (thumbnail() maintains aspect ratio)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 500 or img.width > 500:
            output_size = (500, 500)
            img.thumbnail(output_size)
            img.save(self.image.path)

    def get_listing_comments(self):
        """Returns comments for the listing ordered by most recent"""
        return self.listing_comments.order_by("-date")

    def get_min_bid_amount(self):
        """Returns the min bid amount possible given the current price"""
        if self.bid_count == 0:
            # the initial bid can be equal to starting price
            return self.starting_price

        else:
            current_price = float(self.current_price)

            if 0.01 <= current_price <= 0.99:
                return current_price + 0.05
            if 1.00 <= current_price <= 4.99:
                return current_price + 0.25
            if 5.00 <= current_price <= 24.99:
                return current_price + 0.50
            if 25.00 <= current_price <= 99.99:
                return current_price + 1.00
            if 100.00 <= current_price <= 249.99:
                return current_price + 2.50
            if 250.00 <= current_price <= 499.99:
                return current_price + 5.00
            if 500.00 <= current_price <= 999.99:
                return current_price + 10.00
            if 1000.00 <= current_price <= 2499.99:
                return current_price + 25.00
            if 2500.00 <= current_price <= 4999.99:
                return current_price + 50.00
            if current_price >= 5000.00:
                return current_price + 100.00


class Bid(models.Model):

    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_bids")

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="listing_bids"
    )

    amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.bidder.username}: {self.amount}"


class Comment(models.Model):

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="user_comments"
    )

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="listing_comments"
    )

    comment = models.TextField(max_length=1000, help_text="Enter a comment")

    date = models.DateTimeField(default=timezone.now)

    replies = models.ManyToManyField(
        "Comment", blank=True, related_name="comment_replies"
    )

    comment_status = [
        ("comment", "This is a comment"),
        ("reply", "This is a reply"),
    ]

    status = models.CharField(
        max_length=7,
        choices=comment_status,
        default="comment",
        help_text="Comment status",
    )

    reply_to = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"({self.date.astimezone()}) {self.user.username}: {self.comment}"

    def get_comment_replies(self):
        """Returns replies for a comment ordered by least recent"""
        return self.comment_replies.order_by("date")
