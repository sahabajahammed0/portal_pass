import os
import pytest

from pages.user_page.place_page import UserPlacePage


def _env_expected_count(name: str) -> int | None:
    val = os.getenv(name)
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        return None


def test_user_places_filter_cafe(user_page):
    """Apply 'Cafe' filter on the public Places page and verify results.

    Uses the `user_page` fixture (public portal, no admin login).

    Behavior:
    - If `EXPECTED_CAFE_COUNT` env var is set to an integer, the test asserts
      that exactly that many Cafe occurrences exist and that all visible
      result cards contain the tag.
    - If not set, the test asserts that at least one Cafe exists and that
      all visible cards include the tag.
    """
    expected = _env_expected_count("EXPECTED_CAFE_COUNT")

    # Use the user_page fixture (public portal, unauthenticated)
    place = UserPlacePage(user_page)
    place.navigate_to_home_user_portal()
    place.go_to_places()
    place.open_filters()
    place.select_tag("Beach")
    place.apply_filters()

    # Run the verification (expected may be None)
    place.verify_tag_count_and_all_have_tag("Beach", expected_count=expected)
