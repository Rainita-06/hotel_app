from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from app1 import views
from app1 import api as api_views

router = DefaultRouter()
router.register(r"master/users", api_views.MasterUserViewSet, basename="master-users")
router.register(r"master/locations", api_views.MasterLocationViewSet, basename="master-locations")
router.register(r"vouchers", api_views.VoucherViewSet, basename="vouchers")
router.register(r'complaints', api_views.ComplaintViewSet,basename="complaints")
router.register(r'user-groups',api_views.UserGroupViewSet,basename="user-groups")
router.register(r"departments", api_views.DepartmentViewSet, basename="departments")
router.register(r"locations", api_views.LocationViewSet, basename="locations")
router.register(r"users", api_views.UsersViewSet, basename="users")
router.register(r'reviews', api_views.ReviewViewSet,basename="reviews")
router.register(r'buildings', api_views.BuildingViewSet,basename="buildings")
router.register(r'floors', api_views.FloorViewSet,basename="floors")
router.register(r'families', api_views.LocationFamilyViewSet,basename="families")
router.register(r'types', api_views.LocationTypeViewSet,basename="types")
router.register(r'request-types', api_views.RequestTypeViewSet, basename='request-type')
router.register(r'request-families', api_views.RequestFamilyViewSet, basename='request-family')
router.register(r'work-families', api_views.WorkFamilyViewSet, basename='work-family')
router.register(r'workflows', api_views.WorkflowViewSet, basename='workflow')
router.register(r'checklists', api_views.ChecklistViewSet, basename='checklists')
router.register(r'checklist-items', api_views.ChecklistItemViewSet, basename='checklist-items')
urlpatterns = [
    path("admin/", admin.site.urls),

    # HTML pages
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("master-user/", views.master_user, name="master_user"),
      path("upload-avatar/", views.upload_avatar, name="upload_avatar"),
      path('export-users/', views.export_users, name='export_users'),

    path("reports/service/", views.service_report, name="service_report"),
    path("user/add/", views.add_user, name="add_user"),
    path("user/<int:user_id>/edit/", views.edit_user, name="edit_user"),
    path("user/<int:user_id>/copy/", views.copy_user, name="copy_user"),
    path("user/<int:user_id>/delete/", views.delete_user, name="delete_user"),
    path("master-location/", views.master_location, name="master_location"),
    path("dashboard/", views.hotel_dashboard, name="hotel_dashboard"),
    path("breakfast-voucher/", views.breakfast_voucher, name="breakfast_voucher"),
    path("room/<int:voucher_id>/", views.room_detail, name="room_detail"),
    path("departments/", views.department_list, name="department_list"),
    path("departments/add/", views.add_department, name="add_department"),
    path("departments/edit/<int:pk>/", views.edit_department, name="edit_department"),
    path("departments/delete/<int:pk>/", views.delete_department, name="delete_department"),
    path("departments/<int:pk>/details/", api_views.DepartmentDetailAPIView.as_view(), name="department_details"),
#     path("complaints/", views.complaint_list, name="complaint_list"),
#     path("complaints/add/", views.add_complaint, name="add_complaint"),
#     path("complaints/<int:complaint_id>/assign/", views.assign_complaint, name="assign_complaint"),
# path("complaints/<int:complaint_id>/accept/", views.accept_complaint, name="accept_complaint"),
# path("complaints/<int:complaint_id>/complete/", views.complete_complaint, name="complete_complaint"),
path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints/add/', views.add_complaint, name='add_complaint'),
    path('complaints/assign/<int:complaint_id>/', views.assign_complaint, name='assign_complaint'),
    path('complaints/accept/<int:complaint_id>/', views.accept_complaint, name='accept_complaint'),
    path('complaints/complete/<int:complaint_id>/', views.complete_complaint, name='complete_complaint'),

    # Notifications
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path("complaints/edit/<int:complaint_id>/", views.edit_complaint, name="edit_complaint"),
    path("complaints/delete/<int:complaint_id>/", views.delete_complaint, name="delete_complaint"),
    path('departments/delete/<int:pk>/', views.delete_department, name='delete_department'),
    path('user-groups/', views.user_groups, name='user_groups'),
    path('user-groups/add/', views.add_user_group, name='add_user_group'),
    path('user-groups/edit/<int:group_id>/', views.edit_user_group, name='edit_user_group'),
    path('user-groups/delete/<int:group_id>/', views.delete_user_group, name='delete_user_group'),
    path('user-groups/assign/<int:group_id>/', views.assign_users_group, name='assign_users_group'),
    path('locations/', views.locations_list, name='locations_list'),
    path('locations/add/', views.location_form, name='location_add'),
    
     path('location/', views.location_manage_view, name='location_manage'),
    path('locations/add/', views.add_family, name='add_family'),
    # path('locations/search/', views.search_families, name='search_families'),
    path('locations/search/', views.search_locations, name='search_locations'),

    path('locations/edit/<int:location_id>/', views.location_form, name='location_edit'),
    path('locations/delete/<int:location_id>/', views.location_delete, name='location_delete'),
    path('request-types/', views.request_types_list, name='request_types_list'),
     path('family/delete/<int:family_id>/', views.family_delete, name='family_delete'),
      path('type/delete/<int:type_id>/', views.type_delete, name='type_delete'),
       path('floor/delete/<int:floor_id>/', views.floor_delete, name='floor_delete'),
        path('building/delete/<int:building_id>/', views.building_delete, name='building_delete'),
    path("checklists/", views.checklist_list, name="checklist_list"),
    path("families/", views.location_manage_view, name="location_manage_view"),
     path("families/add/", views.family_form, name="family_add"),
    path("families/edit/<int:family_id>/", views.family_form, name="family_edit"),
    path("families/delete/<int:family_id>/", views.family_delete, name="family_delete"),

    # Types
    path("types/", views.types_list, name="types_list"),
    path("types/add/", views.type_form, name="type_add"),
    path("types/edit/<int:type_id>/", views.type_form, name="type_edit"),
    path("types/delete/<int:type_id>/", views.type_delete, name="type_delete"),

    # Floors
    path("floors/", views.floors_list, name="floors_list"),
    # path("floors/add/", views.floor_form, name="floor_add"),
    # path("floors/edit/<int:floor_id>/", views.floor_form, name="floor_edit"),
    # path("floors/delete/<int:floor_id>/", views.floor_delete, name="floor_delete"),
      path("floors/add/", views.floor_form, name="floor_form"),
    path("floors/<int:floor_id>/edit/", views.floor_form, name="floor_form"),
    path("floors/<int:floor_id>/delete/", views.floor_delete, name="floor_delete"),

    # urls.py
path('buildings/cards/', views.building_cards, name='building_cards'),
# path('buildings/<int:pk>/', views.building_detail, name='building_detail'),
path('buildings/<int:pk>/edit/', views.building_edit, name='building_edit'),

    # Buildings
    path("buildings/add/", views.building_form, name="building_add"),
    path("buildings/edit/<int:building_id>/", views.building_form, name="building_edit"),
    path("buildings/delete/<int:building_id>/", views.building_delete, name="building_delete"),
    path("checklists/add/", views.add_checklist, name="add_checklist"),
    path("checklists/edit/<int:checklist_id>/", views.edit_checklist, name="edit_checklist"),
    path("checklists/delete/<int:checklist_id>/", views.delete_checklist, name="delete_checklist"),
    #   path('buildings/<int:building_id>/upload-image/', views.upload_building_image, name='upload_building_image'),
    # urls.py
path('buildings/<int:building_id>/upload-image/', views.upload_building_image, name='upload_building_image'),


    path("checkin/", views.create_voucher_checkin, name="checkin_form"),
    path("scan/gym/", views.scan_gym_page, name="scan_gym_page"),
    path("gym/report/", views.gym_report, name="gym_report"),
    path("data-checker/", views.data_checker, name="data_checker"),


    path("bulk_import_locations/",views.bulk_import_locations,name="bulk_import_locations"),
    path("export_locations_csv/",views.export_locations_csv,name="export_locations_csv"),
     
    path("voucher/<int:voucher_id>/", views.voucher_detail_public, name="voucher_detail_public"),
    path("scan/<str:code>/", views.scan_voucher, name="scan_voucher"),
    
    path("checkout/<int:voucher_id>/",views.mark_checkout, name="checkout"),
     path("service-report/", views.service_report, name="service_report"),
     
    # Scanner API (restaurant staff)
    path("voucher/scan/", views.scan_voucher_api, name="scan_voucher_api"),

    # Reports
    path("reports/redemptions/", views.report_redemptions_per_day, name="report_redemptions"),
    path("reports/skipped/", views.report_skipped_guests, name="report_skipped"),
    path("reports/peaktimes/", views.report_peak_times, name="report_peak_times"),
    path("report/vouchers/", views.breakfast_voucher_report, name="breakfast_voucher_report"),

    path("checklists/<int:checklist_id>/add-item/", views.add_item, name="add_item"),
    path("items/edit/<int:item_id>/", views.edit_item, name="edit_item"),
    path("items/delete/<int:item_id>/", views.delete_item, name="delete_item"),
    path("members/<int:member_id>/edit/", views.edit_member, name="edit_member"),
    path("members/<int:member_id>/delete/", views.delete_member, name="delete_member"),
    path("members/scan/", views.validate_member_qr, name="validate_member_qr"),
    

    
    # Add new request type
    path('request-types/add/', views.request_type_add, name='request_type_add'),

    # Edit existing request type
    path('request-types/edit/<int:request_type_id>/', views.request_type_edit, name='request_type_edit'),
    path("scan/", views.scan_voucher_page, name="scan_voucher"),
    # Delete request type
    path('request-types/delete/<int:request_type_id>/', views.request_type_delete, name='request_type_delete'),
    path("checkout/<int:voucher_id>/", views.mark_checkout, name="checkout"),
    path("complaints/<int:complaint_id>/<str:action>/", views.update_complaint_status, name="update_complaint_status"),

    path("voucher/<str:voucher_code>/", views.voucher_landing, name="voucher_landing"),
    path("members/add/", views.add_member, name="add_member"),
    path("members/", views.member_list, name="member_list"),
    
    # path("members/export/", views.export_members, name="export_members"),
    # path("members/<int:member_id>/edit/", views.edit_member, name="edit_member"),
    # path("members/<int:member_id>/delete/", views.delete_member, name="delete_member"),

    # # Visitors
    # path("visitor/check/", views.visitor_check, name="visitor_check"),
    # path("visitor/register/", views.visitor_register, name="visitor_register"),

    # # Reports
    # path("visits/", views.visit_report, name="visit_report"),
    # path("visits/export/", views.export_visits, name="export_visits"),
    # Custom API endpoints
    path("api/vouchers/checked-in/", api_views.checked_in_customers, name="api_checked_in_customers"),
    path("api/vouchers/visits/", api_views.visits_by_date, name="api_visits_by_date"),
    path("api/vouchers/visits-weekly/", api_views.visits_weekly, name="api_visits_weekly"),
    path("api/vouchers/validate/", views.validate_voucher, name="validate_voucher"),
    path("api/complaint-summary/", views.complaint_summary, name="complaint-summary"),
    # Your REST endpoint (already exists but include for clarity)
    path("api/members/validate/", views.validate_member_qr, name="validate_member_qr"),
    # QR + Room APIs
    path("api/dashboard/qr/", api_views.QRGenerateAPIView.as_view(), name="api_qr_generate"),
    path("api/room/<int:pk>/", api_views.RoomDetailAPIView.as_view(), name="api_room_detail"),
    
    # API (router)
    path("api/", include(router.urls)),
    # Token auth
    path("api/token-auth/", obtain_auth_token, name="api_token_auth"),
]
from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
