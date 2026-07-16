from playwright.sync_api import Page, expect

class UserEventPage:
    """
    Page object for the public/user-facing Events page on Portal Pass.
    Defines UI elements and interactive helper methods corresponding to the public event search & filters.
    """

    def __init__(self, page: Page):
        self.page = page

        # General / Navigation elements
        self.home_link = page.get_by_role("link", name="Portal Pass").first
        self.discover_heading = page.get_by_role("heading", name="Discover Events & Places Near")
        self.events_link = page.get_by_role("link", name="Events").first
        
        # Events Explore Main Page elements
        self.explore_heading = page.get_by_role("heading", name="Explore Events")
        self.search_box = page.get_by_role("searchbox", name="Search events")
        self.filters_button = page.get_by_role("button", name="Filters")
        # Locate the Sort button dynamically by matching any of its possible text labels
        self.sort_by_button = page.locator(
            'button:has-text("Sort by"), '
            'button:has-text("Name (A-Z)"), '
            'button:has-text("Name (Z-A)"), '
            'button:has-text("Earliest First"), '
            'button:has-text("Newest First")'
        )
        
        # Views
        self.grid_view_button = page.get_by_role("button", name="Grid view")
        self.map_view_button = page.get_by_role("button", name="Map view")
        
        # Filter Configuration Dialog / Panel elements
        self.filter_dialog_container = page.get_by_label("Filter Configuration")
        self.location_input_trigger = page.locator(".relative.flex.items-center").first
        self.search_radius_button = page.get_by_role("button", name="Search Radius")
        self.from_date_button = page.get_by_role("button", name="From Date")
        self.to_date_button = page.get_by_role("button", name="To Date")
        
        self.categories_trigger = page.get_by_text("No categories selected")
        self.apply_filter_button = page.get_by_role("button", name="Apply Filter")

    def navigate_to_home_user_portal(self, base_url: str = "https://portal-pass-web.weavers-web.com/"):
        """Navigates to the home page of the user portal."""
        self.page.goto(base_url)
        # Verify the main discover heading on home page
        expect(self.page.get_by_role("heading", name="Discover Events & Places Near You")).to_be_visible()

    def verify_footer_links(self):
        """Verifies that all standard footer links are visible on the page."""
        footer_link_names = [
            "Categories",
            "About",
            "Events",
            "Saved Event",
            "Become a partner",
            "Places",
            "How It works",
            "FAQ",
            "Contact us"
        ]
        # Scope link lookups to the footer element to avoid strict mode violations (e.g. Events link in header)
        footer = self.page.locator("footer")
        for name in footer_link_names:
            expect(footer.get_by_role("link", name=name)).to_be_visible()

    def go_to_events(self):
        """Clicks the 'Events' link to navigate to the Explore Events page."""
        self.events_link.click()
        expect(self.explore_heading).to_be_visible()
        expect(self.search_box).to_be_visible()
        expect(self.filters_button).to_be_visible()
        expect(self.sort_by_button).to_be_visible()

    def search_event(self, query: str):
        """Clicks and fills the search box with the specified query."""
        self.search_box.click()
        self.search_box.fill(query)
        # Wait dynamically until all rendered card titles contain the query (case-insensitive)
        query_escaped = query.lower().replace("'", "\\'")
        js_expr = f"() => Array.from(document.querySelectorAll('a[href^=\"/event/\"].text-xl.font-bold')).every(el => el.innerText.toLowerCase().includes('{query_escaped}'))"
        self.page.wait_for_function(js_expr, timeout=5000)

    def open_filters(self):
        """Clicks the 'Filters' button to open the filter configuration drawer."""
        self.filters_button.click()
        self.filter_dialog_container.wait_for(state="visible", timeout=5000)

    def click_location_trigger(self):
        """Clicks the location/address trigger field inside filters."""
        self.location_input_trigger.click()

    def click_search_radius(self):
        """Clicks the 'Search Radius' button inside filters."""
        self.search_radius_button.click()

    def click_from_date(self):
        """Clicks the 'From Date' date picker trigger."""
        self.from_date_button.click()

    def click_to_date(self):
        """Clicks the 'To Date' date picker trigger."""
        self.to_date_button.click()

    def select_date_range(self, from_day: str, to_day: str):
        """Selects From Date and To Date from the filter modal calendar."""
        self.click_from_date()
        from_day_str = from_day.zfill(2)
        self.page.get_by_role("button", name=from_day_str, exact=True).click()
        
        self.click_to_date()
        to_day_str = to_day.zfill(2)
        self.page.get_by_role("button", name=to_day_str, exact=True).click()

    def select_category(self, category_name: str):
        """Opens the category selection filter dropdown and clicks the specified category option."""
        if self.categories_trigger.is_visible():
            self.categories_trigger.click()
        else:
            self.page.locator("span:has-text('Categories')").click()
            
        self.filter_dialog_container.get_by_text(category_name).click()

    def select_parent_and_child_filter(self, parent_name: str, child_name: str):
        """Expands the parent category in the filters, then checks the child subcategory."""
        expand_btn = self.filter_dialog_container.get_by_role("button", name=f"Expand {parent_name}")
        expand_btn.click()
        
        checkbox = self.filter_dialog_container.get_by_role("checkbox", name=child_name)
        checkbox.wait_for(state="attached", timeout=5000)
        checkbox_id = checkbox.get_attribute("id")
        self.filter_dialog_container.locator(f"label[for='{checkbox_id}']").click()

    def apply_filters(self):
        """Clicks the 'Apply Filter' button."""
        self.apply_filter_button.click()
        self.filter_dialog_container.wait_for(state="hidden", timeout=5000)

    def click_sort_by(self):
        """Clicks the 'Sort by' button to open sorting options."""
        self.sort_by_button.click()

    def toggle_grid_view(self):
        """Switches to Grid view."""
        self.grid_view_button.click()
        try:
            self.page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass

    def toggle_map_view(self):
        """Switches to Map view."""
        self.map_view_button.click()
        try:
            self.page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass

    def get_event_titles(self) -> list[str]:
        """Returns a list of all visible event titles."""
        titles_locator = self.page.locator('a[href^="/event/"].text-xl.font-bold')
        try:
            titles_locator.first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass
        try:
            self.page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass
        count = titles_locator.count()
        titles = []
        for i in range(count):
            titles.append(titles_locator.nth(i).inner_text().strip())
        return titles

    def verify_event_in_results(self, title: str):
        """Verifies that an event with the exact title is in the results list."""
        titles = self.get_event_titles()
        if not titles:
            raise AssertionError("No event cards found in search results")
        if title not in titles:
            raise AssertionError(f"Expected event title '{title}' not found in search results: {titles}")

    def verify_only_matching_events_displayed(self, query: str):
        """Verifies that all displayed events contain the query string in their title (case-insensitive)."""
        titles = self.get_event_titles()
        if not titles:
            raise AssertionError("No event cards found in search results")
        for title in titles:
            if query.lower() not in title.lower():
                raise AssertionError(f"Event title '{title}' does not match search query '{query}'")

    def select_sort_option(self, option_name: str):
        """Selects a sorting option from the Sort by dropdown."""
        self.click_sort_by()
        option_locator = self.page.get_by_text(option_name, exact=True).first
        option_locator.wait_for(state="visible", timeout=5000)
        option_locator.click()
        try:
            self.page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass

    def verify_events_sorted_alphabetically_az(self):
        """Verifies that the visible events are sorted alphabetically (A-Z)."""
        titles = self.get_event_titles()
        assert len(titles) > 0, "No events displayed to verify sorting."
        key_fn = lambda s: "".join(c for c in s if c.isalnum()).lower()
        sorted_titles = sorted(titles, key=key_fn)
        assert titles == sorted_titles, f"Events are not sorted A-Z.\nFound: {titles}\nExpected: {sorted_titles}"

    def verify_events_sorted_alphabetically_za(self):
        """Verifies that the visible events are sorted alphabetically (Z-A)."""
        titles = self.get_event_titles()
        assert len(titles) > 0, "No events displayed to verify sorting."
        key_fn = lambda s: "".join(c for c in s if c.isalnum()).lower()
        sorted_titles = sorted(titles, key=key_fn, reverse=True)
        assert titles == sorted_titles, f"Events are not sorted Z-A.\nFound: {titles}\nExpected: {sorted_titles}"

    def click_event_by_title(self, title: str):
        """Clicks on the event card link with the given title to navigate to details."""
        event_link = self.page.locator(f'a[href^="/event/"]:has-text("{title}")').first
        event_link.click()
        self.page.wait_for_url("**/event/*", timeout=10000)

    def verify_event_details(self, title: str, description: str, venue: str, category: str):
        """Verifies details on the Event Details page in the user portal."""
        expect(self.page.locator("h1")).to_contain_text(title, timeout=10000)
        body_text = self.page.locator("body").inner_text()
        assert description in body_text, f"Description '{description}' not found on details page."
        assert venue in body_text, f"Venue '{venue}' not found on details page."
        assert category in body_text, f"Category '{category}' not found on details page."

    def navigate_to_page(self, page_number: int) -> bool:
        """Clicks the specified page number button in pagination if it exists."""
        page_btn = self.page.get_by_role("button", name=str(page_number), exact=True)
        if page_btn.count() > 0 and page_btn.is_visible():
            page_btn.click()
            try:
                self.page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                pass
            return True
        return False

    def verify_event_presence_with_pagination(self, event_title: str, max_pages: int = 3) -> bool:
        """Checks for the event title on the current page, and paginates up to max_pages if not found."""
        for p in range(1, max_pages + 1):
            titles = self.get_event_titles()
            print(f"📄 Page {p} visible event titles: {titles}")
            if event_title in titles:
                print(f"✅ Found event '{event_title}' on page {p}!")
                return True
            
            next_page = p + 1
            if next_page <= max_pages:
                print(f"🔍 Event not found on page {p}. Navigating to page {next_page}...")
                success = self.navigate_to_page(next_page)
                if not success:
                    print(f"⚠️ Pagination button for page {next_page} is not available. Stopping search.")
                    break
            else:
                break
        return False
