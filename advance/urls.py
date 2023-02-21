from django.urls import path

from . import views

urlpatterns = [
    path("salary advance", views.advance.as_view(),name="advance"),
    path("advanceDetail/<str:pk>",views.advanceDetail.as_view(), name="advanceDetail"),
    path("FnRequestSalaryAdvanceApproval/<str:pk>",views.FnRequestSalaryAdvanceApproval.as_view(), name="FnRequestSalaryAdvanceApproval"),
    path("FnCancelSalaryAdvanceApproval/<str:pk>",views.FnCancelSalaryAdvanceApproval.as_view(), name="FnCancelSalaryAdvanceApproval"),
    path("UploadAdvanceAttachment/<str:pk>",views.UploadAdvanceAttachment.as_view(), name="UploadAdvanceAttachment"),
    path("DeleteAdvanceAttachment/<str:pk>",views.DeleteAdvanceAttachment.as_view(), name="DeleteAdvanceAttachment"),
]