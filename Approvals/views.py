from django.shortcuts import render, redirect
from datetime import date
import requests
from requests import Session
from django.conf import settings as config
import datetime as dt
from django.contrib import messages
import io as BytesIO
import base64
from django.http import HttpResponse
from zeep import Client
from zeep.transports import Transport
from requests.auth import HTTPBasicAuth
from django.views import View
from myRequest.views import UserObjectMixins


# Create your views here.
class UserObjectMixin(object):
    model =None
    session = requests.Session()
    session.auth = config.AUTHS
    todays_date = dt.datetime.now().strftime("%b. %d, %Y %A")
    def get_object(self,endpoint):
        response = self.session.get(endpoint, timeout=10).json()
        return response

class Approve(UserObjectMixin,View):
    def get(self,request):
        try:
            userID = request.session['User_ID']

            Access_Point = config.O_DATA.format(f"/QyApprovalEntries?$filter=Approver_ID%20eq%20%27{userID}%27")
            response = self.get_object(Access_Point)

            openLeave = [x for x in response['value'] if (x['Status'] == 'Open' and x['Document_Type']=='LeaveApplication') or (x['Status']=='Open' and x['Document_Type']=='TrainingRequest')]
            approvedLeave = [x for x in response['value'] if (x['Status'] == 'Approved' and x['Document_Type']=='LeaveApplication') or (x['Status']=='Approved' and x['Document_Type']=='TrainingRequest')]
            rejectedLeave = [x for x in response['value'] if (x['Status'] == 'Rejected' and x['Document_Type']=='LeaveApplication') or (x['Status']=='Rejected' and x['Document_Type']=='TrainingRequest')]

            # Imprests
            openImp = [x for x in response['value'] if x['Status'] == 'Open' and x['Document_Type']=='Imprest']
            approvedImp = [x for x in response['value'] if x['Status'] == 'Approved' and x['Document_Type']=='Imprest']
            rejectedImp = [x for x in response['value'] if x['Status'] == 'Rejected' and x['Document_Type']=='Imprest']

            # Surrender
            openSurrender = [x for x in response['value'] if x['Status'] == 'Open' and x['Document_Type']=='Imprest Surrender']
            approveSurrender = [x for x in response['value'] if x['Status'] == 'Approved' and x['Document_Type']=='Imprest Surrender']
            rejectSurrender = [x for x in response['value'] if x['Status'] == 'Rejected' and x['Document_Type']=='Imprest Surrender']

            # Staff Claim
            openClaim = [x for x in response['value'] if x['Status'] == 'Open' and x['Document_Type']=='Staff Claim']
            approveClaim = [x for x in response['value'] if x['Status'] == 'Approved' and x['Document_Type']=='Staff Claim']
            rejectClaim = [x for x in response['value'] if x['Status'] == 'Rejected' and x['Document_Type']=='Staff Claim']

            # Purchase Request
            openPurchase = [x for x in response['value'] if x['Status'] == 'Open' and x['Document_Type']=='Purchase Requisitions']
            approvePurchase = [x for x in response['value'] if x['Status'] == 'Approved' and x['Document_Type']=='Purchase Requisitions']
            rejectPurchase = [x for x in response['value'] if x['Status'] == 'Rejected' and x['Document_Type']=='Purchase Requisitions']

            # Repair Request
            openRepair = [x for x in response['value'] if x['Status'] == 'Open' and x['Document_Type']=='Repair']
            appRepair = [x for x in response['value'] if x['Status'] == 'Approved' and x['Document_Type']=='Repair']
            rejRepair = [x for x in response['value'] if x['Status'] == 'Rejected' and x['Document_Type']=='Repair']

            # Store Request
            openStore = [x for x in response['value'] if x['Status'] == 'Open' and x['Document_Type']=='Store Requisitions']
            appStore = [x for x in response['value'] if x['Status'] == 'Approved' and x['Document_Type']=='Store Requisitions']
            rejStore = [x for x in response['value'] if x['Status'] == 'Rejected' and x['Document_Type']=='Store Requisitions']

            # Other Request
            openOther = [x for x in response['value'] if (x['Status'] == 'Open' and x['Document_Type']=='Payment Voucher') or (x['Status']=='Open' and x['Document_Type']=='Petty Cash') or (x['Status']=='Open' and x['Document_Type']=='Petty Cash Surrender') or (x['Status']=='Open' and x['Document_Type']=='Staff Payroll Approval') or (x['Status']=='Open' and x['Document_Type']=='Invoice') or (x['Status']=='Open' and x['Document_Type']=='Order') or (x['Status']=='Open' and x['Document_Type']=='Payroll Loan Application')]
            appOther = [x for x in response['value'] if (x['Status'] == 'Approved' and x['Document_Type']=='Payment Voucher') or (x['Status']=='Approved' and x['Document_Type']=='Petty Cash') or (x['Status']=='Approved' and x['Document_Type']=='Petty Cash Surrender') or (x['Status']=='Approved' and x['Document_Type']=='Staff Payroll Approval') or (x['Status']=='Approved' and x['Document_Type']=='Invoice') or (x['Status']=='Approved' and x['Document_Type']=='Order') or (x['Status']=='Approved' and x['Document_Type']=='Payroll Loan Application')]
            rejOther = [x for x in response['value'] if (x['Status'] == 'Rejected' and x['Document_Type']=='Payment Voucher') or (x['Status']=='Rejected' and x['Document_Type']=='Petty Cash') or (x['Status']=='Rejected' and x['Document_Type']=='Petty Cash Surrender') or (x['Status']=='Rejected' and x['Document_Type']=='Staff Payroll Approval') or (x['Status']=='Rejected' and x['Document_Type']=='Invoice') or (x['Status']=='Rejected' and x['Document_Type']=='Order') or (x['Status']=='Rejected' and x['Document_Type']=='Payroll Loan Application')]
 
            countIMP = len(openImp)

            countSurrender = len(openSurrender)
            countClaim = len(openClaim)
            countPurchase = len(openPurchase)
            countRepair = len(openRepair)
            countStore = len(openStore)
            countOther = len(openOther)

        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, e)
            return redirect('auth')
        except KeyError as e:
            print (e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth') 

        ctx = {"today": self.todays_date, "imprest": openImp,"full": userID,
            "countIMP": countIMP, "approvedIMP":approvedImp,"rejectedImp":rejectedImp,
            "openLeave":openLeave,"approvedLeave":approvedLeave,
            "rejectedLeave":rejectedLeave,"openSurrender":openSurrender,"countSurrender":countSurrender,"approveSurrender":approveSurrender,"rejectSurrender":rejectSurrender,
            "countClaim":countClaim,"openClaim":openClaim,"approveClaim":approveClaim,"rejectClaim":rejectClaim,
            "countPurchase":countPurchase,"openPurchase":openPurchase,"approvePurchase":approvePurchase,
            "rejectPurchase":rejectPurchase, "countRepair":countRepair,"appRepair":appRepair,"rejRepair":rejRepair,
            "countStore":countStore,"openStore":openStore,"appStore":appStore,"rejStore":rejStore,
            "openOther":openOther,"appOther":appOther,"rejOther":rejOther,"countOther":countOther}
              
        return render(request, 'Approve.html', ctx)


class ApproveDetails(UserObjectMixins, View):
    def get(self, request,pk):
        try:
            userID = request.session['User_ID']
  
            response = self.double_filtered_data("/QyApprovalEntries","Document_No_","eq",pk,"and",
                                            "Approver_ID","eq",userID)
            for approve in response[1]:
                res = approve

            res_file = self.one_filter("/QyDocumentAttachments","No_","eq",pk)
            allFiles = [x for x in res_file[1]]

            ImprestResponse = self.one_filter("/Imprests","No_","eq",pk)
            for imprest in ImprestResponse[1]:
                data = imprest
                state = 1
            ResponseImprestLine = self.one_filter("/QyImprestLines","AuxiliaryIndex1","eq",pk)
            ImprestLine = [x for x in ResponseImprestLine[1] if x['AuxiliaryIndex1'] == pk]

            LeaveResponse = self.one_filter("/QyLeaveApplications","Application_No","eq",pk)
            for leave in LeaveResponse[1]:
                data = leave
                state = 2

            TrainResponse = self.one_filter("/QyTrainingRequests","Request_No_","eq",pk)
            for train in TrainResponse[1]:
                data = train
                state = 3

            TrainLineResponse = self.one_filter("/QyTrainingNeedsRequest","Source_Document_No","eq",pk)
            TrainLine = [x for x in TrainLineResponse[1] if x['Source_Document_No'] == pk]

            SurrenderResponse = self.one_filter("/QyImprestSurrenders","No_","eq",pk)
            for imprest in SurrenderResponse[1]:
                data = imprest
                state = 4

            ResponseSurrenderLines = self.one_filter("/QyImprestSurrenderLines","No","eq",pk)
            SurrenderLines = [x for x in ResponseSurrenderLines[1] if x['No'] == pk]

            ClaimResponse = self.one_filter("/QyStaffClaims","No_","eq",pk)
            for claim in ClaimResponse[1]:
                data = claim
                state = 5
 
            ClaimLineResponse = self.one_filter("/QyStaffClaimLines","No","eq",pk)
            ClaimLines = [x for x in ClaimLineResponse[1] if x['No'] == pk]

            PurchaseResponse = self.one_filter("/QyPurchaseRequisitionHeaders","No_","eq",pk)
            for purchase in PurchaseResponse[1]:
                data = purchase
                state = 6

            PurchaseLineResponse = self.one_filter("/QyPurchaseRequisitionLines","AuxiliaryIndex1","eq",pk)
            PurchaseLines = [x for x in PurchaseLineResponse[1] if x['AuxiliaryIndex1'] == pk]
            
            RepairResponse = self.one_filter("/QyRepairRequisitionHeaders","No_","eq",pk)
            for repair in RepairResponse[1]:
                data = repair
                state = 7

            RepairLineResponse = self.one_filter("/QyRepairRequisitionLines","AuxiliaryIndex1","eq",pk)
            RepairLines = [x for x in RepairLineResponse[1] if x['AuxiliaryIndex1'] == pk]

            StoreResponse = self.one_filter("/QyStoreRequisitionHeaders","No_","eq",pk)
            for store in StoreResponse[1]:
                data = store
                state = 8 

            StoreLineResponse = self.one_filter("/QyStoreRequisitionLines","AuxiliaryIndex1","eq",pk)
            StoreLines =  [x for x in StoreLineResponse[1] if x['AuxiliaryIndex1'] == pk]

            VoucherResponse = self.one_filter("/QyPaymentVoucherHeaders","No_","eq",pk)
            for voucher in VoucherResponse[1]:
                data = voucher
                state = "voucher"

            VoucherLineResponse = self.one_filter("/QyPaymentVoucherLines","No","eq",pk)
            VoucherLines = [x for x in VoucherLineResponse[1] if x['No'] == pk]

            PettyResponse = self.one_filter("/QyPettyCashHeaders","No_","eq",pk)
            for petty in PettyResponse[1]:
                data = petty
                state = "petty cash"
  
            PettyLineResponse = self.one_filter("/QyPettyCashLines","No","eq",pk)
            PettyLines = [x for x in PettyLineResponse[1] if x['No'] == pk]

            PettySurrenderResponse = self.one_filter("/QyPettyCashSurrenderHeaders","No_","eq",pk)
            for pettySurrender in PettySurrenderResponse[1]:
                data = pettySurrender
                state = "petty cash surrender"

            PettySurrenderLineResponse = self.one_filter("/QyPettyCashSurrenderLines","No","eq",pk)
            PettySurrenderLines = [x for x in PettySurrenderLineResponse[1] if x['No'] == pk]

            advanceResponse = self.one_filter("/QySalaryAdvances","Loan_No","eq",pk)
            for advance in advanceResponse[1]:
                data = advance
                state = "advance"               
                
                
        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, e)
            return redirect('approve')
        except KeyError as e:
            messages.info(request, e)
            print(e)
            return redirect('auth')
        except Exception as e:
            messages.info(request,e)
            return redirect('auth')
        ctx = {
            "today": self.todays_date,"full": userID, 
             "res": res,"file":allFiles,"data":data,"state":state,
             "SurrenderLines":SurrenderLines,"ClaimLines":ClaimLines,
             "PurchaseLines":PurchaseLines,"ImpLine":ImprestLine,
             "TrainLine":TrainLine,"RepairLines":RepairLines,
             "StoreLines":StoreLines,"VoucherLines":VoucherLines,
             "PettyLines":PettyLines,"PettySurrenderLines":PettySurrenderLines
        }

        return render(request, 'approveDetails.html', ctx)


def All_Approved(request, pk):
    Username = request.session['User_ID']
    Password = request.session['password']
    entryNo = ''
    approvalComments = ""
    AUTHS = Session()
    AUTHS.auth = HTTPBasicAuth(Username, Password)
    CLIENT = Client(config.BASE_URL, transport=Transport(session=AUTHS))
    if request.method == 'POST':
        try:
            entryNo = int(request.POST.get('entryNo'))
            myUserID = request.session['User_ID']
            myAction = 'approve'
            documentNo = pk
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        try:
            response = CLIENT.service.FnDocumentApproval(
                entryNo, documentNo, myUserID, approvalComments, myAction)
            messages.success(request, "Document Approval successful")
            print(response)
            return redirect('approve')
        except Exception as e:
            print(e)
            messages.info(request, e)
            return redirect('ApproveData', pk=pk)
    return redirect('ApproveData', pk=pk)


def Rejected(request, pk):
    Username = request.session['User_ID']
    Password = request.session['password']
    entryNo = ''
    approvalComments = ""
    AUTHS = Session()
    AUTHS.auth = HTTPBasicAuth(Username, Password)
    CLIENT = Client(config.BASE_URL, transport=Transport(session=AUTHS))
    if request.method == 'POST':
        try:
            entryNo = int(request.POST.get('entryNo'))
            approvalComments = request.POST.get('approvalComments')
            myAction = 'reject'
            documentNo = pk
            userID = request.session['User_ID']
        except ValueError:
            messages.error(request, "Missing Input")
            return redirect('ApproveData', pk=pk)
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        try:
            response = CLIENT.service.FnDocumentApproval(
                entryNo, documentNo, userID, approvalComments, myAction)
            messages.success(request, "Reject Document Approval successful")
            print(response)
            return redirect('approve')
        except Exception as e:
            messages.info(request, e)
            return redirect('ApproveData', pk=pk)
    return redirect('ApproveData', pk=pk)

def viewDocs(request,pk,id):
    if request.method == 'POST':
        docNo = pk
        attachmentID = int(request.POST.get('attachmentID'))
        File_Name = request.POST.get('File_Name')
        File_Extension = request.POST.get('File_Extension')
        tableID = int(id)

        try:
            response = config.CLIENT.service.FnGetDocumentAttachment(
                docNo, attachmentID, tableID)
            file_name = File_Name.split()
            filenameFromApp = file_name[0] + "." + File_Extension
            buffer = BytesIO.BytesIO()
            content = base64.b64decode(response)
            buffer.write(content)
            responses = HttpResponse(
                buffer.getvalue(),
                content_type="application/ms-excel",
            )
            responses['Content-Disposition'] = f'inline;filename={filenameFromApp}'
            return responses
        except Exception as e:
            messages.info(request, e)
            return redirect('auth')
    return redirect('auth')