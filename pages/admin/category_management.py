import secrets
import string

from playwright.sync_api import Page, expect


class CategoryManagement:

    def __init__(self, page: Page):
        self.page = page
        self.text_category_management = page.get_by_role("heading", name="Category Management")
        self.add_new_btn = page.get_by_test_id("event-category-add-new-btn")
        self.add_category_name = page.get_by_test_id("event-category-create-name-input")
        self.create_save_btn = page.get_by_test_id("event-category-create-save-btn")
        self.edit_category_name = page.get_by_test_id("event-category-edit-name-input")
        self.update_save_btn = page.get_by_test_id("event-category-edit-update-btn")
        self.text_sucesfully_message = page.get_by_text("Category created successfully")
        self.image_upload = page.locator('input[type="file"]')
        self.delete_button = page.get_by_role("button", name="Delete")
        self.place_category=page.get_by_test_id("category-place-tab-btn")


    def get_success_message(self):
        expect(self.text_sucesfully_message).to_be_visible()
        return self.text_sucesfully_message.text_content()
    
    def get_category_row(self, category_name: str):
        return self.page.locator("tbody tr").filter(
            has_text=category_name)

    def unique_category_name(self, base_name: str) -> str:
        """Return a category name with an unused two-letter suffix."""
        for _ in range(676):
            suffix = "".join(secrets.choice(string.ascii_uppercase) for _ in range(2))
            category_name = f"{base_name} {suffix}"
            if self.get_category_row(category_name).count() == 0:
                return category_name

        raise AssertionError("Could not generate an unused two-letter category suffix.")
    
    def enter_category_name(self, text: str):
        self.add_category_name.fill(text)
        
        
    def upload_category_image(self, image_path: str):
        self.image_upload.set_input_files(image_path)

    def add_category(self, categoryname: str):
        self.add_new_btn.click()              # Click Add New first if the form is hidden
        self.enter_category_name(categoryname)
        self.create_save_btn.click()

    def verify_category_created(self, category_name: str):
        row = self.page.locator("tbody tr").filter(has_text=category_name)
        expect(row).to_have_count(1)
    
    def click_action_menu(self, category_name: str):
        row = self.get_category_row(category_name)
        row.locator("button[data-testid$='actions-dropdown']").click()
        
    def edit_category(self, old_name: str, new_name: str):
        self.click_action_menu(old_name)
        self.page.get_by_role("menuitem", name="Edit Category").click()
        self.edit_category_name.click()
        self.edit_category_name.fill(new_name)
        self.update_save_btn.click()
    
    def delete_category(self, category_name: str):
        self.click_action_menu(category_name)
        self.page.get_by_role("menuitem", name="Delete Category").click()
        self.page.get_by_role("button", name="Delete").click()
    
    def verify_category_updated(self, old_name: str, new_name: str):
        expect(self.get_category_row(old_name)).to_have_count(0)
        expect(self.get_category_row(new_name)).to_have_count(1)
    
    def verify_category_deleted(self, category_name: str):
        expect(self.get_category_row(category_name)).to_have_count(0)
        
    def click_place_category(self):
        self.place_category.click()
