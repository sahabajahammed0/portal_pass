import pytest
import calendar
from datetime import datetime, timedelta
from pages.user_page.event_page import UserEventPage
from config import USER_BASE_URL
from playwright.sync_api import expect

created_tc05_event_titles = {"desktop": None, "mobile": None}


@pytest.fixture(params=[
    {"width": 1920, "height": 1080, "name": "desktop"},
    {"width": 390, "height": 844, "name": "mobile"}
], ids=["desktop", "mobile"])
def user_viewport(request):
    """Fixture supplying viewports for desktop and mobile responsive testing."""
    return request.param


@pytest.fixture(autouse=True)
def configure_user_page_viewport(request, user_viewport):
    """Autouse fixture to set the viewport size of user_page to the current parameterized layout."""
    if "user_page" in request.fixturenames:
        user_p = request.getfixturevalue("user_page")
        user_p.set_viewport_size({"width": user_viewport["width"], "height": user_viewport["height"]})


def test_tc01_user_navigation_and_footer_verification(user_page):
    """TC01: Verify home page heading and footer links, navigate to events and verify headers/footers there."""
    event_page = UserEventPage(user_page)

    # 1. Navigate to the user portal homepage and verify heading
    event_page.navigate_to_home_user_portal()

    # 2. Verify all footer links are visible on the homepage
    event_page.verify_footer_links()

    # 3. Navigate to the Events explore page and verify header
    event_page.go_to_events()

    # 4. Verify that the footer links remain visible on the Events page
    event_page.verify_footer_links()


def test_tc02_search_events(user_page):
    """TC02: Fetch visible events, search for one, and verify search filtering accuracy."""
    event_page = UserEventPage(user_page)

    # 1. Navigate to Events page directly
    event_page.navigate_directly_to_events()

    # 2. Get list of initially visible event titles
    titles = event_page.get_event_titles()
    assert len(titles) > 0, "No events displayed on the page to search for."

    # Select the first event's title to search for
    target_event = titles[0]
    print(f"\n🔎 Target event title selected for search: '{target_event}'")

    # 3. Search for the target event
    event_page.search_event(target_event)

    # 4. Verify search results display the expected event and only matching events
    event_page.verify_event_in_results(target_event)
    event_page.verify_only_matching_events_displayed(target_event)


def test_tc03_sort_events(user_page):
    """TC03: Sort events alphabetically (A-Z and Z-A) and check ordering accuracy."""
    event_page = UserEventPage(user_page)

    # 1. Navigate to Events page directly
    event_page.navigate_directly_to_events()

    # 2. Sort by Name (A-Z)
    print("\n🔀 Sorting by 'Name (A-Z)'")
    event_page.select_sort_option("Name (A-Z)")

    # 3. Verify ordering is alphabetical A-Z
    event_page.verify_events_sorted_alphabetically_az()

    # 4. Sort by Name (Z-A)
    print("🔀 Sorting by 'Name (Z-A)'")
    event_page.select_sort_option("Name (Z-A)")

    # 5. Verify ordering is alphabetical Z-A
    event_page.verify_events_sorted_alphabetically_za()


def test_tc04_create_event_from_admin_and_verify_in_user_portal(
    event_repo,
    event_creation_page,
    user_portal_browser,
    user_viewport
):
    """TC04: Create an event from Admin portal, then verify it exists in the User portal with correct details."""
    import random
    import os
    from playwright.sync_api import expect

    # 1. Choose a random venue and a random image for event creation
    venues = ["New York", "Los Angeles", "Chicago", "Sydney", "Berlin", "Toronto"]
    selected_venue = random.choice(venues)
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.abspath(os.path.join(test_dir, "../../data/images"))
    safe_images = []
    if os.path.exists(image_dir):
        for f in os.listdir(image_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(image_dir, f)
                if os.path.getsize(full_path) < 2500000:
                    safe_images.append(f)
                    
    assert len(safe_images) > 0, "No mock images under 2.5 MB found in data/images!"
    random_image_name = random.choice(safe_images)
    random_image_path = os.path.join(image_dir, random_image_name)

    # 2. Generate a unique event title
    unique_id = random.randint(10000, 99999)
    event_title = f"Admin Created Test Event {unique_id}"
    event_description = f"This is an automated test event description for {event_title}."
    event_website = "https://www.example-test-event.com"
    event_email = f"contact-{unique_id}@example.com"
    event_phone = "5551234567"
    event_notes = "Created for cross-portal validation test."

    print(f"\n➕ Creating event in Admin Portal: '{event_title}'")
    # Click create event button
    event_creation_page.click_create_event()
    
    # Fill and submit event form
    selected_category = event_creation_page.create_event(
        title=event_title,
        venue=selected_venue,
        description=event_description,
        website=event_website,
        email=event_email,
        phone=event_phone,
        notes=event_notes,
        image_path=random_image_path,
        fill_venue=True
    )
    print(f"✅ Event '{event_title}' submitted successfully in Category '{selected_category}' at Venue '{selected_venue}'.")

    # Verify the drawer is fully closed before proceeding (create_event() already waits, this is a safety net)
    expect(event_creation_page.heading_create_event).not_to_be_visible(timeout=15000)

    # Open a dedicated fresh browser for the User Portal (avoids Cloudflare bot challenge in CI)
    print(f"🔎 Opening new page in User Portal to search and verify details for '{event_title}'")
    user_p = user_portal_browser(user_viewport["width"], user_viewport["height"])
    user_event_page = UserEventPage(user_p)
    user_event_page.navigate_directly_to_events()

    # Search for the newly created event (with retries for API propagation lag)
    max_retries = 5
    found = False
    for attempt in range(max_retries):
        try:
            user_event_page.search_box.clear()
            user_event_page.search_box.fill(event_title)
            user_event_page.page.wait_for_timeout(2000)
            user_event_page.verify_event_in_results(event_title)
            found = True
            break
        except AssertionError as e:
            if attempt == max_retries - 1:
                raise
            print(f"⚠️ Event not found in search results on attempt {attempt+1}/{max_retries}. Retrying...")
            user_event_page.navigate_directly_to_events()

    # Click on the event card/title to navigate to the details page
    user_event_page.click_event_by_title(event_title)

    # 4. Verify that the event details page shows all correct fields
    user_event_page.verify_event_details(
        title=event_title,
        description=event_description,
        venue=selected_venue,
        category=selected_category
    )
    print(f"🎉 Successfully verified event details in the User Portal for '{event_title}'!")


def test_tc05_create_event_with_child_category_and_verify_filters(
    event_repo,
    event_creation_page,
    user_portal_browser,
    user_viewport
):
    """TC05: Create an event with a parent category and child category, then verify category filters in the User portal."""
    import random
    import os
    from playwright.sync_api import expect

    global created_tc05_event_titles

    # 1. Choose a random venue and a random image for event creation
    venues = ["New York", "Los Angeles", "Chicago", "Sydney", "Berlin", "Toronto"]
    selected_venue = random.choice(venues)
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.abspath(os.path.join(test_dir, "../../data/images"))
    safe_images = []
    if os.path.exists(image_dir):
        for f in os.listdir(image_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(image_dir, f)
                if os.path.getsize(full_path) < 2500000:
                    safe_images.append(f)
                    
    assert len(safe_images) > 0, "No mock images under 2.5 MB found in data/images!"
    random_image_name = random.choice(safe_images)
    random_image_path = os.path.join(image_dir, random_image_name)

    # 2. Generate a unique event title
    unique_id = random.randint(10000, 99999)
    event_title = f"Admin Child Category Test Event {unique_id}"
    created_tc05_event_titles[user_viewport["name"]] = event_title
    event_description = f"This is an automated test event description for {event_title}."
    event_website = "https://www.example-test-event.com"
    event_email = f"contact-{unique_id}@example.com"
    event_phone = "5551234567"
    event_notes = "Created for cross-portal category filtering validation test."

    parent_cat = "Sports"
    child_cat = "Football"

    print(f"\n➕ Creating event in Admin Portal with Category '{parent_cat} -> {child_cat}': '{event_title}'")
    # Click create event button
    event_creation_page.click_create_event()
    
    # Fill and submit event form (dates and times generated centrally)
    selected_category = event_creation_page.create_event(
        title=event_title,
        venue=selected_venue,
        description=event_description,
        website=event_website,
        email=event_email,
        phone=event_phone,
        notes=event_notes,
        image_path=random_image_path,
        fill_venue=True,
        parent_category=parent_cat,
        child_category=child_cat
    )
    start_day = event_creation_page.last_start_day
    end_day = event_creation_page.last_end_day
    print(f"📅 Using dynamic date range: day {start_day} → day {end_day}")
    print(f"✅ Event '{event_title}' submitted successfully under subcategory '{selected_category}'.")

    # Wait for the drawer to close
    expect(event_creation_page.heading_create_event).not_to_be_visible(timeout=15000)

    # Open a dedicated fresh browser for the User Portal (avoids Cloudflare bot challenge in CI)
    print(f"🔎 Opening new page in User Portal to apply category filters for '{event_title}'")
    user_p = user_portal_browser(user_viewport["width"], user_viewport["height"])
    user_event_page = UserEventPage(user_p)
    user_event_page.navigate_directly_to_events()

    # Click Filters to open the filter configuration drawer
    user_event_page.open_filters()

    # Expand the parent category "Sports" and select the child category "Football"
    print(f"📁 Expanding parent category '{parent_cat}' and selecting child category '{child_cat}' in filters...")
    user_event_page.select_parent_and_child_filter(parent_cat, child_cat)

    # Apply date range filter
    print(f"📅 Selecting date range filter '{start_day}' to '{end_day}'...")
    user_event_page.select_date_range(start_day, end_day)

    # Click Apply Filter
    user_event_page.apply_filters()
    print("✅ Category and Date range filters applied.")

    # Verify that the newly created event is visible in the filtered results page directly, without using the search box (handling both propagation latency and pagination)
    max_retries = 5
    found = False
    for attempt in range(max_retries):
        if user_event_page.verify_event_presence_with_pagination(event_title, max_pages=3):
            found = True
            break
        print(f"⚠️ Event not found in filtered results on attempt {attempt+1}/{max_retries}. Retrying in 3s...")
        user_event_page.page.wait_for_timeout(3000)
        
        # Navigate to a clean Events page to clear active filters and re-apply
        user_event_page.page.goto(f"{USER_BASE_URL}/events")
        user_event_page.open_filters()
        user_event_page.select_parent_and_child_filter(parent_cat, child_cat)
        user_event_page.select_date_range(start_day, end_day)
        user_event_page.apply_filters()

    assert found, f"Expected event '{event_title}' to be in the filtered results, but it was not found after {max_retries} attempts!"
    print(f"🎉 Successfully verified event '{event_title}' is visible when the '{child_cat}' category and date filters are applied!")


def test_tc06_make_inactive_and_verify_not_visible_in_user_portal(
    event_repo,
    event_creation_page,
    page,
    user_portal_browser,
    user_viewport
):
    """
    TC06: Find the event created in TC05, make it Inactive from the Admin portal,
    then verify that it is no longer displayed on the User site.
    """
    global created_tc05_event_titles
    created_tc05_event_title = created_tc05_event_titles[user_viewport["name"]]
    
    # Ensure we have the event title from TC05
    assert created_tc05_event_title is not None, "No event created in TC05 to make inactive!"
    print(f"\n🚫 Making event '{created_tc05_event_title}' Inactive in Admin Portal...")

    # Set up route interceptor for removing venueSourceId on update
    event_creation_page.setup_event_intercept_route(page)

    # 1. Search for the event in the Admin Portal repository
    event_creation_page.search_event(created_tc05_event_title)
    
    # Wait for the row to load
    event_creation_page.table_rows.first.wait_for(state="visible", timeout=10000)

    # Get the row matching the event and verify it is Active initially
    row = event_creation_page.get_row_by_source_and_status(source="Manual Entry", status="Active")
    expect(row).to_be_visible()

    # Toggle the status inline to Inactive
    event_creation_page.toggle_row_status(row)
    print(f"✅ Successfully toggled event '{created_tc05_event_title}' to Inactive in Admin Portal.")

    # Open a dedicated fresh browser for the User Portal (avoids Cloudflare bot challenge in CI)
    print(f"🔎 Opening User Portal to verify '{created_tc05_event_title}' is no longer visible...")
    user_p = user_portal_browser(user_viewport["width"], user_viewport["height"])
    user_event_page = UserEventPage(user_p)
    user_event_page.navigate_directly_to_events()

    # Search for the event title
    user_event_page.search_box.fill(created_tc05_event_title)
    user_event_page.page.wait_for_timeout(2000) # Wait for search response/render

    # Verify that the event is NOT visible/present in the results
    expect(user_event_page.page.locator("text=No events found").first).to_be_visible(timeout=5000)
    
    # Double check that the title is not on the page at all
    titles = user_event_page.get_event_titles()
    assert created_tc05_event_title not in titles, f"Inactive event '{created_tc05_event_title}' was still visible in the user portal!"

    print(f"🎉 Successfully verified that Inactive event '{created_tc05_event_title}' is no longer visible in the User Portal!")
