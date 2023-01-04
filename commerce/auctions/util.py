import re

## Helper functions

PRICE_OVERFLOW = 100000

## Filter
def helper_listView_sort(listings, min, max, criteria) -> tuple:

    # this dict is sent back to the template for some extra logic
    search_criteria = {}

    matches_min = re.search(r"^\d*\.?\d*$", min)
    matches_max = re.search(r"^\d*\.?\d*$", max)

    if matches_min and matches_max:

        if min == "" or min == ".":
            min = 0
        else:
            min = float(min)

        # 0 represents not set. So if 'max' is not set, check whether 'min' is set to filter by 'min'
        if max == "" or max == ".":
            max = 0
            if min != 0 and min < PRICE_OVERFLOW:
                search_criteria["price_range_hint"] = f"Higher than ${min:,.2f}"
                listings = listings.filter(current_price__range=(min, 100000))
        else:
            max = float(max)
            if max > PRICE_OVERFLOW:
                max = 0
                search_criteria[
                    "price_range_hint"
                ] = f"Invalid. Exceeds ${PRICE_OVERFLOW:,.2f}"

        # if the below condition is False, then both 'min' and 'max' are ignored.
        if not ((max == 0) or (min > max)):
            listings = listings.filter(current_price__range=(min, max))
            search_criteria = {
                "min": f"{min:,.2f}",
                "max": f"{max:,.2f}",
            }

    else:
        search_criteria["price_range_hint"] = f"Invalid 'min' and/or 'max'."

    # sort criteria
    descriptive_criteria = ""
    if criteria == "least":
        listings = listings.order_by("current_price")
        descriptive_criteria = "Lowest price"
    elif criteria == "most":
        listings = listings.order_by("-current_price")
        descriptive_criteria = "Highest price"
    elif criteria == "newest":
        listings = listings.order_by("-date_created")
        descriptive_criteria = "Latest"
    elif criteria == "oldest":
        listings = listings.order_by("date_created")
        descriptive_criteria = "Oldest"
    elif criteria == "bid_count_most":
        listings = listings.order_by("-bid_count")
        descriptive_criteria = "Most bids"
    elif criteria == "bid_count_fewest":
        listings = listings.order_by("bid_count")
        descriptive_criteria = "Fewest bids"
    # default to latest/newest
    else:
        # listings = listings.order_by("-date_created")  # unnecessary, already ordered by this criteria at .get_queryset
        descriptive_criteria = "Latest"

    search_criteria["criteria"] = descriptive_criteria

    return (listings, search_criteria)


## Valid page number
# default to page 1 if does not match criteria
def helper_validate_page_number(p_number, total_number_of_pages) -> int:

    matches = re.search(r"^\d*$", p_number)
    try:
        p_number = int(p_number)
    except ValueError:
        return 1

    if matches and (1 <= p_number <= total_number_of_pages):

        return p_number
    else:
        return 1


## Valid bid amount
def helper_validate_bid_amount(bid):
    """Bid has to be a positive number and less than 100,000.00"""

    # valid number
    matches = re.search(r"^\d*\.?\d*$", bid)

    if not matches:
        raise ValueError("Enter a dollar amount.")

    # not empty
    if not bid:
        raise ValueError("Cannot be left empty.")

    # valid range
    if not (0 < float(bid) <= PRICE_OVERFLOW):
        raise ValueError("Amount has to be less than $100,000.00.")

    return True
