"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from ersathi import views

from ersathi.views import (
    #AddCommentView,
    CompanyServiceCategoryListView,
    FeaturedCompaniesView,
    GetUserRating,
    PaymentCreateView,
    PaymentListView,
    RequestSafetyTrainingView,
    RevenueAnalyticsView, 
    AppointmentAnalyticsView,
    CompanyDashboardDataView,
    # CheckNewInquiriesView,
    ClientAgreementsView,
    ClientInquiriesView,
    CompanyAgreementsView,
    CompanyAppointmentsView,
    CompanyInquiriesView,
    CompanyOrderListView,
    CreatePaymentIntentView,
    DeleteAppointmentView,
    # GetLastInquiryCheckView,
    # MarkInquiriesCheckedView,
    OrderCreateView,
    OrderListView,
    PlanListView,
    RentVerificationAdminView,
    RentVerificationCreateView,
    RentVerificationListView,
    RentVerificationUserUpdateView,
    SafetyTrainingCompaniesView,
    SubmitCompanyRating,
   
    SubmitInquiryView,
    SubscribeView,
    SubscriptionPaymentIntentView,
    SubscriptionStatusView,
    Test,
    UpdateAgreementView,
    UpdateAppointmentStatusView,
    UpdateAppointmentView,
    UpdateInquiryStatusView,
    UpdateOrderPaymentView,
    UpdateOrderStatusView,
    clear_cart,
    clear_wishlist,
    

    company_info,
    company_info_detail,
    create_company_service,
    dashboard_stats,
    
    delete_company_service,
    delete_project,
    delete_team_member,
    generate_agreement,
   
    get_company_info,
    get_company_projects,
    
    
    get_company_services,
    get_company_services_basic,
    get_company_services_by_id,
    get_company_team_members,
    get_product_by_id,
    get_user_profile,
    permanent_delete_account,
    project_list_create,
    send_training_email,
   
    team_member_list_create,
    
    update_company_service,
    update_project,
    update_team_member,
    user_verification_status,
    
    SignupView,
    LoginView,
    ForgotPasswordView,
    CompanyRegistrationView,
    get_company_registrations,
    approve_company,
    reject_company,
    get_company_details,
    get_services,
    ConfirmEmailView,
    ResetPasswordView,
    change_password,
    get_all_products,
    get_products_by_category,
    get_company_products,
    get_cart,
    add_to_cart,
    remove_from_cart,
    get_wishlist,
    add_to_wishlist,
    remove_from_wishlist,
#     CreateChatChannel,
#     ChatMessageList,
#    ChatChannelList,
#    UserInfoView,
#    DeactivateChatChannel,
#    SendMessage,
#    AdminList,
    AgoraTokenView,
    ChatListView,
    MessageView,
    verify_password,
    
   
)



from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/services/', get_services, name='get_services'),
   
    # Auth
    path('api/signup/', SignupView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('auth/', include('social_django.urls', namespace='social')),
    path('api/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('api/password_reset/<str:token>/', ResetPasswordView.as_view()),

    # Company
    path('company-registration/', CompanyRegistrationView.as_view(), name='company-registration'),
    path('company-registration-list/', get_company_registrations, name='company-registration-list'),
    path('approve-company/<int:pk>/', approve_company, name='approve-company'),
    path('reject-company/<int:pk>/', reject_company, name='reject-company'),
    path('api/confirm-email/<str:token>/', ConfirmEmailView.as_view(), name='confirm-email'),
    path('company-registration/<int:pk>/', get_company_details, name='company-details'),
    #rating
    path('submit-rating/<int:company_id>/', SubmitCompanyRating.as_view(), name='submit-rating'),
    path('user-rating/<int:company_id>/', GetUserRating.as_view(), name='user-rating'),
    #dashboard stat
    path('dashboard-stats/', dashboard_stats, name='dashboard_stats'),
    #company info
    path('company-info/', company_info, name='company-info-list'), #post
    path('company-info/<int:company_id>/', company_info_detail, name='company-info-detail'),  # Handles GET and PUT
    #Company/project]
    path('company-info/<int:company_id>/projects/', project_list_create, name='project-list-create'),
    path('company-info/<int:company_id>/projects/<int:project_id>/', update_project, name='update-project'),  # PUT update project
    path('company-info/<int:company_id>/projects/<int:project_id>/delete/', delete_project, name='delete-project'),  # DELETE project
    #TEAMmember
    path('company-info/<int:company_id>/team/', team_member_list_create, name='team_member_list_create'),
    path('company-info/<int:company_id>/team/<int:member_id>/', update_team_member, name='update_team_member'),
    path('company-info/<int:company_id>/team/<int:member_id>/delete/', delete_team_member, name='delete_team_member'),
        #companysetailsclient side
    path('get-company-info/<int:company_id>/', get_company_info, name='get-company-info'),
    path('get-company-projects/<int:company_id>/', get_company_projects, name='get-company-projects'),
    path('get-company-team-members/<int:company_id>/', get_company_team_members, name='get-company-team-members'),
    path('api/company-services/<int:company_id>/', get_company_services_by_id, name='get_company_services_by_id'),
#
    path('api/submit-inquiry/<int:company_id>/', SubmitInquiryView.as_view(), name='submit-inquiry'),
    path('api/company-inquiries/', CompanyInquiriesView.as_view(), name='company-inquiries'),
    path('api/update-inquiry-status/<int:inquiry_id>/', UpdateInquiryStatusView.as_view(), name='update-inquiry-status'),
    path('company-appointments/', CompanyAppointmentsView.as_view(), name='company-appointments'),
    path('api/payments/', PaymentCreateView.as_view(), name='payment-create'),
    path('api/payments/', PaymentListView.as_view(), name='payment-list'),
    # path('mark-inquiries-checked/', MarkInquiriesCheckedView.as_view(), name='mark-inquiries-checked'),
    # path('check-new-company-inquiries/', CheckNewInquiriesView.as_view(), name='check-new-inquiries'),
    # path('api/get-last-inquiry-check/', GetLastInquiryCheckView.as_view(), name='get-last-inquiry-check'),
    path('appointments/<int:appointment_id>/update-status/', UpdateAppointmentStatusView.as_view(), name='update-appointment-status'),
    path('api/appointments/<int:appointment_id>/update/', UpdateAppointmentView.as_view(), name='update-appointment'),
    path('api/appointments/<int:appointment_id>/delete/', DeleteAppointmentView.as_view(), name='delete-appointment'),
   # path('api/submit-inquiry/<int:company_id>/', SubmitInquiryView.as_view(), name='submit-inquiry'),
   # path('api/company-inquiries/', CompanyInquiriesView.as_view(), name='company-inquiries'),
   #aggrement
   path('generate-agreement/<int:appointment_id>/', generate_agreement, name='generate_agreement'),
#  path('company-agreements/<int:user_id>/', CompanyAgreementsView.as_view(), name='company_agreements'),
   path('company-agreements/', CompanyAgreementsView.as_view(), name='company_agreements'),
   path('client-agreements/', ClientAgreementsView.as_view(), name='client_agreements'),
   path('api/agreements/<int:agreement_id>/update/', UpdateAgreementView.as_view(), name='update_agreement'),
    
    # Services
    path('api/company-services/get/', get_company_services, name='get_company_services'),
    path('api/company-services/create/', create_company_service, name='create_company_service'),
    path('api/company-services/<int:service_id>/update/', update_company_service, name='update_company_service'),
    path('api/company-services/<int:service_id>/delete/', delete_company_service, name='delete_company_service'),
    path('api/company-services/basic/', get_company_services_basic, name='get_company_services_basic'),

    # User
    path('api/user-profile/', get_user_profile, name='user-profile'),
    path('api/change-password/', change_password, name='change_password'),

    # Products
    path('api/products/', get_all_products, name='get_all_products'),
    path('api/products/<str:category>/', get_products_by_category, name='get_products_by_category'),
    path('api/company-products/', get_company_products, name='get_company_products'),
    path('api/products-item/<int:id>/', get_product_by_id, name='get_product_by_id'),

    # Test
    path('api/test/', Test.as_view(), name='create_Test'),
    path('api/test/<int:pk>/', Test.as_view(), name='update_delete_test'),

    # Cart
    path('api/cart/', get_cart, name='get_cart'),
    path('api/cart/add/', add_to_cart, name='add_to_cart'),
    path('api/cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('api/wishlist/', get_wishlist, name='get_wishlist'),
    path('api/wishlist/add/', add_to_wishlist, name='add_to_wishlist'),
    path('api/wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('api/cart/clear/', clear_cart, name='clear_cart'),
    path('api/wishlist/clear/', clear_wishlist, name='clear_wishlist'),
    #order
   
    path('api/stripe/create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    
    # Order endpoints
    path('api/orders/', OrderListView.as_view(), name='order-list'),
    path('api/company/orders/', CompanyOrderListView.as_view(), name='company-order-list'),
    path('api/orders/create/', OrderCreateView.as_view(), name='order-create'),
    path('api/orders/update-payment/', UpdateOrderPaymentView.as_view(), name='order-update-payment'),
    path("api/orders/<int:order_id>/", UpdateOrderStatusView.as_view(), name="update-order-status"),
    # Rent Verification
    path('api/rent-verification/', RentVerificationCreateView.as_view(), name='rent-verification-create'),
    path('api/rent-verification/<int:pk>/', RentVerificationAdminView.as_view(), name='rent-verification-admin'),
    path('api/rent-verification/list/', RentVerificationListView.as_view(), name='rent-verification-list'),
    path('api/rent-verification/user/', user_verification_status, name='rent-verification-user'),
    path('api/rent-verification/user-update/<int:pk>/', RentVerificationUserUpdateView.as_view(), name='rent-verification-user-update'),

    # JWT Token
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    #safetyemail
    path('api/send-training-email/', send_training_email, name='send_training_email'),
    path('api/upload-certificate/<int:inquiry_id>/', views.upload_certificate, name='upload_certificate'),
    path('api/client-inquiries/', ClientInquiriesView.as_view(), name='client-inquiries'),
    # path('api/add-comment/<int:inquiry_id>/', AddCommentView.as_view(), name='add-comment'),
    path('api/add-comment/<int:inquiry_id>/', views.add_comment, name='add-comment'),
    path('api/add-client-comment/<int:inquiry_id>/', views.add_client_comment, name='add-client-comment'),
    path('api/upload-progress-photos/<int:inquiry_id>/', views.upload_progress_photos, name='upload-progress-photos'),
    path('api/upload-inspection-reports/<int:inquiry_id>/', views.upload_inspection_reports, name='upload-inspection-reports'),
    path('api/upload-completion-certificate/<int:inquiry_id>/', views.upload_completion_certificate, name='upload-completion-certificate'),
    path('api/update-construction-progress/<int:inquiry_id>/', views.update_construction_progress, name='update-construction-progress'),
    path('api/update-comment-response/<int:comment_id>/', views.update_comment_response, name='update-comment-response'),
    path('api/update-construction-progress/<int:inquiry_id>/', views.update_construction_progress, name='update-construction-progress'),
    #Admin
    path('api/service-categories/', views.service_categories, name='service_categories'),
    path('api/service-categories/<int:category_id>/', views.update_service_category, name='update_service_category'),
    path('api/service-categories/<int:category_id>/delete/', views.delete_service_category, name='delete_service_category'),
    path('api/services/create/', views.create_service, name='create_service'),
    path('api/services/<int:service_id>/', views.update_service, name='update_service'),
    path('api/services/<int:service_id>/delete/', views.delete_service, name='delete_service'),
    path('api/safety-training-companies/', SafetyTrainingCompaniesView.as_view(), name='safety-training-companies'),
    path('api/request-safety-training/<int:company_id>/', RequestSafetyTrainingView.as_view(), name='request-safety-training'),

    #subscription
    path('api/stripe/subscription-payment-intent/<int:company_id>/', SubscriptionPaymentIntentView.as_view(), name='subscription-payment-intent'),
    path('subscription-status/<int:company_id>/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('api/subscribe/<int:company_id>/', SubscribeView.as_view(), name='subscribe'),
    path('api/plans/', PlanListView.as_view(), name='plan-list'),
    #companydashbooard data
    path('api/company-dashboard-data/', CompanyDashboardDataView.as_view(), name='company-dashboard-data'),
    path('api/revenue-analytics/', RevenueAnalyticsView.as_view(), name='revenue-analytics'),
    path('api/appointment-analytics/', AppointmentAnalyticsView.as_view(), name='appointment-analytics'),
    path('api/subscription-analytics/', views.SubscriptionAnalyticsView.as_view(), name='subscription-analytics'),
    path('api/total-revenue/', views.TotalRevenueView.as_view(), name='total-revenue'),
    path("api/sse/notifications/", views.sse_notifications, name="sse_notifications"),
    path("api/notifications/mark_read/", views.mark_notification_read, name="mark_notification_read"),
    #homepage
    path('api/featured-companies/', FeaturedCompaniesView.as_view(), name='featured-companies'),
    #chat`
    # path('api/chat/create-channel/', CreateChatChannel.as_view(), name='create-chat-channel'),
    # path('api/chat/messages/<str:channel_id>/', ChatMessageList.as_view(), name='chat-messages'),
    # path('api/chat/channels/', ChatChannelList.as_view(), name='chat-channels'),
    # path('api/user-info/', UserInfoView.as_view(), name='user-info'),
    # path('api/chat/send-message/', SendMessage.as_view(), name='send-message'),
    # path('api/chat/deactivate-channel/', DeactivateChatChannel.as_view(), name='deactivate-channel'),
    # #admin
    # path('api/admins/', AdminList.as_view(), name='admin-list'),
    path('chats/', ChatListView.as_view()),
    path('chats/<int:chat_id>/messages/', MessageView.as_view()),
    path('agora-token/', AgoraTokenView.as_view()),
    #forfilter
    path('company-service-category-list/', CompanyServiceCategoryListView.as_view(), name='company-service-category-list'),
    #delete
    path('api/permanent-delete-account/', permanent_delete_account, name='permanent_delete_account'),
    path('api/verify-password/', verify_password, name='verify_password'),


    
]  
# Serve media files during development 
if settings.DEBUG:  
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)