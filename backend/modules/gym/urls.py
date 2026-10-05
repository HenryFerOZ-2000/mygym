from django.urls import path
from .api import PlansView, PlanView
from .membership_api import (
    MembershipsView,
    PreviewView,
    EnrollmentView,
    ChangeView,
    CorrectView,
    CancelView,
)
from modules.receivables.api import ChargesView, PaymentsView, RefundView
from .report_api import ExpiryView, AttendanceReportView, FinancialReportView
from .attendance_api import (
    AttendanceSearchView,
    AttendanceListView,
    AttendancePreviewView,
    AttendanceCreateView,
    AttendanceVoidView,
)

urlpatterns = [
    path("gym/expiries/", ExpiryView.as_view()),
    path("reports/attendance/", AttendanceReportView.as_view()),
    path("reports/financial/", FinancialReportView.as_view()),
    path("attendance/clients/", AttendanceSearchView.as_view()),
    path("attendance/", AttendanceListView.as_view()),
    path("attendance/<str:attendance_id>/void/", AttendanceVoidView.as_view()),
    path(
        "clients/<str:client_id>/attendance/preview/", AttendancePreviewView.as_view()
    ),
    path("clients/<str:client_id>/attendance/", AttendanceCreateView.as_view()),
    path("gym/plans/", PlansView.as_view()),
    path("gym/plans/<str:plan_id>/", PlanView.as_view()),
    path("clients/<str:client_id>/gym/", MembershipsView.as_view()),
    path("clients/<str:client_id>/gym/preview/", PreviewView.as_view()),
    path("clients/<str:client_id>/gym/memberships/", EnrollmentView.as_view()),
    path(
        "clients/<str:client_id>/gym/memberships/<str:membership_id>/freeze/",
        ChangeView.as_view(),
    ),
    path(
        "clients/<str:client_id>/gym/memberships/<str:membership_id>/correct/",
        CorrectView.as_view(),
    ),
    path(
        "clients/<str:client_id>/gym/memberships/<str:membership_id>/cancel/",
        CancelView.as_view(),
    ),
    path("clients/<str:client_id>/receivables/", ChargesView.as_view()),
    path("clients/<str:client_id>/receivables/payments/", PaymentsView.as_view()),
    path(
        "clients/<str:client_id>/receivables/payments/<str:payment_id>/refunds/",
        RefundView.as_view(),
    ),
]
