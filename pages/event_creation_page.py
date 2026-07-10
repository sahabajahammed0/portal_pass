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
        """Fills the venue search input and selects the first option from suggestions."""
        self.venue_search_input.fill(venue_name)
        self.page.wait_for_timeout(1500) # Wait for suggestions to render
        
        # Try to click matching suggestion button, fallback to ArrowDown and Enter
        suggestions = self.page.locator(f"button:has-text('{venue_name}')")
        if suggestions.count() > 0:
            suggestions.first.click()
        else:
            self.page.keyboard.press("ArrowDown")
            self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1000)

    def select_start_date(self, day: str):
        """Clicks the start date picker and selects a specific day button."""
        self.start_date_picker.click()
        self.page.wait_for_timeout(500)
        self.page.locator("button").filter(has_text=day).first.click()
        self.page.wait_for_timeout(500)

    def select_end_date(self, day: str):
        """Clicks the end date picker and selects a specific day button."""
        self.end_date_picker.click()
        self.page.wait_for_timeout(500)
        self.page.locator("button").filter(has_text=day).first.click()
        self.page.wait_for_timeout(500)

    def fill_times(self, start_time: str, end_time: str):
        """Fills both start and end time input fields."""
        self.start_time_input.fill(start_time)
        self.end_time_input.fill(end_time)

    def select_random_category(self):
        """Opens the category dropdown and selects a random category option."""
        import random
        self.category_dropdown.click()
        self.page.wait_for_timeout(500)
        options = self.page.locator("button[role='option']")
        count = options.count()
        if count > 0:
            random_idx = random.randint(0, count - 1)
            options.nth(random_idx).click()
        self.page.wait_for_timeout(500)

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

    def search_event(self, event_title: str):
        """Fills the search box to filter the event repository list."""
        self.search_input.fill(event_title)
        self.page.wait_for_timeout(2000) # Wait for table filtering

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
        event_row = self.page.locator("tbody tr").filter(has_text=event_title).first
        expect(event_row).to_be_visible()
