import random
import time
from faker import Faker
from playwright.sync_api import Page, Playwright, expect, sync_playwright


class UserPlacePage:
    """Page object for the public/user-facing Places page.

    Provides helpers to navigate to the Places listing, open filters,
    apply a tag filter (e.g., 'Cafe'), and assert that all visible
    results include the chosen tag.
    """

    def __init__(self, page: Page):
        self.page = page

        # Common UI elements used by the user flows
        self.home_link = page.get_by_role("link", name="Portal Pass").first
        self.discover_heading = page.get_by_role("heading", name="Discover Events & Places Near")
        self.places_link = page.get_by_role("link", name="Places").first
        self.search_box = page.get_by_role("textbox", name="Search places...")
        self.explore_heading = page.get_by_role("heading", name="Explore Places")
        self.filters_button = page.get_by_role("button", name="Filters")
        self.venue_location_combobox = page.get_by_role("combobox", name="Search venue location")
        self.search_radius_button = page.get_by_role("button", name="Search Radius")
        self.apply_filter_button = page.get_by_role("button", name="Apply Filter")

        # Generic locator for result cards; this is intentionally permissive
        # to work across slight markup differences. We then filter cards
        # by text when verifying tags.
        self.result_cards = page.locator("article")

    def navigate_to_home_user_portal(self, base_url: str = "https://portal-pass-web.weavers-web.com/"):
        self.page.goto(base_url)
        expect(self.home_link).to_be_visible()

    def go_to_places(self):
        self.places_link.click()
        expect(self.explore_heading).to_be_visible()

    def open_filters(self):
        self.filters_button.click()
        # give UI a moment to reveal the filter options
        self.page.wait_for_timeout(400)

    def select_tag(self, tag_name: str):
        # Click the tag button inside the filters (e.g., 'Cafe', 'Beach')
        self.page.get_by_role("button", name=tag_name).click()
        self.page.wait_for_timeout(200)

    def apply_filters(self):
        self.apply_filter_button.click()
        # Wait for results to refresh; tune timeout if needed
        self.page.wait_for_timeout(1000)

    def verify_all_listed_have_tag(self, tag_name: str) -> bool:
        """Verify every visible result card contains the given tag text.

        Returns True when all visible cards contain the tag, raises
        AssertionError otherwise.
        """
        total = self.result_cards.count()
        if total == 0:
            raise AssertionError("No result cards found after applying filter")

        # Count cards that contain the tag text
        matching = self.result_cards.filter(has_text=tag_name).count()

        if matching != total:
            # Collect a few failing card snippets for debugging
            failed_cards = []
            for i in range(min(5, total)):
                card = self.result_cards.nth(i)
                text = card.inner_text()[:200]
                if tag_name not in text:
                    failed_cards.append(text.replace("\n", " "))

            raise AssertionError(
                f"Not all result cards include tag '{tag_name}'. {matching}/{total} matched. "
                f"Examples of failing cards: {failed_cards}"
            )

        return True

    def verify_tag_count_and_all_have_tag(self, tag_name: str, expected_count: int | None = None) -> bool:
        """Verify tag presence across results.

        - If `expected_count` is an int: asserts that exactly that many tag occurrences exist.
        - If `expected_count` is None: only asserts at least one tag exists and all cards contain it.
        """
        self.page.wait_for_timeout(800)

        tag_elements = self.page.get_by_text(tag_name)
        matching_count = tag_elements.count()
        total_cards = self.result_cards.count()

        # Only enforce exact count if expected_count is provided (not None)
        if expected_count is not None and matching_count != expected_count:
            snippets = []
            for i in range(min(6, matching_count)):
                try:
                    snippets.append(tag_elements.nth(i).inner_text().strip())
                except Exception:
                    pass

            raise AssertionError(
                f"Expected {expected_count} '{tag_name}' results but found {matching_count}. Snippets: {snippets}"
            )

        # Ensure all visible cards contain the tag (when cards exist)
        if total_cards > 0:
            cards_with_tag = self.result_cards.filter(has_text=tag_name).count()
            if cards_with_tag != total_cards:
                failed = []
                for i in range(min(6, total_cards)):
                    try:
                        ctext = self.result_cards.nth(i).inner_text()[:200].replace("\n", " ")
                        if tag_name not in ctext:
                            failed.append(ctext)
                    except Exception:
                        pass
                raise AssertionError(
                    f"Found {total_cards} result cards but only {cards_with_tag} contain the tag '{tag_name}'. Examples: {failed}"
                )

        # If expected_count is None, at least one occurrence should exist
        if expected_count is None and matching_count == 0:
            raise AssertionError(f"No occurrences of tag '{tag_name}' were found.")

        return True


def run_filter_and_verify(playwright: Playwright, tag: str = "Cafe", expected_count: int | None = None) -> None:
    """Demo runner that opens the site, applies a filter tag and verifies results.

    This mirrors the manual script you recorded but uses the `UserPlacePage`
    page object methods.
    
    Args:
      tag: The tag to filter by (e.g., 'Cafe').
      expected_count: Optional. If set, asserts exactly this many results. If None, just verifies results exist and all have the tag.
    """
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    place_page = UserPlacePage(page)
    place_page.navigate_to_home_user_portal()
    place_page.go_to_places()
    place_page.open_filters()
    place_page.select_tag(tag)
    place_page.apply_filters()

    # verify results and that all include the chosen tag
    place_page.verify_tag_count_and_all_have_tag(tag, expected_count=expected_count)

    context.close()
    browser.close()
