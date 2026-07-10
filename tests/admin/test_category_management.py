
def test_add_edit_delete_category_flow(
    login_page,
    category_page,
    dashboard_page,
    category_data,
    edit_category_data,
    delete_category_data,
):
    login_page.sign_in_to_be_visiable()
    login_page.forgot_password_btn_visiable()

    login_page.login("admin.portal@yopmail.com", "Admin1234!")
    login_page.admin_dashboard_visable()

    dashboard_page.click_category_management()

    first_category = category_data[0]
    edit_item = edit_category_data[0]
    delete_item = delete_category_data[0]

    created_name = first_category["name"]
    updated_name = edit_item["new_name"]
    deleted_name = delete_item["name"]

    category_page.add_category(created_name)
    category_page.verify_category_created(created_name)
    print(f"✅ Category '{created_name}' added successfully.")

    category_page.edit_category(created_name, updated_name)
    category_page.verify_category_updated(created_name, updated_name)
    print(f"✅ Category '{created_name}' updated to '{updated_name}' successfully.")

    category_page.delete_category(deleted_name)
    category_page.verify_category_deleted(deleted_name)
    print(f"✅ Category '{deleted_name}' deleted successfully.")