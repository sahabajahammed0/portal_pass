import os
import pytest
import random
from faker import Faker
from playwright.sync_api import expect

fake = Faker()

# Global variable to share the created event's name from TC02 to TC03
created_event_title = None
@pytest.mark.regression
def test_tc01_empty_form_validation(
    login_page,
    dashboard_page,
    event_creation_page,
):
    """
    TC01: Verify validation error messages when submitting empty Event Creation form.
    """
    # 1. Sign in to the portal
    login_page.sign_in_to_be_visiable()
    login_page.login("admin.portal@yopmail.com", "Admin1234!")
    login_page.admin_dashboard_visable()

    # 2. Navigate to Event Repository
    dashboard_page.click_event_reporsitory()

    # 3. Open Create Event form
    event_creation_page.click_create_event()

    # 4. Submit the empty form
    event_creation_page.submit_event()

    # 5. Verify all required field validation messages are displayed
    event_creation_page.verify_validation_errors()
    print("✅ TC01: Successfully verified empty event creation form validation errors.")

@pytest.mark.regression
def test_tc02_create_event_with_fake_data(
    login_page,
    dashboard_page,
    event_creation_page,
):
    """
    TC02: Verify successful creation of an event using random fake data, category, and image.
    """
    global created_event_title

    # 1. Sign in to the portal
    login_page.sign_in_to_be_visiable()
    login_page.login("admin.portal@yopmail.com", "Admin1234!")
    login_page.admin_dashboard_visable()

    # 2. Navigate to Event Repository
    dashboard_page.click_event_reporsitory()

    # 3. Open Create Event form
    event_creation_page.click_create_event()

    # 4. Pick a random image from data/images/ and upload it
    image_dir = os.path.abspath("data/images")
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    assert len(image_files) > 0, "No mock images found in data/images!"
    random_image_name = random.choice(image_files)
    random_image_path = os.path.join(image_dir, random_image_name)
    event_creation_page.upload_event_image(random_image_path)
    print(f"📸 Uploaded random image: {random_image_name}")

    # 5. Fill out event details with Faker/fake filler
    fake_title = f"Fake Event {fake.word().capitalize()} {random.randint(1000, 9999)}"
    created_event_title = fake_title  # Save to global variable for TC03
    event_creation_page.fill_title(fake_title)
    
    # Fill venue with Google Autocomplete fallback support
    event_creation_page.fill_venue("New York")

    # Select random start date and end date from calendar
    event_creation_page.select_start_date("15")
    event_creation_page.select_end_date("18")

    # Fill start and end times
    event_creation_page.fill_times("10:00", "18:00")

    # Select a random category from the dropdown
    event_creation_page.select_random_category()

    # Fill in description, website, contact info, and notes
    event_creation_page.fill_description(fake.paragraph(nb_sentences=3))
    event_creation_page.fill_contact_info(
        website=fake.url(),
        email=fake.ascii_free_email(),
        phone="5551234567"
    )
    event_creation_page.fill_notes(f"Automated test event created via Pytest on {fake.date()}.")

    # 6. Submit the event
    event_creation_page.submit_event()
    print("📤 Submitted the event creation form.")

    # 7. Verify the event is created and displayed in the event list/table
    # Wait for the drawer to close (the Create Event heading should not be visible anymore)
    expect(event_creation_page.heading_create_event).not_to_be_visible()

    # Search for the created event
    event_creation_page.search_event(fake_title)

    # Verify that the created event row exists in the table
    event_creation_page.verify_event_in_list(fake_title)
    print(f"✅ TC02: Successfully verified creation of event '{fake_title}'.")

@pytest.mark.regression
def test_tc03_search_created_event(
    login_page,
    dashboard_page,
    event_creation_page,
):
    """
    TC03: Search and verify the event created in TC02.
    """
    global created_event_title
    
    # Ensure TC02 ran and set the global variable
    assert created_event_title is not None, "No event title was stored by TC02!"

    # 1. Sign in to the portal
    login_page.sign_in_to_be_visiable()
    login_page.login("admin.portal@yopmail.com", "Admin1234!")
    login_page.admin_dashboard_visable()

    # 2. Navigate to Event Repository
    dashboard_page.click_event_reporsitory()

    # 3. Search for the event title stored from TC02
    print(f"🔍 Searching for event created in TC02: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # 4. Verify that the event is listed in the search results table
    event_creation_page.verify_event_in_list(created_event_title)
    print(f"✅ TC03: Successfully verified that event '{created_event_title}' shows up in search list.")
