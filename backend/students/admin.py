from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
     # Columns shown in the student list page
     list_display = ['student_id', 'full_name', 'year_of_join', 'parent_phone', 'admission_date', 'is_active']
     
     # Filters on the right side
     list_filter = ['is_active', 'status', 'gender', 'year_of_join']
     
     # Search box - can search by these fields
     search_fields = ['student_id', 'first_name', 'last_name', 'parent_name', 'email', 'phone']
     
     # Fields that can't be edited (auto-generated)
     readonly_fields = ['student_id', 'created_at', 'updated_at', 'last_login']
     
     # Organize form into sections
     fieldsets = (
          ('Authentication & Identity', {
               'fields': ('student_id', 'user')
          }),
          ('Student Information', {
               'fields': ('year_of_join', 'admission_date')
          }),
          ('Basic Details', {
               'fields': ('first_name', 'last_name', 'dob', 'gender')
          }),
          ('Contact Information', {
               'fields': ('email', 'phone', 'address', 'city', 'state', 'pincode')
          }),
          ('Parent/Guardian Information', {
               'fields': ('parent_name', 'parent_relationship', 'parent_phone', 'parent_email')
          }),
          ('Emergency Contact', {
               'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'),
               'classes': ('collapse',)  # This section starts collapsed
          }),
          ('Status', {
               'fields': ('is_active', 'status')
          }),
          ('Notification Preferences', {
               'fields': ('email_notifications', 'sms_notifications', 'parent_notifications')
          }),
          ('Timestamps', {
               'fields': ('created_at', 'updated_at', 'last_login'),
               'classes': ('collapse',)  # This section starts collapsed
          }),
     )
    
    # Date hierarchy for easy filtering by date
     date_hierarchy = 'admission_date'
    
    # How many students to show per page
     list_per_page = 50
    
    # Enable bulk actions
     actions = ['mark_as_active', 'mark_as_inactive']
    
    # Custom admin actions
     def mark_as_active(self, request, queryset):
        queryset.update(is_active=True, status='Active')
        self.message_user(request, f"{queryset.count()} students marked as active.")
     mark_as_active.short_description = "Mark selected students as Active"
    
     def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False, status='Inactive')
        self.message_user(request, f"{queryset.count()} students marked as inactive.")
     mark_as_inactive.short_description = "Mark selected students as Inactive"
