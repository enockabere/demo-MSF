from django.urls import path
from . import views


urlpatterns = [
    path('imprest/requisition', views.ImprestRequisition.as_view(), name='imprestReq'),
    path('FnDeleteImprestLine/<str:pk>',
         views.FnDeleteImprestLine.as_view(), name='FnDeleteImprestLine'),
    path('Impres/<str:pk>', views.FnRequestPaymentApproval.as_view(), name='Impres'),
    path('FnGenerateImprestReport/<str:pk>',
         views.FnGenerateImprestReport.as_view(), name='FnGenerateImprestReport'),
    path('ImpresCancel/<str:pk>', views.FnCancelPaymentApproval.as_view(), name='ImpresCancel'),
    path('Imp/<str:pk>', views.ImprestDetails.as_view(), name='IMPDetails'),
    path('UploadAttachment/<str:pk>',
         views.UploadAttachment.as_view(), name='UploadAttachment'),
    path('DeleteImprestAttachment/<str:pk>',
         views.DeleteImprestAttachment.as_view(), name='DeleteImprestAttachment'),


    path('ImprestSurrender', views.ImprestSurrender.as_view(), name='imprestSurr'),
    path('ImpSurrender/<str:pk>',
         views.SurrenderDetails.as_view(), name='IMPSurrender'),
    path('SurrenderApprove/<str:pk>',
         views.SurrenderApproval.as_view(), name='SurrenderApprove'),
    path('CancelSurrenderApproval/<str:pk>',
         views.FnCancelSurrenderApproval.as_view(), name='CancelSurrenderApproval'),
    path('UploadSurrenderAttachment/<str:pk>',
         views.UploadSurrenderAttachment.as_view(), name='UploadSurrenderAttachment'),
    path('FnGenerateImprestSurrenderReport/<str:pk>',
         views.FnGenerateImprestSurrenderReport.as_view(), name='FnGenerateImprestSurrenderReport'),
    path('DeleteSurrenderAttachment/<str:pk>',
         views.DeleteSurrenderAttachment.as_view(), name='DeleteSurrenderAttachment'),

    path('StaffClaim', views.StaffClaim.as_view(), name='claim'),
    path('Claim/<str:pk>', views.ClaimDetails.as_view(), name='ClaimDetail'),
    path('ClaimApprove/<str:pk>', views.ClaimApproval.as_view(), name='ClaimApprove'),
    path('ClaimCancel/<str:pk>', views.FnCancelClaimApproval.as_view(), name='ClaimCancel'),
    path('FnDeleteStaffClaimLine/<str:pk>', views.FnDeleteStaffClaimLine.as_view(),
         name='FnDeleteStaffClaimLine'),
    path('FnGenerateStaffClaimReport/<str:pk>', views.FnGenerateStaffClaimReport.as_view(),
         name='FnGenerateStaffClaimReport'),
    path('DeleteClaimAttachment/<str:pk>',
         views.DeleteClaimAttachment.as_view(), name='DeleteClaimAttachment'),

]
