import pytest


created_category_name = None
updated_category_name = None


def _open_category_management(dashboard_page):
    dashboard_page.click_category_management()


@pytest.mark.regression
@pytest.mark.order(1)
def test_01_add_category(category_page, dashboard_page, category_data):
    """Create one category with a unique two-letter suffix."""
    global created_category_name

    _open_category_management(dashboard_page)
    created_category_name = category_page.unique_category_name(category_data[0]["name"])

    category_page.add_category(created_category_name)
    category_page.verify_category_created(created_category_name)
    print(f"✅ Category '{created_category_name}' added successfully.")


@pytest.mark.regression
@pytest.mark.order(2)
def test_02_edit_category(category_page, dashboard_page, edit_category_data):
    """Edit the category created by test_01."""
    global updated_category_name

    if not created_category_name:
        pytest.fail("The add-category test must run before the edit-category test.")

    _open_category_management(dashboard_page)
    updated_category_name = category_page.unique_category_name(edit_category_data[0]["new_name"])

    category_page.edit_category(created_category_name, updated_category_name)
    category_page.verify_category_updated(created_category_name, updated_category_name)
    print(f"✅ Category Edit  '{created_category_name}' updated to '{updated_category_name}' successfully.")


@pytest.mark.regression
@pytest.mark.order(3)
def test_03_delete_category(category_page, dashboard_page):
    """Delete the same category updated by test_02."""
    if not updated_category_name:
        pytest.fail("The edit-category test must run before the delete-category test.")

    _open_category_management(dashboard_page)
    category_page.delete_category(updated_category_name)
    category_page.verify_category_deleted(updated_category_name)
    print(f"✅ Category Delete  '{updated_category_name}' deleted successfully.")
