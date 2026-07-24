import random
import time
from faker import Faker
from playwright.sync_api import Page, expect

class PlaceListing:
    def __init__(self, page: Page):
        self.page = page

        # Page header and actions
        self.heading = page.get_by_role("heading", name="Place Listing Management")
        self.add_new_btn = page.get_by_test_id("place-add-new-btn")
        
        # Repository list search
        self.search_input = page.get_by_placeholder("Search by title, venue, or location ...")

        # Validation messages
        self.place_name_error = page.get_by_text("Place name is required")
        self.description_error = page.get_by_text("Description is required")
        self.place_category_error = page.get_by_text("Place category is required")
        self.rating_error = page.get_by_text("Rating is required")
        self.address_error = page.get_by_text("Address is required")
        self.city_error = page.get_by_text("City is required")
        self.state_error = page.get_by_text("State is required")
        self.zip_error = page.get_by_text("ZIP code is required")
        self.country_error = page.get_by_text("Country is required")
        self.latitude_error = page.get_by_text("Latitude is required")
        self.longitude_error = page.get_by_text("Longitude is required")
        self.phone_error = page.get_by_text("Phone number is required")
        self.email_error = page.get_by_text("Must be a valid email address")

        # Create Place Listing form fields
        self.upload_image_trigger = page.get_by_test_id("place-create-image-upload")
        self.file_input = page.locator('input[type="file"]')
        self.place_name_input = page.get_by_test_id("place-create-name-input")
        # The place form uses a Tiptap contenteditable editor rather than a
        # textarea.  It currently has no dedicated test id.
        self.place_description_input = page.locator("div.ProseMirror[contenteditable='true']").first
        self.category_dropdown = page.get_by_test_id("place-create-category-dropdown")
        self.rating_input = page.get_by_test_id("place-create-rating-input")
        self.city_input = page.get_by_test_id("place-create-city-input")
        self.state_input = page.get_by_test_id("place-create-state-input")
        self.zipcode_input = page.get_by_test_id("place-create-zipcode-input")
        self.country_input = page.get_by_test_id("place-create-country-input")
        self.phone_input = page.get_by_test_id("place-create-phone-input")
        self.alt_phone_input = page.get_by_test_id("place-create-alt-phone-input")
        self.email_input = page.get_by_test_id("place-create-email-input")
        self.website_input = page.get_by_test_id("place-create-website-input")
        self.facebook_input = page.get_by_test_id("place-create-facebook-input")
        self.instagram_input = page.get_by_test_id("place-create-instagram-input")
        self.twitter_input = page.get_by_test_id("place-create-twitter-input")
        self.notes_textarea = page.get_by_test_id("place-create-notes-textarea")
        self.save_button = page.get_by_test_id("place-create-save-btn")
        self.venue_location = page.get_by_placeholder("Search venue location")
        self.three_dot_button = page.locator("button[data-testid$='actions-dropdown']")
        self.edit_menuitem = page.get_by_role("menuitem", name="Edit Place")
        self.delete_menuitem = page.get_by_role("menuitem", name="Delete Place")
        self.delete_confirm_dialog = page.get_by_test_id("place-delete-confirm-dialog")
        self.save_place = page.get_by_role("button", name="Save Place")
        
        
        
    def verify_place_listing_page_visible(self):
        expect(self.heading).to_be_visible()
        expect(self.add_new_btn).to_be_visible()

    def click_add_new_place(self):
        self.add_new_btn.click()
        expect(self.place_name_input).to_be_visible()
        expect(self.save_button).to_be_visible()

    def upload_place_image(self, image_path: str):
        if self.file_input.count() > 0:
            self.file_input.set_input_files(image_path)
        else:
            self.upload_image_trigger.set_input_files(image_path)

    def select_category(self, category_name: str | None = None) -> str:
        self.category_dropdown.click()
        self.page.wait_for_timeout(500)
        options = self.page.locator("[role='option']")
        if category_name:
            selected_option = options.filter(has_text=category_name).first
            if selected_option.count() > 0:
                selected_option.click()
                return category_name
        option_count = options.count()
        if option_count == 0:
            return ""
        chosen = random.randint(0, option_count - 1)
        chosen_option = options.nth(chosen)
        display_text = chosen_option.inner_text().strip()
        chosen_option.click()
        self.page.wait_for_timeout(500)
        return display_text

    def _generate_unique_telephone(self) -> str:
        """Generate a unique 10-digit phone number starting with 9."""
        return "9" + "".join(str(random.randint(0, 9)) for _ in range(9))

    def fill_place_form_with_fake_data(self):
        fake = Faker()
        self.place_name_input.type(f"{fake.company()} Place")
        time.sleep(2)
        self.place_description_input.type(fake.paragraph(nb_sentences=3))
        time.sleep(2)
        self.select_category()
        time.sleep(2)
        self.rating_input.type(str(random.randint(1, 5)))
        time.sleep(2)
        self.city_input.type(fake.city())
        time.sleep(2)
        self.state_input.type(fake.state())
        time.sleep(2)
        self.zipcode_input.type(fake.postcode())
        time.sleep(2)
        self.country_input.type(fake.country())
        time.sleep(2)
        self.phone_input.type(self._generate_unique_telephone())
        time.sleep(2)
        self.alt_phone_input.type(self._generate_unique_telephone())
        time.sleep(2)
        self.email_input.type(fake.ascii_free_email())
        self.website_input.type(fake.url())
        if self.facebook_input.count() > 0:
            self.facebook_input.type(f"https://facebook.com/{fake.user_name()}")
        if self.instagram_input.count() > 0:
            self.instagram_input.type(f"https://instagram.com/{fake.user_name()}")
        if self.twitter_input.count() > 0:
            self.twitter_input.type(f"https://twitter.com/{fake.user_name()}")
        self.notes_textarea.type(fake.sentence(nb_words=14))

    def fill_place_form_with_venue_location(self, venue_name: str, postal_code: str, place_name: str = None):
        """
        Fills place form with Google autocomplete venue selection.
        City/State auto-populate from selected location, only postal code is required.
        """
        fake = Faker()
        
        place_name = place_name or f"{fake.company()} Place"
        self.place_name_input.type(place_name)
        time.sleep(1)
        
        self.place_description_input.type(fake.paragraph(nb_sentences=3))
        time.sleep(1)
        
        self.select_category()
        time.sleep(1)
        
        self.rating_input.type(str(random.randint(1, 5)))
        time.sleep(1)
        
        # Fill venue location using autocomplete
        self.fill_venue_location_with_autocomplete(venue_name, postal_code)
        time.sleep(2)
        
        self.country_input.type(fake.country())
        time.sleep(1)
        
        self.phone_input.type(self._generate_unique_telephone())
        time.sleep(1)
        
        self.alt_phone_input.type(self._generate_unique_telephone())
        time.sleep(1)
        
        self.email_input.type(fake.ascii_free_email())
        time.sleep(1)
        
        self.website_input.type(fake.url())
        time.sleep(1)
        
        if self.facebook_input.count() > 0:
            self.facebook_input.type(f"https://facebook.com/{fake.user_name()}")
            time.sleep(1)
        
        if self.instagram_input.count() > 0:
            self.instagram_input.type(f"https://instagram.com/{fake.user_name()}")
            time.sleep(1)
        
        if self.twitter_input.count() > 0:
            self.twitter_input.type(f"https://twitter.com/{fake.user_name()}")
            time.sleep(1)
        
        self.notes_textarea.type(fake.sentence(nb_words=14))


    def fill_venue_location_with_autocomplete(self, venue_name: str, postal_code: str = ""):
        """
        Fills venue location, waits for Google autocomplete suggestions,
        selects the first option using keyboard, and fills postal code if provided.
        Falls back to manual entry of address details if autocomplete fails to trigger or populate.
        """
        self.venue_location.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(500)
        
        # Type venue name sequentially to trigger autocomplete
        self.venue_location.type(venue_name, delay=100)
        self.page.wait_for_timeout(1500)
        
        # Use keyboard to select first suggestion
        self.page.keyboard.press("ArrowDown")
        self.page.wait_for_timeout(300)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1000)
        
        # Fill postal code if provided
        if postal_code:
            self.zipcode_input.fill(postal_code)
            self.page.wait_for_timeout(500)
        
        # Robust fallback: If Google autocomplete failed to populate city, state, country, lat, or long
        # (common in headless CI pipelines), manually fill them with fallback coordinates/details.
        fallbacks = {
            "delhi": {"city": "New Delhi", "state": "Delhi", "country": "India", "lat": "28.6139", "long": "77.2090"},
            "bangalore": {"city": "Bengaluru", "state": "Karnataka", "country": "India", "lat": "12.9716", "long": "77.5946"},
            "chennai": {"city": "Chennai", "state": "Tamil Nadu", "country": "India", "lat": "13.0827", "long": "80.2707"},
            "kolkata": {"city": "Kolkata", "state": "West Bengal", "country": "India", "lat": "22.5726", "long": "88.3639"}
        }

        lat_input = self.page.locator("input[name='location.lat']").last
        long_input = self.page.locator("input[name='location.long']").last

        v_lower = venue_name.lower()
        matched_key = None
        for key in fallbacks:
            if key in v_lower:
                matched_key = key
                break
        
        fallback_data = fallbacks[matched_key] if matched_key else {"city": venue_name, "state": "State", "country": "India", "lat": "22.5726", "long": "88.3639"}

        if not self.city_input.input_value():
            self.city_input.fill(fallback_data["city"])
            print(f"⚠️ Autocomplete failed to fill city. Filled with fallback: {fallback_data['city']}")
        if not self.state_input.input_value():
            self.state_input.fill(fallback_data["state"])
            print(f"⚠️ Autocomplete failed to fill state. Filled with fallback: {fallback_data['state']}")
        if not self.country_input.input_value():
            self.country_input.fill(fallback_data["country"])
            print(f"⚠️ Autocomplete failed to fill country. Filled with fallback: {fallback_data['country']}")
        if not lat_input.input_value():
            lat_input.fill(fallback_data["lat"])
            print(f"⚠️ Autocomplete failed to fill latitude. Filled with fallback: {fallback_data['lat']}")
        if not long_input.input_value():
            long_input.fill(fallback_data["long"])
            print(f"⚠️ Autocomplete failed to fill longitude. Filled with fallback: {fallback_data['long']}")

        print(f"✅ Finished selecting and checking address fields for venue '{venue_name}'.")

    def submit_place_form(self):
        self.save_button.click()
        
    def submit_save_place(self):
        self.save_place.click()

    def verify_place_validation_errors(self):
        expect(self.place_name_error).to_be_visible()
        expect(self.description_error).to_be_visible()
        expect(self.place_category_error).to_be_visible()
        expect(self.rating_error).to_be_visible()
        expect(self.address_error).to_be_visible()
        expect(self.city_error).to_be_visible()
        expect(self.state_error).to_be_visible()
        expect(self.zip_error).to_be_visible()
        expect(self.country_error).to_be_visible()
        expect(self.latitude_error).to_be_visible()
        expect(self.longitude_error).to_be_visible()
        expect(self.phone_error).to_be_visible()
        expect(self.email_error).to_be_visible()
    
    def search_place(self, place_name: str):
        """Search for a place by name in the place listing repository."""
        self.search_input.fill(place_name)
        self.page.wait_for_timeout(2000)
    
    def verify_place_in_list(self, place_name: str):
        """Verify that a place is visible in the place listing table."""
        place_row = self.page.locator("tbody tr").filter(has_text=place_name).first
        expect(place_row).to_be_visible()

    def verify_place_contains(self, place_name: str, text: str):
        """Verify that the place row contains specific text (e.g., updated phone or description)."""
        place_row = self.page.locator("tbody tr").filter(has_text=place_name).first
        expect(place_row).to_be_visible()
        expect(place_row).to_contain_text(text)

    def _open_actions_for_place(self, place_name: str):
        """Open the row actions menu (three dots) for a given place and return the row locator."""
        row = self.page.locator("tbody tr").filter(has_text=place_name).first
        expect(row).to_be_visible()

        # Try common action button selectors within the row
        try:
            row.locator("button[aria-label='More']").first.click()
            return row
        except Exception:
            pass

        try:
            row.locator("button:has-text('...')").first.click()
            return row
        except Exception:
            pass

        # Fallback: click the first button in the row (usually actions)
        row.locator("button").first.click()
        return row

    def click_edit_for_place(self, place_name: str):
        """Open actions and click Edit for the specified place."""
        self._open_actions_for_place(place_name)
        # Try role-based menu item
        try:
            self.page.get_by_role("menuitem", name="Edit").first.click()
            return
        except Exception:
            pass
        # Fallback text selector
        self.page.get_by_text("Edit").first.click()

    def click_delete_for_place(self, place_name: str):
        """Open actions and click Delete for the specified place."""
        self._open_actions_for_place(place_name)
        try:
            self.page.get_by_role("menuitem", name="Delete").first.click()
            return
        except Exception:
            pass
        self.page.get_by_text("Delete").first.click()

    def confirm_delete(self):
        """Confirm deletion in the confirmation dialog."""
        # Try the dialog-specific delete button if available
        if self.delete_confirm_dialog.count() > 0:
            delete_button = self.delete_confirm_dialog.locator("button:has-text('Delete'):not(:disabled)")
            if delete_button.count() > 0:
                delete_button.first.click()
                return

        # Fallback: use the first visible enabled Delete button on the page
        visible_delete = self.page.locator("button:has-text('Delete'):not(:disabled)")
        if visible_delete.count() > 0:
            visible_delete.first.click()
            return

        raise AssertionError("Unable to find a visible enabled Delete confirmation button.")
    def edit_place_description_and_phone(self, place_name: str, new_description: str, new_phone: str):
        """Open edit, change description and phone, then save."""
        self.click_edit_for_place(place_name)
        # Wait for edit form to appear (reuse existing inputs)
        expect(self.place_description_input).to_be_visible()
        self.place_description_input.fill(new_description)
        self.phone_input.fill(new_phone)
        self.save_button.click()
        self.page.wait_for_timeout(1000)

    def edit_place_listing(self):
        self.three_dot_button.click()
        self.edit_menuitem.click()
        
    def delete_place_listing(self):
        self.three_dot_button.click()
        self.delete_menuitem.click()
        self.confirm_delete()
    
        
        
        
