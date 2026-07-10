import os
import random
import pytest
from faker import Faker
from playwright.sync_api import expect

fake = Faker()

# Global variables to share the created event's data from TC02 to other tests
created_event_title = None
created_event_venue = "New York"
created_event_source = "Manual Entry"
created_event_status = "Active"
created_event_category = None


def test_tc01_empty_form_validation(
    event_repo,
    event_creation_page,
):
    """
    TC01: Verify validation error messages when submitting empty Event Creation form.
    """
    # Open Create Event form
    event_creation_page.click_create_event()

    # Submit the empty form
    event_creation_page.submit_event()

    # Verify all required field validation messages are displayed
    event_creation_page.verify_validation_errors()
    print("✅ TC01: Successfully verified empty event creation form validation errors.")


def test_tc02_create_event_with_fake_data(
    event_repo,
    event_creation_page,
):
    """
    TC02: Verify successful creation of an event using random fake data, category, and image.
    """
    global created_event_title, created_event_category, created_event_venue

    # Pick a random venue from a list of major cities
    venues = ["New York", "Los Angeles", "Chicago", "London", "Paris", "Tokyo", "Sydney", "Berlin", "Toronto"]
    created_event_venue = random.choice(venues)
    print(f"📍 Selected venue: {created_event_venue}")

    # Open Create Event form
    event_creation_page.click_create_event()

    # Pick a random image from data/images/ under 2.5 MB and upload it
    image_dir = os.path.abspath("data/images")
    safe_images = []
    for f in os.listdir(image_dir):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            full_path = os.path.join(image_dir, f)
            if os.path.getsize(full_path) < 2500000:  # Less than 2.5 MB
                safe_images.append(f)
                
    assert len(safe_images) > 0, "No mock images under 2.5 MB found in data/images!"
    random_image_name = random.choice(safe_images)
    random_image_path = os.path.join(image_dir, random_image_name)
    event_creation_page.upload_event_image(random_image_path)
    print(f"📸 Uploaded random image: {random_image_name}")

    # Fill out event details with Faker/fake filler
    fake_title = f"Fake Event {fake.word().capitalize()} {random.randint(1000, 9999)}"
    created_event_title = fake_title  # Save to global variable for TC03
    event_creation_page.fill_title(fake_title)
    
    # Fill venue with Google Autocomplete fallback support
    event_creation_page.fill_venue(created_event_venue)

    # Select random start date and end date from calendar
    event_creation_page.select_start_date("15")
    event_creation_page.select_end_date("18")

    # Fill start and end times
    event_creation_page.fill_times("10:00", "18:00")

    # Select a random category from the dropdown and store it
    created_event_category = event_creation_page.select_random_category()
    print(f"🏷️ Selected category: {created_event_category}")

    # Fill in description, website, contact info, and notes
    event_creation_page.fill_description(fake.paragraph(nb_sentences=3))
    event_creation_page.fill_contact_info(
        website=fake.url(),
        email=fake.ascii_free_email(),
        phone="5551234567"
    )
    event_creation_page.fill_notes(f"Automated test event created via Pytest on {fake.date()}.")

    # Submit the event
    event_creation_page.submit_event()
    print("📤 Submitted the event creation form.")

    # Verify the event is created and displayed in the event list/table
    # Wait for the drawer to close (the Create Event heading should not be visible anymore)
    expect(event_creation_page.heading_create_event).not_to_be_visible()

    # Search for the created event
    event_creation_page.search_event(fake_title)

    # Verify that the created event row exists in the table
    event_creation_page.verify_event_in_list(fake_title)
    print(f"✅ TC02: Successfully verified creation of event '{fake_title}'.")


def test_tc03_search_created_event(
    event_repo,
    event_creation_page,
):
    """
    TC03: Search and verify the event created in TC02.
    """
    global created_event_title
    
    # Ensure TC02 ran and set the global variable
    assert created_event_title is not None, "No event title was stored by TC02!"

    # Search for the event title stored from TC02
    print(f"🔍 Searching for event created in TC02: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # Verify that the event is listed in the search results table
    event_creation_page.verify_event_in_list(created_event_title)
    print(f"✅ TC03: Successfully verified that event '{created_event_title}' shows up in search list.")


def test_tc04_active_events_api_verification(
    event_repo,
    page,
):
    """
    TC04: Verify that filtering events by 'Active' status and changing rows per page to 100
    returns only events with systemStatus 'ACTIVE' in the API responses across all pages.
    """
    # List to store captured API responses as tuples of (url, json_data)
    captured_responses = []

    def handle_response(response):
        if "events/all-events" in response.url:
            try:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    captured_responses.append((response.url, response.json()))
            except Exception:
                pass

    # Register response listener
    page.on("response", handle_response)

    # Select 'Active' status from dropdown
    page.get_by_test_id("event-status-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text="Active").first.click()
    page.wait_for_timeout(2000)

    # Change rows per page to 100
    rows_btn = page.locator("label:has-text('Rows per page:') + div button")
    rows_btn.click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text="100").first.click()
    page.wait_for_timeout(3000)

    # Paginate through all pages of active events
    next_btn = page.locator("button[aria-label='Next page']")
    page_count = 1
    while next_btn.count() > 0 and not next_btn.evaluate("el => el.disabled"):
        print(f"📄 Navigating from page {page_count} to page {page_count + 1}...")
        next_btn.click()
        page.wait_for_timeout(2000)
        page_count += 1
        if page_count > 30:  # Safety cap to prevent infinite loops
            print("⚠️ Safety cap of 30 pages reached.")
            break

    print(f"🏁 Finished pagination. Visited {page_count} pages.")

    # Verify all captured API responses
    assert len(captured_responses) > 0, "No event list API responses were captured!"
    
    validated_responses_count = 0
    for url, data in captured_responses:
        # We check responses that are filtered by systemStatus=ACTIVE
        if "systemStatus=ACTIVE" in url:
            if isinstance(data, dict) and "data" in data:
                inner_data = data["data"]
                if isinstance(inner_data, dict) and "items" in inner_data:
                    items = inner_data["items"]
                    print(f"🔍 Validating API response for URL: {url} | Items: {len(items)}")
                    for item in items:
                        status = item.get("systemStatus")
                        assert status == "ACTIVE", (
                            f"Expected event status to be ACTIVE, but got '{status}' "
                            f"for event ID {item.get('id')} / '{item.get('name')}'"
                        )
                    validated_responses_count += 1

    assert validated_responses_count > 0, "No filtered active event list API responses were validated!"
    print(f"✅ TC04: Successfully verified only active events across all {validated_responses_count} paginated API responses.")


def test_tc05_inactive_events_api_verification(
    event_repo,
    page,
):
    """
    TC05: Verify that filtering events by 'Inactive' status and changing rows per page to 100
    returns only events with systemStatus 'INACTIVE' in the API responses across all pages.
    """
    # List to store captured API responses as tuples of (url, json_data)
    captured_responses = []

    def handle_response(response):
        if "events/all-events" in response.url:
            try:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    captured_responses.append((response.url, response.json()))
            except Exception:
                pass

    # Register response listener
    page.on("response", handle_response)

    # Select 'Inactive' status from dropdown
    page.get_by_test_id("event-status-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text="Inactive").first.click()
    page.wait_for_timeout(2000)

    # Change rows per page to 100
    rows_btn = page.locator("label:has-text('Rows per page:') + div button")
    rows_btn.click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text="100").first.click()
    page.wait_for_timeout(3000)

    # Paginate through all pages of inactive events
    next_btn = page.locator("button[aria-label='Next page']")
    page_count = 1
    while next_btn.count() > 0 and not next_btn.evaluate("el => el.disabled"):
        print(f"📄 Navigating from page {page_count} to page {page_count + 1}...")
        next_btn.click()
        page.wait_for_timeout(2000)
        page_count += 1
        if page_count > 30:  # Safety cap to prevent infinite loops
            print("⚠️ Safety cap of 30 pages reached.")
            break

    print(f"🏁 Finished pagination. Visited {page_count} pages.")

    # Verify all captured API responses
    assert len(captured_responses) > 0, "No event list API responses were captured!"
    
    validated_responses_count = 0
    for url, data in captured_responses:
        # We check responses that are filtered by systemStatus=INACTIVE
        if "systemStatus=INACTIVE" in url:
            if isinstance(data, dict) and "data" in data:
                inner_data = data["data"]
                if isinstance(inner_data, dict) and "items" in inner_data:
                    items = inner_data["items"]
                    print(f"🔍 Validating API response for URL: {url} | Items: {len(items)}")
                    for item in items:
                        status = item.get("systemStatus")
                        assert status == "INACTIVE", (
                            f"Expected event status to be INACTIVE, but got '{status}' "
                            f"for event ID {item.get('id')} / '{item.get('name')}'"
                        )
                    validated_responses_count += 1

    assert validated_responses_count > 0, "No filtered inactive event list API responses were validated!"
    print(f"✅ TC05: Successfully verified only inactive events across all {validated_responses_count} paginated API responses.")


def test_tc06_edit_active_to_inactive(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC06: Find the first active 'Manual Entry' event, edit it, toggle its status to 'Inactive',
    and verify that it shows up when filtering the repository by 'Inactive' status.
    """
    global created_event_title, created_event_status

    # 1. Locate the first row with SOURCE 'Manual Entry' and STATUS 'Active'
    row = page.locator("tbody tr").filter(
        has=page.locator("td").nth(3).get_by_text("Manual Entry")
    ).filter(
        has=page.locator("td").nth(4).get_by_text("Active")
    ).first

    # Ensure a matching row was found
    expect(row).to_be_visible()

    # Get the title of the target event
    event_title = row.locator("td").nth(1).inner_text().strip()
    print(f"Target Event for edit: '{event_title}'")

    # 2. Click the actions button (dropdown menu) for that row
    # (Note: column 7 contains the actions dropdown button)
    row.locator("button[data-testid*='actions-dropdown']").click()
    page.wait_for_timeout(500)

    # 3. Click "Edit Event"
    page.locator("//span[normalize-space()='Edit Event']").click()
    page.wait_for_timeout(2000)

    # 4. Check if status is Active, then make it Inactive
    status_btn = page.locator("[data-testid='event-edit-system-status-toggle-btn']")
    status_text = status_btn.locator("span").inner_text().strip()
    print(f"Current Status text: '{status_text}'")

    if status_text == "Active":
        print("Clicking status button to make Inactive...")
        status_btn.click()
        page.wait_for_timeout(500)
        expect(status_btn.locator("span")).to_have_text("Inactive")

    # 5. Click the submit button (Update Event)
    page.locator("//button[@type='submit']").click()

    # Wait for the edit drawer to close (submit button becomes hidden)
    page.locator("[data-testid='event-edit-submit-btn']").wait_for(state="hidden", timeout=10000)
    print("Drawer successfully closed.")

    # Update global status if the edited event was our TC02 event
    if event_title == created_event_title:
        created_event_status = "Inactive"
        print(f"🔄 Updated global created_event_status to '{created_event_status}'")

    # 6. Navigate back to Event Repository list view
    page.get_by_role("link", name="Event Repository").click()
    page.wait_for_timeout(2000)

    # 7. Select "Inactive" status in the filter dropdown
    page.get_by_test_id("event-status-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text="Inactive").first.click()
    page.wait_for_timeout(2000)

    # 8. Search for the edited event
    event_creation_page.search_event(event_title)

    # 9. Verify the event shows in the table
    event_creation_page.verify_event_in_list(event_title)
    print(f"✅ TC06: Successfully verified event '{event_title}' was updated to Inactive and shows in the Inactive list.")


def test_tc07_verify_event_details_in_list(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC07: Search for the event created in TC02 and verify that all its details
    (Title, Location, Source, Status, Created date) are displayed correctly in the repository list table.
    """
    global created_event_title, created_event_venue, created_event_source, created_event_status

    # Ensure TC02 ran and stored the event title
    assert created_event_title is not None, "No event title was stored by TC02!"

    # Navigate fresh to Event Repository
    page.get_by_role("link", name="Event Repository").click()
    page.wait_for_timeout(2000)

    # Clear filters if visible
    clear_filters_btn = page.locator("button:has-text('Clear All Filters')")
    if clear_filters_btn.is_visible():
        clear_filters_btn.click()
        page.wait_for_timeout(1000)

    # Explicitly filter by the current status of the event (since default view might show Active only)
    page.get_by_test_id("event-status-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text=created_event_status).first.click()
    page.wait_for_timeout(2000)

    # 1. Search for the event title
    print(f"🔍 Searching for event: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # 2. Locate the row for the created event
    row = page.locator("tbody tr").filter(has_text=created_event_title).first
    expect(row).to_be_visible()

    # 3. Verify each column's text in the table row
    # Column 1: Title (Cell index 1)
    expect(row.locator("td").nth(1)).to_have_text(created_event_title)

    # Column 2: Location/Venue (Cell index 2) - should start with or contain the query
    expect(row.locator("td").nth(2)).to_contain_text(created_event_venue)

    # Column 3: Source (Cell index 3)
    expect(row.locator("td").nth(3)).to_have_text(created_event_source)

    # Column 4: Status (Cell index 4)
    expect(row.locator("td").nth(4)).to_have_text(created_event_status)

    # Column 5: Created Date (Cell index 5)
    from datetime import datetime
    today = datetime.now()
    today_str = f"{today.month}/{today.day}/{today.year}"
    expect(row.locator("td").nth(5)).to_contain_text(today_str)

    print(f"✅ TC07: Successfully verified details for event '{created_event_title}' in the list: "
          f"Location='{created_event_venue}', Source='{created_event_source}', Status='{created_event_status}', "
          f"Created date contains '{today_str}'.")


@pytest.mark.xfail(reason="Known developer issue: Category filtering is broken on the repository list page.")
def test_tc08_search_by_category(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC08: Verify that filtering events by the category selected in TC02 and searching for
    the event title displays the created event in the list.
    """
    global created_event_title, created_event_category, created_event_status

    # Ensure TC02 ran and stored the category
    assert created_event_title is not None, "No event title was stored by TC02!"
    assert created_event_category is not None, "No category was stored by TC02!"

    # Navigate fresh to Event Repository
    page.get_by_role("link", name="Event Repository").click()
    page.wait_for_timeout(2000)

    # Clear filters if visible
    clear_filters_btn = page.locator("button:has-text('Clear All Filters')")
    if clear_filters_btn.is_visible():
        clear_filters_btn.click()
        page.wait_for_timeout(1000)

    # Set status filter to match the event's current status
    page.get_by_test_id("event-status-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text=created_event_status).first.click()
    page.wait_for_timeout(2000)

    # 1. Filter by category
    print(f"🔍 Filtering repository by category: '{created_event_category}'")
    page.get_by_test_id("event-category-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text=created_event_category).first.click()
    page.wait_for_timeout(2000)

    # 2. Search for the event title
    print(f"🔍 Searching for event title: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # 3. Verify the created event is displayed in the list
    event_creation_page.verify_event_in_list(created_event_title)
    print(f"✅ TC08: Successfully verified that event '{created_event_title}' displays when filtered by category '{created_event_category}'.")


def test_tc09_source_filter_verification(
    event_repo,
    page,
):
    """
    TC09: Verify that filtering events by source ('Manual Entry' and 'Ticket Master')
    returns only events with the correct source in both the UI table list and API responses.
    """
    # Navigate fresh to Event Repository
    page.get_by_role("link", name="Event Repository").click()
    page.wait_for_timeout(2000)

    # Clear filters if visible
    clear_filters_btn = page.locator("button:has-text('Clear All Filters')")
    if clear_filters_btn.is_visible():
        clear_filters_btn.click()
        page.wait_for_timeout(1000)

    # 1. Test "Manual Entry" source
    captured_responses = []

    def handle_response(response):
        if "events/all-events" in response.url:
            try:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    captured_responses.append((response.url, response.json()))
            except Exception:
                pass

    page.on("response", handle_response)

    # Click Source filter dropdown and select "Manual Entry"
    print("🔍 Filtering repository by source: 'Manual Entry'")
    page.get_by_test_id("event-source-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text="Manual Entry").first.click()
    page.wait_for_timeout(2500)

    # Verify DOM table rows have "Manual Entry" in the Source column (cell index 3)
    rows = page.locator("tbody tr").all()
    # Check up to first 10 rows for DOM validation
    for i, row in enumerate(rows[:10]):
        # Skip 'No events found' row if table is empty
        if "No events found" in row.inner_text():
            continue
        source_text = row.locator("td").nth(3).inner_text().strip()
        assert source_text == "Manual Entry", f"Expected 'Manual Entry' in row {i}, but got '{source_text}'"

    # Verify API responses contain only 'Manual Entry' (systemName == 'Manual Entry')
    assert len(captured_responses) > 0, "No event list API responses were captured for Manual Entry!"
    validated_manual_count = 0
    for url, data in captured_responses:
        # Check if URL has systemId parameter
        if "systemId=" in url:
            if isinstance(data, dict) and "data" in data:
                inner_data = data["data"]
                if isinstance(inner_data, dict) and "items" in inner_data:
                    items = inner_data["items"]
                    for item in items:
                        sys_name = item.get("systemName")
                        assert sys_name == "Manual Entry", (
                            f"Expected item source systemName to be 'Manual Entry', but got '{sys_name}'"
                        )
                    validated_manual_count += 1
    
    assert validated_manual_count > 0, "No filtered Manual Entry API responses were validated!"
    print(f"✅ Verified {validated_manual_count} Manual Entry API responses successfully.")

    # 2. Test "Ticket Master" source
    # Clear capturing list for clean Ticket Master verification
    captured_responses.clear()

    # Click Source filter dropdown and select "Ticket Master"
    print("🔍 Filtering repository by source: 'Ticket Master'")
    page.get_by_test_id("event-source-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text="Ticket Master").first.click()
    page.wait_for_timeout(2500)

    # Verify DOM table rows have "Ticket Master" in the Source column (cell index 3)
    rows = page.locator("tbody tr").all()
    for i, row in enumerate(rows[:10]):
        if "No events found" in row.inner_text():
            continue
        source_text = row.locator("td").nth(3).inner_text().strip()
        assert source_text == "Ticket Master", f"Expected 'Ticket Master' in row {i}, but got '{source_text}'"

    # Verify API responses contain only 'Ticket Master'
    assert len(captured_responses) > 0, "No event list API responses were captured for Ticket Master!"
    validated_ticket_count = 0
    for url, data in captured_responses:
        if "systemId=" in url:
            if isinstance(data, dict) and "data" in data:
                inner_data = data["data"]
                if isinstance(inner_data, dict) and "items" in inner_data:
                    items = inner_data["items"]
                    for item in items:
                        sys_name = item.get("systemName")
                        assert sys_name == "Ticket Master", (
                            f"Expected item source systemName to be 'Ticket Master', but got '{sys_name}'"
                        )
                    validated_ticket_count += 1

    assert validated_ticket_count > 0, "No filtered Ticket Master API responses were validated!"
    print(f"✅ Verified {validated_ticket_count} Ticket Master API responses successfully.")
    print("✅ TC09: Successfully verified source-based filtering for both Manual Entry and Ticket Master in DOM and API.")


def test_tc10_date_range_filter_verification(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC10: Verify that filtering events by a date range (15th to 18th of current month)
    correctly filters the list to show only events within that range in both the DOM table
    and intercepted API responses.
    """
    global created_event_title, created_event_status

    # Ensure TC02 ran and stored the event title
    assert created_event_title is not None, "No event title was stored by TC02!"

    # Navigate fresh to Event Repository
    page.get_by_role("link", name="Event Repository").click()
    page.wait_for_timeout(2000)

    # Clear filters if visible
    clear_filters_btn = page.locator("button:has-text('Clear All Filters')")
    if clear_filters_btn.is_visible():
        clear_filters_btn.click()
        page.wait_for_timeout(1000)

    # Select the status filter to match our event's current status (so we can find it in the DOM)
    page.get_by_test_id("event-status-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text=created_event_status).first.click()
    page.wait_for_timeout(2000)

    captured_responses = []

    def handle_response(response):
        if "events/all-events" in response.url:
            try:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    captured_responses.append((response.url, response.json()))
            except Exception:
                pass

    page.on("response", handle_response)

    # Click Date Range filter dropdown
    print("🔍 Selecting Date Range filter: 15th to 18th of current month")
    page.get_by_test_id("event-date-range-datepicker").click()
    page.wait_for_timeout(1000)

    # Select "15" and "18" in the calendar popover
    calendar_popup = page.locator("div[role='dialog'], div[role='tooltip'], div.absolute").first
    calendar_popup.locator("button").filter(has_text="15").first.click()
    page.wait_for_timeout(500)
    calendar_popup.locator("button").filter(has_text="18").first.click()
    page.wait_for_timeout(2500)

    # Close calendar popup if it doesn't close automatically
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)

    # 1. Search for the event title to verify it is shown within the filtered date range list
    print(f"🔍 Searching for event title in date range filtered list: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # Verify that the created event row exists in the table (meaning it was in the date range)
    event_creation_page.verify_event_in_list(created_event_title)

    # 2. Verify API responses contain only events within the specified date range
    assert len(captured_responses) > 0, "No event list API responses were captured for Date Range filter!"
    validated_api_count = 0
    for url, data in captured_responses:
        if "dateTimeFrom=" in url and "dateTimeTo=" in url:
            # Parse the query parameters from URL to get range
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            dt_from = params.get("dateTimeFrom")[0]
            dt_to = params.get("dateTimeTo")[0]
            print(f"📡 Validating API Response for Date Range {dt_from} to {dt_to}...")

            # Parse strings to datetime objects
            from datetime import datetime
            from_dt = datetime.fromisoformat(dt_from.replace("Z", "+00:00"))
            to_dt = datetime.fromisoformat(dt_to.replace("Z", "+00:00"))

            if isinstance(data, dict) and "data" in data:
                inner_data = data["data"]
                if isinstance(inner_data, dict) and "items" in inner_data:
                    items = inner_data["items"]
                    for item in items:
                        item_date_str = item.get("dateTime")
                        if item_date_str:
                            item_dt = datetime.fromisoformat(item_date_str.replace("Z", "+00:00"))
                            assert from_dt <= item_dt <= to_dt, (
                                f"Expected event date {item_date_str} to be within [{dt_from}, {dt_to}]"
                            )
                    validated_api_count += 1

    assert validated_api_count > 0, "No filtered Date Range API responses were validated!"
    print(f"✅ TC10: Successfully verified date-range-based filtering in both DOM list and {validated_api_count} API responses.")


@pytest.mark.xfail(reason="Known developer issue: Category filtering is broken on the repository list page.")
def test_tc11_combination_and_clear_filters(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC11: Apply a combination of search filter and dropdown filters (Status, Category, Source, Date Range),
    verify that the created event is correctly listed, click the "Clear All Filters" button,
    and assert that all inputs and dropdowns revert to their default states.
    """
    global created_event_title, created_event_venue, created_event_source, created_event_status, created_event_category

    # Ensure TC02 ran and stored the event title
    assert created_event_title is not None, "No event title was stored by TC02!"
    assert created_event_category is not None, "No category was stored by TC02!"

    # Navigate fresh to Event Repository
    page.get_by_role("link", name="Event Repository").click()
    page.wait_for_timeout(2000)

    # Clear filters if visible to start fresh
    clear_filters_btn = page.locator("button:has-text('Clear All Filters')")
    if clear_filters_btn.is_visible():
        clear_filters_btn.click()
        page.wait_for_timeout(1000)

    # 1. Apply Multiple Filters Simultaneously:
    # A. Search input
    print(f"🔍 Typing search query: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # B. Status filter
    print(f"🔍 Selecting Status filter: '{created_event_status}'")
    status_dropdown = page.get_by_test_id("event-status-filter-dropdown")
    status_dropdown.click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text=created_event_status).first.click()
    page.wait_for_timeout(1000)

    # C. Category filter
    print(f"🔍 Selecting Category filter: '{created_event_category}'")
    category_dropdown = page.get_by_test_id("event-category-filter-dropdown")
    category_dropdown.click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text=created_event_category).first.click()
    page.wait_for_timeout(1000)

    # D. Source filter
    print(f"🔍 Selecting Source filter: '{created_event_source}'")
    source_dropdown = page.get_by_test_id("event-source-filter-dropdown")
    source_dropdown.click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text=created_event_source).first.click()
    page.wait_for_timeout(1000)

    # E. Date Range filter
    print("🔍 Selecting Date Range filter: 15th to 18th of current month")
    date_range_btn = page.get_by_test_id("event-date-range-datepicker")
    date_range_btn.click()
    page.wait_for_timeout(1000)
    calendar_popup = page.locator("div[role='dialog'], div[role='tooltip'], div.absolute").first
    calendar_popup.locator("button").filter(has_text="15").first.click()
    page.wait_for_timeout(500)
    calendar_popup.locator("button").filter(has_text="18").first.click()
    page.wait_for_timeout(2500)
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)

    # 2. Verify that the event matches the list table output
    event_creation_page.verify_event_in_list(created_event_title)
    print("✅ Successfully verified event is visible under the combination of filters.")

    # 3. Verify states before clicking clear
    expect(page.get_by_test_id("event-search-input")).to_have_value(created_event_title)
    expect(status_dropdown).to_have_text(created_event_status)
    expect(category_dropdown).to_have_text(created_event_category)
    expect(source_dropdown).to_have_text(created_event_source)
    expect(date_range_btn).to_contain_text("15")

    # 4. Click the "Clear All Filters" button
    print("🧹 Clicking 'Clear All Filters' button...")
    expect(clear_filters_btn).to_be_visible()
    clear_filters_btn.click()
    page.wait_for_timeout(2000)

    # 5. Assert that all inputs and dropdowns reverted to their default states:
    # Search input should be empty
    expect(page.get_by_test_id("event-search-input")).to_have_value("")
    # Status dropdown should show "All Status"
    expect(status_dropdown).to_have_text("All Status")
    # Source dropdown should show "All Sources"
    expect(source_dropdown).to_have_text("All Sources")
    # Date Range dropdown should show "All Dates"
    expect(date_range_btn).to_have_text("All Dates")
    # Category dropdown should show "All Categories" (default state)
    expect(category_dropdown).to_have_text("All Categories")

    # Verify Clear All Filters button remains visible and ready for next use
    expect(clear_filters_btn).to_be_visible()
    print("✅ TC11: Successfully verified filter combinations and reset using Clear All Filters button.")


def test_tc12_delete_events_verification(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC12: Verify deletion of events in three cases.
    - Case 1: Select 3 events starting with 'Fake Event', click 'Delete Selected', confirm delete.
              If 3 such events are not present, emit a soft warning and do not fail the test.
    - Case 2: Click on a particular event, navigate to Details, click 'Delete Event', confirm.
    - Case 3: Click Actions dropdown on a row, select 'Delete Event', confirm.
    All actions are performed on events starting with 'Fake Event'.
    """
    # Navigate fresh to Event Repository
    page.get_by_role("link", name="Event Repository").click()
    page.wait_for_timeout(2000)

    # Clear filters if visible
    clear_filters_btn = page.locator("button:has-text('Clear All Filters')")
    if clear_filters_btn.is_visible():
        clear_filters_btn.click()
        page.wait_for_timeout(1000)

    # Click status filter to "All Status" to ensure we see all events (Active/Inactive)
    page.get_by_test_id("event-status-filter-dropdown").click()
    page.wait_for_timeout(500)
    page.locator("[role='option']").filter(has_text="All Status").first.click()
    page.wait_for_timeout(2000)

    # ==========================================
    # CASE 1: Delete Selected (Bulk Delete)
    # ==========================================
    print("📌 [Case 1] Starting Bulk Delete Verification...")
    rows = page.locator("tbody tr").all()
    fake_event_rows = []
    for r in rows:
        # Check if the row contains text first to avoid indexing empty lists
        cols = r.locator("td").all()
        if len(cols) > 1:
            title_text = cols[1].inner_text().strip()
            if title_text.startswith("Fake Event"):
                fake_event_rows.append((r, title_text))

    print(f"Found {len(fake_event_rows)} events starting with 'Fake Event'.")

    if len(fake_event_rows) < 3:
        import warnings
        msg = f"⚠️ Soft Warning: Less than 3 'Fake Event's found (count: {len(fake_event_rows)}). Skipping Case 1 bulk delete."
        print(msg)
        warnings.warn(msg)
    else:
        # Select first 3 fake events
        deleted_titles = []
        for idx in range(3):
            r, title = fake_event_rows[idx]
            deleted_titles.append(title)
            # Click checkbox in column 0 with force=True
            r.locator("td").nth(0).locator("input[type='checkbox']").click(force=True)
            page.wait_for_timeout(200)

        print(f"Selected 3 events for deletion: {deleted_titles}")

        # Click //span[normalize-space()='Delete Selected']
        delete_selected_btn = page.locator("//span[normalize-space()='Delete Selected']").first
        expect(delete_selected_btn).to_be_visible()
        delete_selected_btn.click()
        page.wait_for_timeout(1000)

        # Locate confirmation popup and click Delete
        popup = page.locator("div[role='dialog'], div[role='alertdialog']").first
        expect(popup).to_be_visible()
        popup.locator("button:has-text('Delete')").first.click()
        print("Confirmed bulk deletion in popup.")
        
        # Wait for reload and verify they are no longer in the list
        page.wait_for_timeout(3000)
        for title in deleted_titles:
            event_creation_page.search_event(title)
            page.wait_for_timeout(1000)
            expect(page.locator("tbody")).not_to_contain_text(title)
            # Clear search
            page.get_by_test_id("event-search-input").fill("")
            page.wait_for_timeout(1000)
        
        print("✅ Case 1: Successfully verified bulk delete.")

    # ==========================================
    # CASE 2: Delete from Event Details Page
    # ==========================================
    print("📌 [Case 2] Starting Details Page Delete Verification...")
    # Refresh rows list
    rows = page.locator("tbody tr").all()
    target_event_title = None
    for r in rows:
        cols = r.locator("td").all()
        if len(cols) > 1:
            title_text = cols[1].inner_text().strip()
            if title_text.startswith("Fake Event"):
                target_event_title = title_text
                # Click the title to go to details
                cols[1].click()
                break

    if target_event_title is None:
        print("⚠️ Soft Warning: No 'Fake Event' found for Case 2. Skipping.")
    else:
        page.wait_for_timeout(3000)
        assert "/event/details/" in page.url, f"Expected detail page, but got URL: {page.url}"
        print(f"Navigated to details page for: '{target_event_title}'")

        # Scroll to bottom and click //span[normalize-space()='Delete Event']
        delete_event_btn = page.locator("//span[normalize-space()='Delete Event']").first
        expect(delete_event_btn).to_be_visible()
        delete_event_btn.scroll_into_view_if_needed()
        delete_event_btn.click()
        page.wait_for_timeout(1000)

        # Locate confirmation popup and click Delete
        popup = page.locator("div[role='dialog'], div[role='alertdialog']").first
        expect(popup).to_be_visible()
        popup.locator("button:has-text('Delete')").first.click()
        print("Confirmed deletion on details page.")

        # Wait for redirection back to Repository
        page.wait_for_timeout(3000)
        assert "/event" in page.url, f"Expected event list page, but got URL: {page.url}"

        # Verify that the event is no longer in the list
        event_creation_page.search_event(target_event_title)
        page.wait_for_timeout(1000)
        expect(page.locator("tbody")).not_to_contain_text(target_event_title)
        page.get_by_test_id("event-search-input").fill("")
        page.wait_for_timeout(1000)
        print(f"✅ Case 2: Successfully verified delete from Details page for '{target_event_title}'.")

    # ==========================================
    # CASE 3: Delete from Row Actions Dropdown
    # ==========================================
    print("📌 [Case 3] Starting Actions Dropdown Delete Verification...")
    # Refresh rows list
    rows = page.locator("tbody tr").all()
    target_event_title = None
    target_row = None
    for r in rows:
        cols = r.locator("td").all()
        if len(cols) > 1:
            title_text = cols[1].inner_text().strip()
            if title_text.startswith("Fake Event"):
                target_event_title = title_text
                target_row = r
                break

    if target_event_title is None or target_row is None:
        print("⚠️ Soft Warning: No 'Fake Event' found for Case 3. Skipping.")
    else:
        # Click actions dropdown
        actions_btn = target_row.locator("button[data-testid*='actions-dropdown']").first
        expect(actions_btn).to_be_visible()
        actions_btn.click()
        page.wait_for_timeout(1000)

        # Click //span[normalize-space()='Delete Event'] option
        delete_option = page.locator("//span[normalize-space()='Delete Event']").first
        expect(delete_option).to_be_visible()
        delete_option.click()
        page.wait_for_timeout(1000)

        # Verify Delete Event popup displays and click //span[normalize-space()='Delete']
        popup = page.locator("div[role='dialog'], div[role='alertdialog']").first
        expect(popup).to_be_visible()
        expect(popup.locator("span:has-text('Delete Event'), h2:has-text('Delete Event')").first).to_be_visible()
        
        # Click //span[normalize-space()='Delete'] or button:has-text('Delete')
        popup.locator("button:has-text('Delete'), span:has-text('Delete')").first.click()
        print("Confirmed deletion in Actions dropdown popup.")

        # Wait for reload and verify that the event is no longer in the list
        page.wait_for_timeout(3000)
        event_creation_page.search_event(target_event_title)
        page.wait_for_timeout(1000)
        expect(page.locator("tbody")).not_to_contain_text(target_event_title)
        page.get_by_test_id("event-search-input").fill("")
        page.wait_for_timeout(1000)
        print(f"✅ Case 3: Successfully verified delete from Actions dropdown for '{target_event_title}'.")



