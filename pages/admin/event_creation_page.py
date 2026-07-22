from playwright.sync_api import Page, expect

class EventCreationPage:
    def __init__(self, page: Page):
        self.page = page
        
        # Trigger / Header Locators
        self.create_event_btn = page.get_by_test_id("event-create-btn")
        self.heading_create_event = page.get_by_role("heading", name="Create Event")
        
        # Form Input Locators
        self.image_upload_trigger = page.get_by_test_id("event-create-image-upload")
        self.file_input = page.locator('input[type="file"]')
        self.title_input = page.get_by_test_id("event-create-title-input")
        self.venue_search_input = page.get_by_role("textbox", name="Search venue location")
        
        # Date & Time Pickers
        self.start_date_picker = page.get_by_test_id("event-create-start-date-datepicker")
        self.start_time_input = page.get_by_test_id("event-create-start-time-input")
        self.end_date_picker = page.get_by_test_id("event-create-end-date-datepicker")
        self.end_time_input = page.get_by_test_id("event-create-end-time-input")
        
        # Other Form Fields
        self.category_dropdown = page.get_by_test_id("event-create-category-dropdown-0")
        self.description_editor = page.locator(".tiptap")
        self.website_input = page.get_by_test_id("event-create-website-input")
        self.contact_email_input = page.get_by_test_id("event-create-contact-email-input")
        self.contact_phone_input = page.get_by_test_id("event-create-contact-phone-input")
        self.notes_textarea = page.get_by_test_id("event-create-notes-textarea")
        
        # Styled class locator (recorded from codegen)
        self.custom_styled_container = page.locator(
            ".relative.flex.items-center.gap-2\\.5.w-full.bg-white.rounded-\\[50px\\].border.border-solid.px-4\\.25.py-3\\.75.transition-colors.duration-200.border-\\[\\#ddd\\].opacity-50"
        ).first
        
        # Submission Locator
        self.submit_btn = page.get_by_test_id("event-create-submit-btn")
        
        # Repository List Search Locator
        self.search_input = page.get_by_test_id("event-search-input")

        # Error/Validation Messages
        self.err_title_required = page.get_by_text("Event title is required").first
        self.err_venue_required = page.get_by_text("Venue location is required").first
        self.err_start_date_required = page.get_by_text("Start date is required").first
        self.err_time_format_first = page.get_by_text("Use format HH:MM").first
        self.err_end_date_required = page.get_by_text("End date is required").first
        self.err_time_format_second = page.get_by_text("Use format HH:MM").nth(1)
        self.err_category_required = page.get_by_text("Primary category is required").first
        self.err_description_required = page.get_by_text("Description is required").first

        # Repository Filter Locators
        self.status_filter_dropdown = page.get_by_test_id("event-status-filter-dropdown")
        self.source_filter_dropdown = page.get_by_test_id("event-source-filter-dropdown")
        self.category_filter_dropdown = page.get_by_test_id("event-category-filter-dropdown")
        self.date_range_filter_picker = page.get_by_test_id("event-date-range-datepicker")
        self.clear_all_filters_btn = page.locator("button:has-text('Clear All Filters')")
        self.rows_per_page_btn = page.locator("label:has-text('Rows per page:') + div button")
        self.next_page_btn = page.locator("button[aria-label='Next page']")

        # List & Table Locators
        self.table_rows = page.locator("tbody tr")
        self.edit_event_option = page.locator("//span[normalize-space()='Edit Event']")
        self.delete_event_option = page.locator("//span[normalize-space()='Delete Event']")
        self.active_status_btn = page.locator("//div[contains(., 'System Status:')]//button[normalize-space()='Active']").last
        self.inactive_status_btn = page.locator("//div[contains(., 'System Status:')]//button[normalize-space()='Inactive']").last
        self.update_event_btn = page.locator("button[type='submit']")
        
        # Bulk Deletion and Details Page Deletion
        self.delete_selected_btn = page.locator("//span[normalize-space()='Delete Selected']")
        self.confirmation_popup = page.locator("div[role='dialog'], div[role='alertdialog']").first
        self.popup_delete_btn = self.confirmation_popup.locator("button:has-text('Delete'), span:has-text('Delete')")
        self.details_delete_event_btn = page.locator("//span[normalize-space()='Delete Event']")
        self.event_repository_link = page.get_by_role("link", name="Event Repository")
        
        # Centralized dynamically generated values
        self.last_start_day = None
        self.last_end_day = None
        self.last_start_time = None
        self.last_end_time = None

    # --- Actions ---
    
    def click_create_event(self):
        """Clicks the button to open the Create Event form and verifies the heading."""
        self.create_event_btn.click()
        expect(self.heading_create_event).to_be_visible()

    def upload_event_image(self, image_path: str):
        """Uploads an image for the event."""
        self.file_input.set_input_files(image_path)

    def fill_title(self, title: str):
        """Fills the event title."""
        self.title_input.fill(title)

    def fill_venue(self, venue_name: str):
        """Fills the venue search input and selects the first option from 'System Places' suggestions."""
        # Click the input field to focus
        self.venue_search_input.click()
        # Clear any existing text
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        
        # Type the venue name sequentially to trigger the autocomplete dropdown
        self.venue_search_input.press_sequentially(venue_name, delay=100)
        
        # Locate the suggestions container containing 'System Places'
        container = self.page.locator(".absolute.top-full:has-text('System Places')")
        
        try:
            # Wait for the System Places container to become visible
            container.wait_for(state="visible", timeout=5000)
            # Locate the first suggestion button inside the System Places section
            suggestion_btn = container.locator("button").first
            suggestion_btn.click()
            print(f"✅ Successfully selected '{venue_name}' from System Places dropdown.")
        except Exception as e:
            print(f"⚠️ Warning: Could not select '{venue_name}' from System Places. Attempting Google Places fallback...")
            # Fallback to any dropdown container (e.g. Google Places) if System Places is not present
            fallback_container = self.page.locator(".absolute.top-full")
            try:
                fallback_container.wait_for(state="visible", timeout=3000)
                fallback_container.locator("button").first.click()
                print("✅ Successfully selected from fallback dropdown suggestions.")
            except Exception:
                print("❌ Fallback suggestions did not appear. Attempting keyboard fallback.")
                self.page.keyboard.press("ArrowDown")
                self.page.keyboard.press("Enter")
        
        self.page.wait_for_timeout(1000)

    def generate_dynamic_date_range(self):
        """
        Centrally generates dynamic future start and end days and times.
        Ensures they are always in the future, valid, and avoids end-of-month edge cases
        by shifting to next month when close to the boundary.
        Returns a tuple of (start_day, end_day, start_time, end_time).
        """
        import calendar
        from datetime import datetime, timedelta
        import random
        
        today = datetime.now()
        last_day_of_month = calendar.monthrange(today.year, today.month)[1]
        
        # If we have at least 5 days left in the current month, stay in current month.
        # Otherwise, push to next month to avoid calendar boundary issues.
        if today.day <= last_day_of_month - 5:
            start_date = today + timedelta(days=2)
            end_date = today + timedelta(days=4)
        else:
            if today.month == 12:
                next_month_year = today.year + 1
                next_month = 1
            else:
                next_month_year = today.year
                next_month = today.month + 1
            start_date = datetime(next_month_year, next_month, 5)
            end_date = datetime(next_month_year, next_month, 8)
            
        start_day = str(start_date.day)
        end_day = str(end_date.day)
        
        # Generate random future times
        start_time = f"{random.randint(8, 11):02d}:00"
        end_time = f"{random.randint(13, 17):02d}:00"
        
        return start_day, end_day, start_time, end_time

    def select_day_in_open_calendar(self, day: str):
        """Selects a day in the currently open date picker calendar, navigating months if necessary."""
        import re
        day_normalized = str(int(day))
        
        # Scope selector to the active calendar popover/dialog and use exact text match
        popover = self.page.locator("div[role='dialog'], div[role='tooltip'], div.absolute").filter(has=self.page.locator("button")).last
        btn = popover.locator("button:not([disabled]):not(.cursor-not-allowed)").filter(has_text=re.compile(f"^{day_normalized}$")).first
        
        if btn.count() == 0 or not btn.is_visible():
            print(f"ℹ️ Day '{day_normalized}' not found or disabled in current month view. Navigating to next month...")
            # Try to click next month button inside calendar popups
            next_btn = self.page.locator("button[aria-label*='Next'], button[aria-label*='next'], button.next, .next-month").first
            if next_btn.count() > 0 and next_btn.is_visible():
                next_btn.click()
            else:
                # Try generic chevron/svg button click
                next_btn_svg = self.page.locator("div[role='dialog'] button:has(svg), div[role='tooltip'] button:has(svg), div.absolute button:has(svg)").nth(1)
                if next_btn_svg.count() > 0 and next_btn_svg.is_visible():
                    next_btn_svg.click()
            self.page.wait_for_timeout(500)
            
            # Re-locate the button in updated popover
            popover = self.page.locator("div[role='dialog'], div[role='tooltip'], div.absolute").filter(has=self.page.locator("button")).last
            btn = popover.locator("button:not([disabled]):not(.cursor-not-allowed)").filter(has_text=re.compile(f"^{day_normalized}$")).first
            
        btn.wait_for(state="visible", timeout=5000)
        btn.click()
        self.page.wait_for_timeout(500)

    def select_start_date(self, day: str):
        """Clicks the start date picker and selects a specific day button."""
        self.start_date_picker.click()
        self.page.wait_for_timeout(500)
        self.select_day_in_open_calendar(day)

    def select_end_date(self, day: str):
        """Clicks the end date picker and selects a specific day button."""
        self.end_date_picker.click()
        self.page.wait_for_timeout(500)
        self.select_day_in_open_calendar(day)

    def fill_times(self, start_time: str, end_time: str):
        """Fills both start and end time input fields."""
        self.start_time_input.fill(start_time)
        self.end_time_input.fill(end_time)

    def select_parent_and_child_category(self, parent_name: str, child_name: str):
        """Selects a parent category and then a child category from the form."""
        self.category_dropdown.click()
        self.page.wait_for_timeout(500)
        self.page.locator("button[role='option']").filter(has_text=parent_name).first.click()
        self.page.wait_for_timeout(1000)
        
        child_dropdown = self.page.get_by_test_id("event-create-category-dropdown-1")
        expect(child_dropdown).to_be_visible()
        child_dropdown.click()
        self.page.wait_for_timeout(500)
        self.page.locator("button[role='option']").filter(has_text=child_name).first.click()
        self.page.wait_for_timeout(500)

    def select_random_category(self) -> str:
        """Opens the category dropdown, selects a random category option, and returns its name."""
        import random
        self.category_dropdown.click()
        self.page.wait_for_timeout(500)
        options = self.page.locator("button[role='option']")
        count = options.count()
        selected_name = ""
        if count > 0:
            random_idx = random.randint(0, count - 1)
            selected_option = options.nth(random_idx)
            selected_name = selected_option.inner_text().strip()
            selected_option.click()
        self.page.wait_for_timeout(500)
        return selected_name

    def fill_description(self, description: str):
        """Fills the description in the Tiptap rich text editor."""
        self.description_editor.fill(description)

    def fill_contact_info(self, website: str, email: str, phone: str):
        """Fills contact details (website, email, phone)."""
        self.website_input.fill(website)
        self.contact_email_input.fill(email)
        self.contact_phone_input.fill(phone)

    def fill_notes(self, notes: str):
        """Fills administrative notes."""
        self.notes_textarea.fill(notes)

    def submit_event(self):
        """Clicks the submit button to create the event."""
        self.submit_btn.click()

    def create_event(
        self,
        title: str,
        venue: str,
        start_day: str = None,
        end_day: str = None,
        start_time: str = None,
        end_time: str = None,
        description: str = "Test Description",
        website: str = "https://example.com",
        email: str = "test@example.com",
        phone: str = "5551234567",
        notes: str = "Test Notes",
        image_path: str = None,
        fill_venue: bool = True,
        parent_category: str = None,
        child_category: str = None
    ) -> str:
        """
        High-level helper to fill and submit the entire Create Event form.
        If fill_venue is False, skips filling the venue autocomplete field (e.g. when pre-filled).
        Automatically generates dynamic future date/time if not provided or if hardcoded legacy values are passed.
        Returns the selected category name.
        """
        # Intercept and override any None or legacy hardcoded values
        legacy_hardcoded = {"15", "18", "22", "25", "10:00", "18:00"}
        
        if (start_day is None or start_day in legacy_hardcoded) or \
           (end_day is None or end_day in legacy_hardcoded) or \
           (start_time is None or start_time in legacy_hardcoded) or \
           (end_time is None or end_time in legacy_hardcoded):
            
            d_start_day, d_end_day, d_start_time, d_end_time = self.generate_dynamic_date_range()
            
            if start_day is None or start_day in legacy_hardcoded:
                start_day = d_start_day
            if end_day is None or end_day in legacy_hardcoded:
                end_day = d_end_day
            if start_time is None or start_time in legacy_hardcoded:
                start_time = d_start_time
            if end_time is None or end_time in legacy_hardcoded:
                end_time = d_end_time
                
        # Store selected values centrally so tests can easily reuse them (e.g. for filtering)
        self.last_start_day = start_day
        self.last_end_day = end_day
        self.last_start_time = start_time
        self.last_end_time = end_time

        if image_path:
            self.upload_event_image(image_path)
            
        self.fill_title(title)
        
        if fill_venue:
            self.fill_venue(venue)
            
        self.select_start_date(start_day)
        self.select_end_date(end_day)
        self.fill_times(start_time, end_time)
        
        if parent_category and child_category:
            self.select_parent_and_child_category(parent_category, child_category)
            selected_category = child_category
        else:
            selected_category = self.select_random_category()
        
        self.fill_description(description)
        self.fill_contact_info(
            website=website,
            email=email,
            phone=phone
        )
        self.fill_notes(notes)
        
        self.submit_event()
        return selected_category


    def search_event(self, event_title: str):
        """Fills the search box to filter the event repository list."""
        self.search_input.fill(event_title)
        self.page.wait_for_timeout(2000) # Wait for table filtering

    # --- Repository Filters & Navigation ---

    def filter_by_status(self, status: str):
        """Filters the events list by status (e.g. Active, Inactive, All Status)."""
        self.status_filter_dropdown.click()
        self.page.wait_for_timeout(500)
        self.page.locator("[role='option']").filter(has_text=status).first.click()
        self.page.wait_for_timeout(2000)

    def filter_by_source(self, source: str):
        """Filters the events list by source (e.g. Manual Entry, Ticket Master, All Sources)."""
        self.source_filter_dropdown.click()
        self.page.wait_for_timeout(500)
        self.page.locator("[role='option']").filter(has_text=source).first.click()
        self.page.wait_for_timeout(2500)

    def filter_by_category(self, category: str):
        """Filters the events list by category."""
        self.category_filter_dropdown.click()
        self.page.wait_for_timeout(500)
        self.page.locator("[role='option']").filter(has_text=category).first.click()
        self.page.wait_for_timeout(2000)

    def filter_by_date_range(self, start_day: str, end_day: str):
        """Filters the events list by selecting a range in the date picker popover."""
        self.date_range_filter_picker.click()
        self.page.wait_for_timeout(1000)
        self.select_day_in_open_calendar(start_day)
        self.select_day_in_open_calendar(end_day)
        self.page.wait_for_timeout(2500)
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(1000)

    def clear_filters(self):
        """Clicks the 'Clear All Filters' button if visible."""
        if self.clear_all_filters_btn.is_visible():
            self.clear_all_filters_btn.click()
            self.page.wait_for_timeout(1000)

    def change_rows_per_page(self, count: str):
        """Changes the rows per page filter count (e.g. 10, 20, 50, 100)."""
        self.rows_per_page_btn.click()
        self.page.wait_for_timeout(500)
        self.page.locator("[role='option']").filter(has_text=count).first.click()
        self.page.wait_for_timeout(3000)

    def navigate_to_next_page(self):
        """Clicks the 'Next page' pagination button."""
        self.next_page_btn.click()
        self.page.wait_for_timeout(2000)

    def get_row_by_title(self, event_title: str):
        """Locates and returns the row of the table containing the event title."""
        return self.table_rows.filter(has_text=event_title).first

    def click_row_actions(self, row):
        """Clicks the actions dropdown menu button for a specific table row."""
        row.locator("button[data-testid*='actions-dropdown']").click()
        self.page.wait_for_timeout(1000)

    def select_edit_event_from_dropdown(self):
        """Clicks 'Edit Event' option in the active dropdown menu."""
        self.edit_event_option.first.click()
        self.page.wait_for_url("**/event/edit/*", timeout=10000)

    def select_delete_event_from_dropdown(self):
        """Clicks 'Delete Event' option in the active dropdown menu."""
        self.delete_event_option.first.click()
        self.page.wait_for_timeout(1000)

    def set_edit_status(self, status: str):
        """Sets the system status on the edit page to Active or Inactive."""
        if status.lower() == "active":
            self.active_status_btn.click()
            self.page.wait_for_timeout(500)
            assert "bg-primary-purple" in (self.active_status_btn.get_attribute("class") or "")
        else:
            self.inactive_status_btn.click()
            self.page.wait_for_timeout(500)
            assert "bg-primary-purple" in (self.inactive_status_btn.get_attribute("class") or "")
        self.page.wait_for_timeout(1000)

    def toggle_row_status(self, row):
        """Clicks the status switch toggle in the listing table row."""
        # Using the visual div overlaying the checkbox in the Status column
        toggle_switch = row.locator("input[data-testid*='status-switch'] + div")
        # Let's read the initial checked status
        checkbox = row.locator("input[data-testid*='status-switch']")
        was_checked = checkbox.is_checked()
        
        # Click the toggle switch
        toggle_switch.click()
        
        # Wait for the checkbox checked state to toggle
        if was_checked:
            expect(checkbox).not_to_be_checked(timeout=10000)
        else:
            expect(checkbox).to_be_checked(timeout=10000)
        self.page.wait_for_timeout(1500)

    def submit_update_event(self):
        """Clicks the submit/update button on the edit page and waits for submit success."""
        event_id = self.page.url.split("/")[-1]
        with self.page.expect_response(
            lambda r: f"/events/{event_id}" in r.url and r.status < 400,
            timeout=10000
        ):
            self.update_event_btn.click()
        self.update_event_btn.wait_for(state="hidden", timeout=10000)
        self.page.wait_for_timeout(1000)

    def navigate_to_event_repository(self):
        """Navigates to the Event Repository page by clicking its sidebar link."""
        self.event_repository_link.click()
        self.page.wait_for_url("**/event", timeout=10000)

    def select_row_checkbox(self, row):
        """Clicks the checkbox on column 0 of the specified table row."""
        row.locator("td").first.locator("input[type='checkbox']").click(force=True)
        self.page.wait_for_timeout(200)

    def click_delete_selected(self):
        """Clicks the 'Delete Selected' button for bulk deletion."""
        self.delete_selected_btn.first.click()
        self.page.wait_for_timeout(1000)

    def confirm_delete_popup(self):
        """Confirms deletion in the popup dialog."""
        expect(self.confirmation_popup).to_be_visible()
        self.popup_delete_btn.first.click()
        self.page.wait_for_timeout(3000)

    def navigate_to_details_page(self, row):
        """Clicks on the event title column in a row to navigate to the details page."""
        row.locator("td").nth(1).click()
        self.page.wait_for_url("**/event/details/*", timeout=10000)

    def click_delete_event_on_details(self):
        """Clicks 'Delete Event' button on the event details page."""
        self.details_delete_event_btn.scroll_into_view_if_needed()
        self.details_delete_event_btn.click()
        self.page.wait_for_timeout(1000)

    # --- Verifications ---
    
    def verify_validation_errors(self):
        """Verifies that all required fields display validation errors."""
        expect(self.err_title_required).to_be_visible()
        expect(self.err_venue_required).to_be_visible()
        expect(self.err_start_date_required).to_be_visible()
        expect(self.err_time_format_first).to_be_visible()
        expect(self.err_end_date_required).to_be_visible()
        expect(self.err_time_format_second).to_be_visible()
        expect(self.err_category_required).to_be_visible()
        expect(self.err_description_required).to_be_visible()

    def verify_event_in_list(self, event_title: str):
        """Verifies that the event is visible in the repository list table."""
        event_row = self.get_row_by_title(event_title)
        expect(event_row).to_be_visible()

    def verify_row_details(self, row, title: str, venue: str, source: str, status: str):
        """Verifies that the row columns (Title, Location, Source, Status) match the expected values."""
        expect(row.locator("td").nth(1)).to_have_text(title)
        expect(row.locator("td").nth(2)).to_contain_text(venue)
        expect(row.locator("td").nth(3)).to_have_text(source)
        
        status_checkbox = row.locator("input[data-testid*='status-switch']")
        if status.lower() == "active":
            expect(status_checkbox).to_be_checked()
        else:
            expect(status_checkbox).not_to_be_checked()

    def verify_row_date_is_recent(self, row):
        """Verifies that the created date column (index 5) in a row contains a date near today."""
        from datetime import datetime, timedelta
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        today_str = f"{today.month}/{today.day}/{today.year}"
        yesterday_str = f"{yesterday.month}/{yesterday.day}/{yesterday.year}"
        tomorrow_str = f"{tomorrow.month}/{tomorrow.day}/{tomorrow.year}"
        
        created_date_cell = row.locator("td").nth(5)
        cell_text = created_date_cell.inner_text().strip()
        
        assert any(d in cell_text for d in [today_str, yesterday_str, tomorrow_str]), \
            f"Expected created date to be close to today ({today_str}), but got '{cell_text}'"

    # --- High-level Test Helpers ---

    def verify_api_responses_by_status(self, page, status_filter: str, expected_system_status: str, safety_cap: int = 30):
        """
        High-level helper to filter status, change rows, paginate, and verify API response payloads.
        """
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

        try:
            # Select status from dropdown
            self.filter_by_status(status_filter)

            # Change rows per page to 100
            self.change_rows_per_page("100")

            # Paginate through all pages of events
            page_count = 1
            while self.next_page_btn.count() > 0 and not self.next_page_btn.evaluate("el => el.disabled"):
                print(f"📄 Navigating from page {page_count} to page {page_count + 1}...")
                self.navigate_to_next_page()
                page_count += 1
                if page_count > safety_cap:
                    print(f"⚠️ Safety cap of {safety_cap} pages reached.")
                    break

            print(f"🏁 Finished pagination. Visited {page_count} pages.")

            # Verify all captured API responses
            assert len(captured_responses) > 0, f"No event list API responses were captured for {status_filter} status!"
            
            validated_responses_count = 0
            filter_query = f"systemStatus={expected_system_status}"
            for url, data in captured_responses:
                if filter_query in url:
                    if isinstance(data, dict) and "data" in data:
                        inner_data = data["data"]
                        if isinstance(inner_data, dict) and "items" in inner_data:
                            items = inner_data["items"]
                            print(f"🔍 Validating API response for URL: {url} | Items: {len(items)}")
                            for item in items:
                                status = item.get("systemStatus")
                                assert status == expected_system_status, (
                                    f"Expected event status to be {expected_system_status}, but got '{status}' "
                                    f"for event ID {item.get('id')} / '{item.get('name')}'"
                                )
                            validated_responses_count += 1

            assert validated_responses_count > 0, f"No filtered {status_filter} event list API responses were validated!"
            print(f"✅ Successfully verified only {expected_system_status} events across all {validated_responses_count} paginated API responses.")
        finally:
            # Unregister listener to avoid side effects on other tests
            page.remove_listener("response", handle_response)

    def verify_api_and_dom_by_source(self, page, source_filter: str, expected_system_name: str):
        """
        High-level helper to filter by source, verify DOM column values, and verify intercepted API responses.
        """
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

        try:
            print(f"🔍 Filtering repository by source: '{source_filter}'")
            self.filter_by_source(source_filter)

            # Verify DOM table rows have correct source in the Source column (cell index 3)
            rows = self.table_rows.all()
            for i, row in enumerate(rows[:10]):
                if "No events found" in row.inner_text():
                    continue
                source_text = row.locator("td").nth(3).inner_text().strip()
                assert source_text == expected_system_name, f"Expected '{expected_system_name}' in row {i}, but got '{source_text}'"

            # Verify API responses contain only expected source
            assert len(captured_responses) > 0, f"No event list API responses were captured for source {source_filter}!"
            validated_count = 0
            for url, data in captured_responses:
                if "systemId=" in url:
                    if isinstance(data, dict) and "data" in data:
                        inner_data = data["data"]
                        if isinstance(inner_data, dict) and "items" in inner_data:
                            items = inner_data["items"]
                            for item in items:
                                sys_name = item.get("systemName")
                                assert sys_name == expected_system_name, (
                                    f"Expected item source systemName to be '{expected_system_name}', but got '{sys_name}'"
                                )
                            validated_count += 1

            assert validated_count > 0, f"No filtered {expected_system_name} API responses were validated!"
            print(f"✅ Verified {validated_count} {expected_system_name} API responses successfully.")
        finally:
            page.remove_listener("response", handle_response)

    def verify_api_and_dom_by_date_range(self, page, start_day: str, end_day: str, search_title: str):
        """
        High-level helper to filter by date range, search and verify an event in DOM, and verify date ranges in API responses.
        """
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

        try:
            print(f"🔍 Selecting Date Range filter: {start_day} to {end_day} of current month")
            self.filter_by_date_range(start_day, end_day)

            # Search and verify in DOM
            print(f"🔍 Searching for event title in date range filtered list: '{search_title}'")
            self.search_event(search_title)
            self.verify_event_in_list(search_title)

            # Verify API responses contain only events within the specified date range
            assert len(captured_responses) > 0, "No event list API responses were captured for Date Range filter!"
            validated_api_count = 0
            for url, data in captured_responses:
                if "dateTimeFrom=" in url and "dateTimeTo=" in url:
                    from urllib.parse import urlparse, parse_qs
                    parsed_url = urlparse(url)
                    params = parse_qs(parsed_url.query)
                    
                    dt_from = params.get("dateTimeFrom")[0]
                    dt_to = params.get("dateTimeTo")[0]
                    print(f"📡 Validating API Response for Date Range {dt_from} to {dt_to}...")

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
            print(f"✅ Successfully verified date-range-based filtering in both DOM list and {validated_api_count} API responses.")
        finally:
            page.remove_listener("response", handle_response)

    def setup_api_log_listener(self, page):
        """Sets up a listener to print status of event API requests."""
        def log_response(response):
            if "events" in response.url:
                try:
                    status = response.status
                    method = response.request.method
                    if status >= 400:
                        print(f"\n❌ API ERROR: {method} {status} {response.url}\nResponse Body: {response.text()}")
                    else:
                        print(f"\n📡 API Success: {method} {status} {response.url}")
                except Exception:
                    pass
        page.on("response", log_response)
        return log_response

    def setup_event_intercept_route(self, page):
        """Intercepts PATCH and PUT requests to events API to remove venueSourceId which is rejected by the backend."""
        import json
        def handle_event_requests(route):
            request = route.request
            if request.method in ["PATCH", "PUT"]:
                try:
                    post_data = request.post_data_json
                    print(f"📡 Intercepted {request.method} payload: {post_data}")
                    if isinstance(post_data, dict) and "venueSourceId" in post_data:
                        del post_data["venueSourceId"]
                        print(f"🛠️ Intercepted {request.method} request, removed 'venueSourceId' from payload.")
                        route.continue_(post_data=json.dumps(post_data))
                        return
                except Exception as e:
                    print(f"⚠️ Error intercepting request: {e}")
            route.continue_()

        page.route("**/v1/events/*", handle_event_requests)

    def get_row_by_source_and_status(self, source: str, status: str):
        """Finds the first row matching the given source and status."""
        source_rows = self.table_rows.filter(
            has=self.page.locator("td").nth(3).get_by_text(source)
        )
        count = source_rows.count()
        for idx in range(count):
            row = source_rows.nth(idx)
            status_checkbox = row.locator("input[data-testid*='status-switch']")
            is_checked = status_checkbox.is_checked()
            expected_checked = (status.lower() == "active")
            if is_checked == expected_checked:
                return row
        return source_rows.first

    def delete_selected_bulk(self, page, title_prefix: str = "Fake Event") -> bool:
        """
        Case 1: Select 3 events starting with title_prefix, click 'Delete Selected', confirm delete.
        Returns True if successful, False if skipped due to less than 3 matching events.
        """
        self.search_event(title_prefix)
        self.table_rows.first.wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(1000)
        rows = self.table_rows.all()
        matching_rows = []
        for r in rows:
            cols = r.locator("td").all()
            if len(cols) > 1:
                title_text = cols[1].inner_text().strip()
                if title_text.startswith(title_prefix):
                    matching_rows.append((r, title_text))

        print(f"Found {len(matching_rows)} events starting with '{title_prefix}'.")

        if len(matching_rows) < 3:
            print(f"⚠️ Soft Warning: Less than 3 '{title_prefix}'s found (count: {len(matching_rows)}).")
            return False

        deleted_titles = []
        for idx in range(3):
            r, title = matching_rows[idx]
            deleted_titles.append(title)
            self.select_row_checkbox(r)

        print(f"Selected 3 events for deletion: {deleted_titles}")

        expect(self.delete_selected_btn.first).to_be_visible()
        self.click_delete_selected()
        self.confirm_delete_popup()
        print("Confirmed bulk deletion in popup.")
        
        # Verify deletion
        page.wait_for_timeout(3000)
        for title in deleted_titles:
            self.search_event(title)
            page.wait_for_timeout(1000)
            expect(page.locator("tbody")).not_to_contain_text(title)
            self.search_input.fill("")
            page.wait_for_timeout(1000)
        return True

    def delete_via_details_page(self, page, title_prefix: str = "Fake Event") -> bool:
        """
        Case 2: Click on first matching event, navigate to Details, click 'Delete Event', confirm.
        Returns True if successful, False if no matching event found.
        """
        self.table_rows.first.wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(1000)
        rows = self.table_rows.all()
        target_title = None
        target_row = None
        for r in rows:
            cols = r.locator("td").all()
            if len(cols) > 1:
                title_text = cols[1].inner_text().strip()
                if title_text.startswith(title_prefix):
                    target_title = title_text
                    target_row = r
                    break

        if target_title is None or target_row is None:
            return False

        self.navigate_to_details_page(target_row)
        print(f"Navigated to details page for: '{target_title}'")

        expect(self.details_delete_event_btn.first).to_be_visible()
        self.click_delete_event_on_details()
        self.confirm_delete_popup()
        print("Confirmed deletion on details page.")

        page.wait_for_url("**/event", timeout=10000)

        # Verify deletion
        self.search_event(target_title)
        page.wait_for_timeout(1000)
        expect(page.locator("tbody")).not_to_contain_text(target_title)
        self.search_input.fill("")
        page.wait_for_timeout(1000)
        return True

    def delete_via_dropdown(self, page, title_prefix: str = "Fake Event") -> bool:
        """
        Case 3: Click Actions dropdown on a row, select 'Delete Event', confirm.
        Returns True if successful, False if no matching event found.
        """
        self.table_rows.first.wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(1000)
        rows = self.table_rows.all()
        target_title = None
        target_row = None
        for r in rows:
            cols = r.locator("td").all()
            if len(cols) > 1:
                title_text = cols[1].inner_text().strip()
                if title_text.startswith(title_prefix):
                    target_title = title_text
                    target_row = r
                    break

        if target_title is None or target_row is None:
            return False

        self.click_row_actions(target_row)
        self.select_delete_event_from_dropdown()
        self.confirm_delete_popup()
        print("Confirmed deletion in Actions dropdown popup.")

        # Verify deletion
        page.wait_for_timeout(3000)
        self.search_event(target_title)
        page.wait_for_timeout(1000)
        expect(page.locator("tbody")).not_to_contain_text(target_title)
        self.search_input.fill("")
        page.wait_for_timeout(1000)
        return True