import os
import random
import pytest
from faker import Faker
from playwright.sync_api import expect
import time

from pages.admin.place_listing_page import PlaceListing
from pages.admin.event_creation_page import EventCreationPage

# Global variable to count created places across tests
created_places_count = 0
created_chennai_place_name = None


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
    global created_chennai_place_name

    dashboard_page.click_place_listing()
    dashboard_page.page.wait_for_timeout(1000)

    created_places = []
    
    for idx, place in enumerate(place_listing_data, 1):
        place_listing_page.click_add_new_place()
        place_listing_page.page.wait_for_timeout(500)

        # Create a unique name by appending 4 random words from Faker
        unique_suffix = " " + " ".join(fake.words(4))
        unique_name = place["place_name"] + unique_suffix

        if place["place_name"] == "Chennai Marina Place":
            created_chennai_place_name = unique_name

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


@pytest.mark.regression
def test_06_create_event_for_place(dashboard_page, place_listing_page: PlaceListing, event_creation_page: EventCreationPage):
    """
    Test creating an event under a specific place.
    Taps on 'Chennai Marina Place ...', clicks 'Create Event',
    uses the POM create_event helper with fill_venue=False,
    and verifies the event is successfully created and shown in the Event Repository under that place's location.
    """
    global created_chennai_place_name

    dashboard_page.click_place_listing()
    dashboard_page.page.wait_for_timeout(1000)

    # Use the Chennai place name that was created in test_05
    target_place = created_chennai_place_name or "Chennai Marina Place"
    print(f"🔍 Searching for place: '{target_place}'")

    # Search for the place
    place_listing_page.search_place(target_place)

    # Tap on that place in the table
    place_span = place_listing_page.page.locator(f"//span[normalize-space()='{target_place}']").first
    expect(place_span).to_be_visible()
    place_span.click()
    
    # Wait for the details page to load
    place_listing_page.page.wait_for_url("**/place/details/*", timeout=10000)
    print("ℹ️ Navigated to Place Details page.")

    # Tap on Create Event: //span[normalize-space()='Create Event']
    create_event_btn = place_listing_page.page.locator("//span[normalize-space()='Create Event']").first
    expect(create_event_btn).to_be_visible()
    create_event_btn.click()

    # Wait for the Create Event page to load
    place_listing_page.page.wait_for_url("**/event/create", timeout=10000)
    print("ℹ️ Navigated to Create Event page from Place Details.")

    # Pick a random image from data/images/ under 2.5 MB
    test_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.abspath(os.path.join(test_dir, "../../data/images"))
    safe_images = []
    for f in os.listdir(image_dir):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            full_path = os.path.join(image_dir, f)
            if os.path.getsize(full_path) < 2500000:
                safe_images.append(f)
                
    assert len(safe_images) > 0, "No mock images under 2.5 MB found in data/images!"
    random_image_name = random.choice(safe_images)
    random_image_path = os.path.join(image_dir, random_image_name)

    # Call create_event function with fill_venue=False (since venue is pre-filled)
    unique_event_title = f"Associated Event Under Place {random.randint(1000, 9999)}"
    print(f"📝 Creating event: '{unique_event_title}' under place '{target_place}'")

    event_creation_page.create_event(
        title=unique_event_title,
        venue="",
        start_day="15",
        end_day="18",
        start_time="10:00",
        end_time="18:00",
        description=fake.paragraph(nb_sentences=3),
        website=fake.url(),
        email=fake.ascii_free_email(),
        phone="5551234567",
        notes="Created under place details.",
        image_path=random_image_path,
        fill_venue=False  # Skip filling venue since it is pre-filled with the Place
    )

    # Wait for redirection to Event Repository
    place_listing_page.page.wait_for_url("**/event", timeout=10000)
    print("ℹ️ Event submitted successfully. Redirected to Event Repository.")

    # Verify that the event is listed successfully in the repository under that place location
    event_creation_page.search_event(unique_event_title)
    
    # Locate the row for the created event
    row = event_creation_page.get_row_by_title(unique_event_title)
    expect(row).to_be_visible()

    # Assert that the location column contains 'Chennai'
    location_cell = row.locator("td").nth(2)
    expect(location_cell).to_contain_text("Chennai")

    print(f"✅ Successfully verified that event '{unique_event_title}' is created under place '{target_place}' (Location: Chennai).")
