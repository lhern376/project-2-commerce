from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Listing, Bid, Comment

# Register your models here.
admin.site.register(User, UserAdmin)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "category_name", "category_string")


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    ## List View of Admin site
    list_display = (
        "id",
        "seller",
        "category",
        "date_created",
        "status",
        "starting_price",
        "current_price",
    )

    list_filter = (
        "category",
        "date_created",
        "status",
        "starting_price",
        "current_price",
    )


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    ## List View of Admin site
    list_display = ("id", "bidder", "listing", "amount", "date")

    list_filter = ("amount", "date")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    ## List View of Admin site
    list_display = ("id", "user", "date")

    list_filter = ("date",)
