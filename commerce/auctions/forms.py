from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import (
    validate_password,
    get_default_password_validators,
)
from django.utils.translation import gettext_lazy as _

from django.forms import ModelForm
from .models import User, Listing, Category
from django.utils import timezone
import datetime
import re


## Registration and Login


class RegisterUserModelForm(ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean_password(self):
        data = self.cleaned_data["password"]

        # raises ValidationError, or None if valid
        validate_password(data, password_validators=get_default_password_validators())

        return data


class LoginUserForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100)


## Create and Edit Listing


class ListingModelForm(ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Select a category",
        widget=forms.Select(attrs={"class": "form-select text-secondary"}),
    )

    class Meta:
        model = Listing
        fields = [
            "title",
            "description",
            "category",
            "starting_price",
            # optional:
            "bidding_starts",
            "duration",
            "image",
        ]

    def clean_starting_price(self):
        """Starting price has to be positive and less than 100,000.00"""
        data = self.cleaned_data["starting_price"]
        PRICE_OVERFLOW = 100000

        if not data:
            raise ValidationError(_("Cannot be empty or $0."))

        if not (0 < data <= PRICE_OVERFLOW):
            raise ValidationError(
                _(
                    "Invalid amount. Starting price has to be higher than $0 and less than $100,000.00"
                )
            )

        return data

    def clean_duration(self):
        """Duration cannot be greater than 7 days"""
        data = self.cleaned_data.get("duration", "")

        if data:
            if data > datetime.timedelta(days=3):
                raise ValidationError(
                    _("Invalid duration. The duration cannot be greater than 3 days.")
                )
            if data < datetime.timedelta(days=0):
                raise ValidationError(
                    _("Invalid duration. The duration cannot be less than 0.")
                )
        return data

    def clean_bidding_starts(self):
        """Starting date cannot be in the past or greater than 3 days ahead"""
        data = self.cleaned_data.get("bidding_starts", "")

        min = timezone.make_aware(
            datetime.datetime.now() - datetime.timedelta(hours=1),
            timezone.get_default_timezone(),
        )

        max = timezone.make_aware(
            datetime.datetime.fromisoformat(
                (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
            )
            + datetime.timedelta(hours=23, minutes=59)
        )

        if data:
            # Check if a date is not in the past.
            if data < min:
                raise ValidationError(
                    _("Invalid date. Starting date cannot be in the past.")
                )

            # Check if a date is in the allowed range (max. 3 days from today).
            if data > max:
                raise ValidationError(
                    _("Invalid date. Starting date cannot be more than 3 days ahead.")
                )

        return data
