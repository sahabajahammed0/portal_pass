import os
import pytest
import random
import calendar
from datetime import datetime, timedelta
from faker import Faker
from playwright.sync_api import expect

fake = Faker()

# Global variables to share the created event's data from TC02 to other tests
created_event_title = None
created_event_venue = "New York"
created_event_source = "Manual Entry"
created_event_status = "Active"
created_event_category = None
created_event_start_day = None   # Set dynamically in TC02 based on today's date
created_event_end_day = None     # Set dynamically in TC02 based on today's date


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

@pytest.mark.regression
def test_tc02_create_event_with_fake_data(
    event_repo,
    event_creation_page,
):
    """
    TC02: Verify successful creation of an event using random fake data, category, and image.
    """
    global created_event_title, created_event_category, created_event_venue, created_event_start_day, created_event_end_day

    # Pick a random venue from a list of verified System Places in the database
    venues = ["New York", "Los Angeles", "Chicago", "Sydney", "Berlin", "Toronto"]
    created_event_venue = random.choice(venues)
    print(f"📍 Selected venue: {created_event_venue}")

    # Open Create Event form
    event_creation_page.click_create_event()

    # Pick a random image from data/images/ under 2.5 MB and upload it
    test_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.abspath(os.path.join(test_dir, "../../data/images"))
    safe_images = []
    for f in os.listdir(image_dir):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            full_path = os.path.join(image_dir, f)
            if os.path.getsize(full_path) < 2500000:  # Less than 2.5 MB
                safe_images.append(f)

    assert len(safe_images) > 0, "No mock images under 2.5 MB found in data/images!"
    random_image_name = random.choice(safe_images)
    random_image_path = os.path.join(image_dir, random_image_name)
    print(f"📸 Selected random image for upload: {random_image_name}")

    # Generate Fake Title and details
    fake_title = f"Fake Event {fake.word().capitalize()} {random.randint(1000, 9999)}"
    created_event_title = fake_title  # Save to global variable for TC03

    # Call the high-level create_event function (dates and times generated centrally)
    created_event_category = event_creation_page.create_event(
        title=fake_title,
        venue=created_event_venue,
        description=fake.paragraph(nb_sentences=3),
        website=fake.url(),
        email=fake.ascii_free_email(),
        phone="5551234567",
        notes=f"Automated test event created via Pytest on {fake.date()}.",
        image_path=random_image_path,
        fill_venue=True
    )
    created_event_start_day = event_creation_page.last_start_day
    created_event_end_day = event_creation_page.last_end_day
    print(f"📅 Using dynamic date range: day {created_event_start_day} → day {created_event_end_day}")
    print(f"🏷️ Selected category: {created_event_category}")
    print("📤 Submitted the event creation form.")


    # Verify the event is created and displayed in the event list/table
    # Wait for the drawer to close (the Create Event heading should not be visible anymore)
    expect(event_creation_page.heading_create_event).not_to_be_visible(timeout=15000)

    # Search for the created event
    event_creation_page.search_event(fake_title)

    # Verify that the created event row exists in the table
    event_creation_page.verify_event_in_list(fake_title)
    print(f"✅ TC02: Successfully verified creation of event '{fake_title}'.")

@pytest.mark.regression
def test_tc03_search_created_event(
    event_repo,
    event_creation_page,
):
    """
    TC03: Search and verify the event created in TC02.
    """
    global created_event_title
    
    # Ensure TC02 ran and set the global variable
    if created_event_title is None:
        pytest.skip("Skipping because TC02 did not run in this process/session.")

    # Search for the event title stored from TC02
    print(f"🔍 Searching for event created in TC02: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # Verify that the event is listed in the search results table
    event_creation_page.verify_event_in_list(created_event_title)
    print(f"✅ TC03: Successfully verified that event '{created_event_title}' shows up in search list.")


def test_tc04_active_events_api_verification(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC04: Verify that filtering events by 'Active' status and changing rows per page to 100
    returns only events with systemStatus 'ACTIVE' in the API responses across all pages.
    """
    event_creation_page.verify_api_responses_by_status(
        page=page,
        status_filter="Active",
        expected_system_status="ACTIVE"
    )


def test_tc05_inactive_events_api_verification(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC05: Verify that filtering events by 'Inactive' status and changing rows per page to 100
    returns only events with systemStatus 'INACTIVE' in the API responses across all pages.
    """
    event_creation_page.verify_api_responses_by_status(
        page=page,
        status_filter="Inactive",
        expected_system_status="INACTIVE"
    )



@pytest.mark.regression
def test_tc06_edit_active_to_inactive(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC06: Test status toggling via two methods.
    - Case 1: Toggle status from Active to Inactive directly from the repository list table row.
    - Case 2: Edit the Inactive event and set it to Active on the Edit page, then verify it is Active again.
    """
    global created_event_title, created_event_status

    log_listener = event_creation_page.setup_api_log_listener(page)
    event_creation_page.setup_event_intercept_route(page)

    # 1. Search for the created event if available to ensure we edit the correct one and avoid page 1 empty state
    if created_event_title:
        print(f"🔍 Searching for event: '{created_event_title}'")
        event_creation_page.search_event(created_event_title)
    else:
        print("⚠️ No created_event_title found. Filtering repository by Active and Manual Entry to find a target event.")
        event_creation_page.filter_by_status("Active")
        event_creation_page.filter_by_source("Manual Entry")

    # Wait for the first row to load and be visible in the table
    event_creation_page.table_rows.first.wait_for(state="visible", timeout=10000)

    # Locate the target row with SOURCE 'Manual Entry' and STATUS 'Active'
    row = event_creation_page.get_row_by_source_and_status(source="Manual Entry", status="Active")
    expect(row).to_be_visible()

    # Get the title of the target event
    event_title = row.locator("td").nth(1).inner_text().strip()
    print(f"Target Event for edit: '{event_title}'")

    # ==========================================
    # Case 1: Toggle status directly from the listing page (make Inactive)
    # ==========================================
    print("🔄 [Case 1] Toggling status from Active to Inactive via the list switch...")
    event_creation_page.toggle_row_status(row)
    print("✅ Successfully toggled status to Inactive on the list.")

    # Refresh/filter to see it in the Inactive list
    event_creation_page.filter_by_status("Inactive")
    event_creation_page.search_event(event_title)
    
    # Locate the row in the Inactive list
    row_inactive = event_creation_page.get_row_by_source_and_status(source="Manual Entry", status="Inactive")
    expect(row_inactive).to_be_visible()
    
    # ==========================================
    # Case 2: Navigate to Edit and toggle back to Active
    # ==========================================
    print("🔄 [Case 2] Editing the Inactive event to make it Active again...")
    event_creation_page.click_row_actions(row_inactive)
    event_creation_page.select_edit_event_from_dropdown()

    # Set status to Active on the edit page
    event_creation_page.set_edit_status("Active")
    event_creation_page.submit_update_event()
    print("Update submitted successfully.")

    # Update global status if the edited event was our TC02 event
    if event_title == created_event_title:
        created_event_status = "Active"
        print(f"🔄 Updated global created_event_status to '{created_event_status}'")

    # Navigate back to Event Repository list view
    event_creation_page.navigate_to_event_repository()

    # Select "Active" status in the filter dropdown
    event_creation_page.filter_by_status("Active")
    event_creation_page.search_event(event_title)

    # Verify the event is back in the Active list
    row_active_again = event_creation_page.get_row_by_source_and_status(source="Manual Entry", status="Active")
    expect(row_active_again).to_be_visible()
    print(f"✅ TC06: Successfully verified status toggles in both listing table and edit page for event '{event_title}'.")

    # Clean up listener
    page.remove_listener("response", log_listener)



def test_tc07_verify_event_details_in_list(
    event_repo,
    page,
    event_creation_page,
    user_portal_browser,
):
    """
    TC07: Search for the event created in TC02 and verify that all its details
    (Title, Location, Source, Status, Created date) are displayed correctly in the repository list table.
    """
    global created_event_title, created_event_venue, created_event_source, created_event_status

    # Ensure TC02 ran and stored the event title
    if created_event_title is None:
        pytest.skip("Skipping because TC02 did not run in this process/session.")

    # Navigate fresh to Event Repository
    event_creation_page.navigate_to_event_repository()

    # Clear filters if visible
    event_creation_page.clear_filters()

    # Explicitly filter by the current status of the event (since default view might show Active only)
    event_creation_page.filter_by_status(created_event_status)

    # 1. Search for the event title
    print(f"🔍 Searching for event: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # 2. Locate the row for the created event
    row = event_creation_page.get_row_by_title(created_event_title)
    expect(row).to_be_visible()

    # 3. Verify each column's text in the table row
    event_creation_page.verify_row_details(
        row=row,
        title=created_event_title,
        venue=created_event_venue,
        source=created_event_source,
        status=created_event_status
    )
    event_creation_page.verify_row_date_is_recent(row)

    print(f"✅ TC07: Successfully verified details for event '{created_event_title}' in the Admin list: "
          f"Location='{created_event_venue}', Source='{created_event_source}', Status='{created_event_status}'.")

    # 4. Verify in the User Portal in BOTH desktop and mobile responsive layouts
    from pages.user_page.event_page import UserEventPage

    for layout, width, height in [("desktop", 1920, 1080), ("mobile", 390, 844)]:
        print(f"🔎 [TC07] Opening User Portal in {layout} layout to verify details for '{created_event_title}'")
        # Use a fresh isolated browser — not admin context — to avoid Cloudflare bot challenge
        user_p = user_portal_browser(width, height)
        user_event_page = UserEventPage(user_p)
        user_event_page.navigate_directly_to_events()

        # Search for the newly created event (with retries for API propagation lag)
        max_retries = 5
        for attempt in range(max_retries):
            try:
                user_event_page.search_box.clear()
                user_event_page.search_box.fill(created_event_title)
                user_event_page.page.wait_for_timeout(2000)
                user_event_page.verify_event_in_results(created_event_title)
                break
            except AssertionError:
                if attempt == max_retries - 1:
                    raise
                print(f"⚠️ Event not found in search results on attempt {attempt+1}/{max_retries}. Retrying...")
                user_event_page.navigate_directly_to_events()

        # Click on the event card/title to navigate to the details page
        user_event_page.click_event_by_title(created_event_title)

        # Verify that the event details page shows correct Title, Venue, and Category
        expect(user_event_page.page.locator("h1, h2").first).to_contain_text(created_event_title, timeout=10000)
        body_text = user_event_page.page.locator("body").inner_text()
        assert created_event_venue in body_text, f"Venue '{created_event_venue}' not found on details page."
        assert created_event_category in body_text, f"Category '{created_event_category}' not found on details page."
        # user_portal_browser fixture handles cleanup automatically

    print(f"✅ TC07: Successfully verified details for event '{created_event_title}' in both the Admin list and User Portal (both layouts)!")



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
    if created_event_title is None or created_event_category is None:
        pytest.skip("Skipping because TC02 did not run in this process/session.")

    # Navigate fresh to Event Repository
    event_creation_page.navigate_to_event_repository()

    # Clear filters if visible
    event_creation_page.clear_filters()

    # Set status filter to match the event's current status
    event_creation_page.filter_by_status(created_event_status)

    # 1. Filter by category
    print(f"🔍 Filtering repository by category: '{created_event_category}'")
    event_creation_page.filter_by_category(created_event_category)

    # 2. Search for the event title
    print(f"🔍 Searching for event title: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # 3. Verify the created event is displayed in the list
    event_creation_page.verify_event_in_list(created_event_title)
    print(f"✅ TC08: Successfully verified that event '{created_event_title}' displays when filtered by category '{created_event_category}'.")


def test_tc09_source_filter_verification(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC09: Verify that filtering events by source ('Manual Entry' and 'Ticket Master')
    returns only events with the correct source in both the UI table list and API responses.
    """
    # Navigate fresh to Event Repository
    event_creation_page.navigate_to_event_repository()

    # Clear filters if visible
    event_creation_page.clear_filters()

    # 1. Test "Manual Entry" source
    event_creation_page.verify_api_and_dom_by_source(
        page=page,
        source_filter="Manual Entry",
        expected_system_name="Manual Entry"
    )

    # 2. Test "Ticket Master" source
    event_creation_page.verify_api_and_dom_by_source(
        page=page,
        source_filter="Ticket Master",
        expected_system_name="Ticket Master"
    )
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
    global created_event_title, created_event_status, created_event_start_day, created_event_end_day

    # Ensure TC02 ran and stored the event title and date range
    if created_event_title is None:
        pytest.skip("Skipping because TC02 did not run in this process/session.")

    # Navigate fresh to Event Repository
    event_creation_page.navigate_to_event_repository()

    # Clear filters if visible
    event_creation_page.clear_filters()

    # Select the status filter to match our event's current status (so we can find it in the DOM)
    event_creation_page.filter_by_status(created_event_status)

    # Verify using the same dynamic date range used in TC02
    event_creation_page.verify_api_and_dom_by_date_range(
        page=page,
        start_day=created_event_start_day,
        end_day=created_event_end_day,
        search_title=created_event_title
    )



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
    global created_event_title, created_event_venue, created_event_source, created_event_status, created_event_category, created_event_start_day, created_event_end_day

    # Ensure TC02 ran and stored the event title
    if created_event_title is None or created_event_category is None:
        pytest.skip("Skipping because TC02 did not run in this process/session.")

    # Navigate fresh to Event Repository
    event_creation_page.navigate_to_event_repository()

    # Clear filters if visible to start fresh
    event_creation_page.clear_filters()

    # 1. Apply Multiple Filters Simultaneously:
    # A. Search input
    print(f"🔍 Typing search query: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    # B. Status filter
    print(f"🔍 Selecting Status filter: '{created_event_status}'")
    event_creation_page.filter_by_status(created_event_status)

    # C. Category filter
    print(f"🔍 Selecting Category filter: '{created_event_category}'")
    event_creation_page.filter_by_category(created_event_category)

    # D. Source filter
    print(f"🔍 Selecting Source filter: '{created_event_source}'")
    event_creation_page.filter_by_source(created_event_source)

    # E. Date Range filter — reuse the same dynamic range computed in TC02
    print(f"🔍 Selecting Date Range filter: day {created_event_start_day} to day {created_event_end_day}")
    event_creation_page.filter_by_date_range(created_event_start_day, created_event_end_day)

    # 2. Verify that the event matches the list table output
    event_creation_page.verify_event_in_list(created_event_title)
    print("✅ Successfully verified event is visible under the combination of filters.")

    # 3. Verify states before clicking clear
    expect(event_creation_page.search_input).to_have_value(created_event_title)
    expect(event_creation_page.status_filter_dropdown).to_have_text(created_event_status)
    expect(event_creation_page.category_filter_dropdown).to_have_text(created_event_category)
    expect(event_creation_page.source_filter_dropdown).to_have_text(created_event_source)
    expect(event_creation_page.date_range_filter_picker).to_contain_text(created_event_start_day)

    # 4. Click the "Clear All Filters" button
    print("🧹 Clicking 'Clear All Filters' button...")
    expect(event_creation_page.clear_all_filters_btn).to_be_visible()
    event_creation_page.clear_filters()

    # 5. Assert that all inputs and dropdowns reverted to their default states:
    # Search input should be empty
    expect(event_creation_page.search_input).to_have_value("")
    # Status dropdown should show "All Status"
    expect(event_creation_page.status_filter_dropdown).to_have_text("All Status")
    # Source dropdown should show "All Sources"
    expect(event_creation_page.source_filter_dropdown).to_have_text("All Sources")
    # Date Range dropdown should show "All Dates"
    expect(event_creation_page.date_range_filter_picker).to_have_text("All Dates")
    # Category dropdown should show "All Categories" (default state)
    expect(event_creation_page.category_filter_dropdown).to_have_text("All Categories")

    # Verify Clear All Filters button remains visible and ready for next use
    expect(event_creation_page.clear_all_filters_btn).to_be_visible()
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
    event_creation_page.navigate_to_event_repository()

    # Clear filters if visible
    event_creation_page.clear_filters()

    # Click status filter to "All Status" to ensure we see all events (Active/Inactive)
    event_creation_page.filter_by_status("All Status")

    # ==========================================
    # CASE 1: Delete Selected (Bulk Delete)
    # ==========================================
    print("📌 [Case 1] Starting Bulk Delete Verification...")
    success = event_creation_page.delete_selected_bulk(page, title_prefix="Admin Child Category Test Event")
    if success:
        print("✅ Case 1: Successfully verified bulk delete.")
    else:
        import warnings
        msg = "⚠️ Soft Warning: Less than 3 'Admin Child Category Test Event's found. Skipping Case 1 bulk delete."
        print(msg)
        warnings.warn(msg)

    # ==========================================
    # CASE 2: Delete from Event Details Page
    # ==========================================
    print("📌 [Case 2] Starting Details Page Delete Verification...")
    success = event_creation_page.delete_via_details_page(page, title_prefix="Fake Event")
    if success:
        print("✅ Case 2: Successfully verified delete from Details page.")
    else:
        print("⚠️ Soft Warning: No 'Fake Event' found for Case 2. Skipping.")

    # ==========================================
    # CASE 3: Delete from Row Actions Dropdown
    # ==========================================
    print("📌 [Case 3] Starting Actions Dropdown Delete Verification...")
    success = event_creation_page.delete_via_dropdown(page, title_prefix="Fake Event")
    if success:
        print("✅ Case 3: Successfully verified delete from Actions dropdown.")
    else:
        print("⚠️ Soft Warning: No 'Fake Event' found for Case 3. Skipping.")


@pytest.mark.xfail(reason="Known developer issue: Searching an inactive event with status filter set to 'All Status' does not display the event in the repository list.")
def test_tc13_search_inactive_event_with_all_status(
    event_repo,
    page,
    event_creation_page,
):
    """
    TC13: Verify that an inactive event is visible in the repository list table when searched
    under 'All Status' status filter.
    """
    global created_event_title, created_event_status

    # Ensure TC02 and TC06 ran, and the event was set to inactive
    if created_event_title is None or created_event_status != "Inactive":
        pytest.skip("Skipping because TC02/TC06 did not run in this process/session or event is not Inactive.")

    # Navigate fresh to Event Repository
    event_creation_page.navigate_to_event_repository()

    # Clear filters to start from a clean state
    event_creation_page.clear_filters()

    # 1. Set Status filter to 'All Status'
    print("🔍 Selecting 'All Status' in status filter dropdown...")
    event_creation_page.filter_by_status("All Status")

    # 2. Search for the inactive event's title
    print(f"🔍 Searching for inactive event: '{created_event_title}'")
    event_creation_page.search_event(created_event_title)

    try:
        # 3. Verify that the event is displayed in the list (expect to be visible, but xfailed due to system bug)
        print("🔍 Verifying that the inactive event is visible in the list...")
        inactive_row = event_creation_page.get_row_by_title(created_event_title)
        expect(inactive_row).to_be_visible()
        print("✅ Verified inactive event is visible under 'All Status' status filter.")
    finally:
        # Cleanup: Delete the event to avoid creating unnecessary junk
        print("🧹 Cleaning up: Deleting the created inactive event...")
        event_creation_page.filter_by_status("Inactive")
        event_creation_page.search_event(created_event_title)
        event_creation_page.delete_via_dropdown(page, title_prefix=created_event_title)
        print(f"✅ Successfully cleaned up event '{created_event_title}'.")




