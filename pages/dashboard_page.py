from playwright.sync_api import Page , expect

class DashboardPage:
    
        def __init__(self, page:Page):
                self.page=page
                self.event_repository=page.get_by_role("link", name="Event Repository")
                self.category_managment=page.get_by_role("link", name="Category Management")
                self.place_listing=page.get_by_role("link", name="Place Listing")
                self.analytics= page.get_by_role("link", name="Analytics")
                self.activity_log=page.get_by_role("link", name="Activity log")
                self.text_category_management=page.get_by_role("heading", name="Category Management")
                
                
                
        def click_event_reporsitory(self):
            self.event_repository.click()
            
        def click_category_management(self):
            self.category_managment.click()
            
        def click_place_listing(self):
            self.place_listing.click()
            
        def click_analytics(self):
            self.analytics.click()
        def click_activity_log(self):
            self.activity_log.click()
            
    
                
                