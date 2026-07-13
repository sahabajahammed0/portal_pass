import pytest
from faker import Faker
from playwright.sync_api import expect
import time

from pages.admin.place_listing_page import PlaceListing

# Global variable to count created places across tests
created_places_count = 0

fake = Faker()

@pytest.mark.regression
def test_01_place_listing_page_visible(dashboard_page, place_listing_page: PlaceListing):
    dashboard_page.click_place_listing()
    dashboard_page.page.wait_for_timeout(1000)

    place_listing_page.verify_place_listing_page_visible()
    print("✅ Place Listing Management page header and Add New button are visible.")

@pytest.mark.regression
def test_02_place_listing_empty_form_validation(dashboard_page, place_listing_page: PlaceListing):
    dashboard_page.click_place_listing()
    dashboard_page.page.wait_for_timeout(1000)

    place_listing_page.click_add_new_place()
    place_listing_page.submit_place_form()
    place_listing_page.verify_place_validation_errors()
    print("✅ Verified Place Listing validation errors when submitting an empty form.")


@pytest.mark.regression
def test_04_add_place_listing(dashboard_page, place_listing_page: PlaceListing, place_listing_data):
    """
    Test creating a place with Google autocomplete venue selection using JSON data.
    When entering 'Kolkata', Google autocomplete appears.
    Select first option via keyboard, city/state auto-populate, only postal code needed.
    Then search and verify the place was created successfully.
    """
    dashboard_page.click_place_listing()
    dashboard_page.page.wait_for_timeout(1000)

    place_listing_page.click_add_new_place()

    # Use first place from JSON (Kolkata) but append a 4-word unique suffix
    kolkata_place = place_listing_data[0]
    unique_suffix = " " + " ".join(fake.words(4))
    unique_place_name = kolkata_place["place_name"] + unique_suffix
    place_listing_page.fill_place_form_with_venue_location(
        venue_name=kolkata_place["venue_name"],
        postal_code=kolkata_place["postal_code"],
        place_name=unique_place_name
    )

    place_listing_page.submit_place_form()
    place_listing_page.page.wait_for_timeout(2000)

    # Search and verify the created place using the unique name
    place_listing_page.search_place(unique_place_name)
    place_listing_page.verify_place_in_list(unique_place_name)

    expect(place_listing_page.add_new_btn).to_be_visible()
    print(f"✅ Successfully created place '{unique_place_name}' and verified in listing.")
    time.sleep(2)
    place_listing_page.edit_place_listing()
    place_listing_page.submit_save_place()
    place_listing_page.search_place(unique_place_name)
    place_listing_page.verify_place_in_list(unique_place_name)
    place_listing_page.delete_place_listing()
    
    
    


@pytest.mark.regression
def test_05_place_listing_create_multiple_venues(dashboard_page, place_listing_page: PlaceListing, place_listing_data):
    """
    Test creating multiple places from place_listing.json data.
    Each iteration uses venue location with Google autocomplete and postal code.
    After all creations, search and verify each place in the listing.
    """
    dashboard_page.click_place_listing()
    dashboard_page.page.wait_for_timeout(1000)

    created_places = []
    
    for idx, place in enumerate(place_listing_data, 1):
        place_listing_page.click_add_new_place()
        place_listing_page.page.wait_for_timeout(500)

        # Create a unique name by appending 4 random words from Faker
        unique_suffix = " " + " ".join(fake.words(4))
        unique_name = place["place_name"] + unique_suffix

        place_listing_page.fill_place_form_with_venue_location(
            venue_name=place["venue_name"],
            postal_code=place["postal_code"],
            place_name=unique_name
        )

        place_listing_page.submit_place_form()
        place_listing_page.page.wait_for_timeout(2000)
        created_places.append(unique_name)
        print(f"✅ [{idx}/{len(place_listing_data)}] Created place '{unique_name}' with venue '{place['venue_name']}'")

    # Verify all created places in the listing
    dashboard_page.click_place_listing()
    dashboard_page.page.wait_for_timeout(1000)
    
    for place_name in created_places:
        place_listing_page.search_place(place_name)
        place_listing_page.verify_place_in_list(place_name)
        print(f"✅ Verified place '{place_name}' is successfully listed.")
    
    expect(place_listing_page.add_new_btn).to_be_visible()
    print(f"✅ Successfully created and verified all {len(created_places)} places from JSON data.")


