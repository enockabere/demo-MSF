import base64
from ctypes.wintypes import PHKEY
from django.shortcuts import render, redirect
from datetime import  datetime
import requests
from requests import Session
import json
from django.conf import settings as config
import datetime as dt
from django.contrib import messages
import enum
import secrets
from django.http import HttpResponse
import io as BytesIO
import string
from zeep import Client
from zeep.transports import Transport
from requests.auth import HTTPBasicAuth
from django.http import JsonResponse
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

class PurchaseRequisition(UserObjectMixins,View):
    def get(self,request):
        try:
            userID = request.session['User_ID']
            empNo = request.session['Employee_No_']

            response = self.one_filter("/QyPurchaseRequisitionHeaders","Employee_No_","eq",empNo)
            openPurchase = [x for x in response[1] if x['Status'] == 'Open']
            Pending = [x for x in response[1] if x['Status'] == 'Pending Approval']
            Approved = [x for x in response[1] if x['Status'] == 'Released']

        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('auth')
        except KeyError as e:
            print(e)
            messages.info(request, e)
            return redirect('auth')
        

        ctx = {
            "today": self.todays_date, "res": openPurchase,
            "response": Approved,"pending": Pending,
            "full": userID
            }
    
        return render(request, 'purchaseReq.html', ctx)
    def post(self, request):
        if request.method == 'POST':
            try:
                requisitionNo = request.POST.get('requisitionNo')
                myUserId = request.session['User_ID']
                employeeNo = request.session['Employee_No_']
                orderDate = datetime.strptime(
                    request.POST.get('orderDate'), '%Y-%m-%d').date()
                myAction = request.POST.get('myAction')
            
            
                response = self.zeep_client(request).service.FnPurchaseRequisitionHeader(
                    requisitionNo, orderDate, employeeNo, myUserId, myAction)
                if response !=False:
                    messages.success(request,"Success")
                    return redirect('PurchaseDetail', pk=response)
                messages.error(request,response)
                return redirect('PurchaseDetail', pk=response)
            except KeyError:
                messages.info(request, "Session Expired. Please Login")
                return redirect('auth')
            except Exception as e:
                messages.info(request, e)
                print(e)
                return redirect('purchase')
        return redirect('purchase')

class PurchaseRequestDetails(UserObjectMixins,View):
    def get(self, request,pk):
        try:
            Dpt = request.session['Department']
            empNo = request.session['Employee_No_']
            myUserId = request.session['User_ID']

            response = self.double_filtered_data("/QyPurchaseRequisitionHeaders","No_","eq",pk,"and",
                                                    "Employee_No_","eq",empNo)
            for document in response[1]:
                res = document

            res_approver = self.one_filter("/QyApprovalEntries","Document_No_","eq",pk)
            Approvers = [x for x in res_approver[1]]

            Res_Proc = self.one_filter("/QyProcurementPlans","Shortcut_Dimension_2_Code","eq",Dpt)
            planitem = [x for x in Res_Proc[1]]

            itemNo = config.O_DATA.format("/QyItems")
            Res_itemNo = self.get_object(itemNo)
            Items = Res_itemNo['value']

            GL_Acc = config.O_DATA.format("/QyGLAccounts")
            Res_GL = self.get_object(GL_Acc)
            Gl_Accounts = Res_GL['value']

            response_Lines = self.one_filter("/QyPurchaseRequisitionLines","AuxiliaryIndex1","eq",pk)
            openLines = [x for x in response_Lines[1] if x['AuxiliaryIndex1'] == pk]

            res_file = self.one_filter("/QyDocumentAttachments","No_","eq",pk)
            allFiles = [x for x in res_file[1]]

            RejectedResponse = self.one_filter("/QyApprovalCommentLines","Document_No_","eq",pk)
            Comments = [x for x in RejectedResponse[1]]
 
        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('purchase')
        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {
            "today": self.todays_date, "res": res, "line": openLines,
             "Approvers": Approvers,"plans": planitem, "items": Items,
            "gl": Gl_Accounts,"file":allFiles,"Comments":Comments,
            "full":myUserId
            }
        return render(request, 'purchaseDetail.html', ctx)
    def post(self, request,pk):
        if request.method == 'POST':
            try:
                myUserId = request.session['User_ID']
                lineNo = int(request.POST.get('lineNo'))
                procPlanItem = request.POST.get('procPlanItem')
                itemTypes = request.POST.get('itemTypes')
                itemNo = request.POST.get('itemNo')
                specification = request.POST.get('specification')
                quantity = int(request.POST.get('quantity'))
                Unit_of_Measure = request.POST.get('Unit_of_Measure')
                myAction = request.POST.get('myAction')

                class Data(enum.Enum):
                    values = itemTypes
                itemType = (Data.values).value

                if not procPlanItem:
                    procPlanItem = ""
                if not Unit_of_Measure:
                    Unit_of_Measure = ''
                response = self.zeep_client(request).service.FnPurchaseRequisitionLine(
                    pk, lineNo, procPlanItem, itemType, itemNo, specification,
                     quantity, myUserId, myAction,Unit_of_Measure)
                if response == True:
                    messages.success(request, "Success")
                    return redirect('PurchaseDetail', pk=pk)
                messages.error(request, "Failed")
                return redirect('PurchaseDetail', pk=pk)

            except KeyError:
                messages.info(request, "Session Expired. Please Login")
                return redirect('auth')
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('PurchaseDetail', pk=pk)
        return redirect('PurchaseDetail', pk=pk)

def RequisitionCategory(request):
    session = requests.Session()
    session.auth = config.AUTHS
    Item = config.O_DATA.format("/QyItems")
    GL_Acc = config.O_DATA.format("/QyGLAccounts")
    Assets = config.O_DATA.format("/QyFixedAssets")
    text = request.GET.get('ItemCode')
    try:
        if text == '1':
            Res_GL = session.get(GL_Acc, timeout=10).json()
            return JsonResponse(Res_GL)
        if text == '2':
            Item_res = session.get(Item, timeout=10).json()
            return JsonResponse(Item_res)
        if text == '3':
            Asset_res = session.get(Assets, timeout=10).json()
            return JsonResponse(Asset_res)
    except  Exception as e:
        print(e)
    return redirect('purchase') 


class  PurchaseApproval(UserObjectMixins, View):
    def post(self, request,pk):
        if request.method == 'POST':
            try:
                requistionNo = request.POST.get('requistionNo')
                myUserID = request.session['User_ID']

                response = self.zeep_client(request).service.FnRequestInternalRequestApproval(
                    myUserID, requistionNo)
                if response == True:
                    messages.success(request, "Approval Request Sent Successfully")
                    return redirect('PurchaseDetail', pk=pk)
                messages.error(request, response)
                return redirect('PurchaseDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('PurchaseDetail', pk=pk)
        return redirect('PurchaseDetail', pk=pk)


class UploadPurchaseAttachment(UserObjectMixins, View):
    def post(self, request,pk):
        if request.method == "POST":
            try:
                tableID = 52177432
                attach = request.FILES.getlist('attachment')

                for files in attach:
                    fileName = request.FILES['attachment'].name
                    attachment = base64.b64encode(files.read())
                    response = self.zeep_client(request).service.FnUploadAttachedDocument(
                            pk, fileName, attachment, tableID,request.session['User_ID'])

                if response == True:
                    messages.success(request, "File(s) Uploaded Successfully")
                    return redirect('PurchaseDetail', pk=pk)
                messages.error(request, "Failed, try Again")
                return redirect('PurchaseDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('PurchaseDetail', pk=pk)

class DeletePurchaseAttachment(UserObjectMixins,View):
    def post (self,request,pk):
        if request.method == "POST":
            try:
                docID = int(request.POST.get('docID'))
                tableID= int(request.POST.get('tableID'))
                response = self.zeep_client(request).service.FnDeleteDocumentAttachment(
                    pk,docID,tableID)
                if response == True:
                    messages.success(request, "Deleted Successfully")
                    return redirect('PurchaseDetail', pk=pk)
                messages.success(request, "Deleted Successfully ")
                return redirect('PurchaseDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('PurchaseDetail', pk=pk)


class FnCancelPurchaseApproval(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                requistionNo = request.POST.get('requistionNo')
                response = self.zeep_client(request).service.FnCancelInternalRequestApproval(
                    request.session['User_ID'], requistionNo)
                if response == True:
                    messages.success(request, "Cancel Approval Successful")
                    return redirect('PurchaseDetail', pk=pk)
                messages.error(request, response)
                return redirect('PurchaseDetail', pk=pk)
            except KeyError:
                messages.info(request, "Session Expired. Please Login")
                return redirect('auth')
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('PurchaseDetail', pk=pk)
        return redirect('PurchaseDetail', pk=pk)

class FnGeneratePurchaseReport(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            nameChars = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                            for i in range(5))
            filenameFromApp = pk + str(nameChars) + ".pdf"
            try:
                response = self.zeep_client(request).service.FnGenerateRequisitionReport(
                    pk, filenameFromApp)
                buffer = BytesIO.BytesIO()
                content = base64.b64decode(response)
                buffer.write(content)
                responses = HttpResponse(
                    buffer.getvalue(),
                    content_type="application/pdf",
                )
                responses['Content-Disposition'] = f'inline;filename={filenameFromApp}'
                return responses
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('PurchaseDetail', pk=pk)
        return redirect('PurchaseDetail', pk=pk)


class FnDeletePurchaseRequisitionLine(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                lineNo = int(request.POST.get('lineNo'))
                response = self.zeep_client(request).service.FnDeletePurchaseRequisitionLine(
                    pk, lineNo)
                if response == True:
                    messages.success(request, "Successfully Deleted")
                    return redirect('PurchaseDetail', pk=pk)
                messages.error(request, response)
                return redirect('PurchaseDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('PurchaseDetail', pk=pk)
        return redirect('PurchaseDetail', pk=pk)


class RepairRequest(UserObjectMixins,View):
    def get(self, request):
        try:
            userID = request.session['User_ID']

            response = self.one_filter("/QyRepairRequisitionHeaders","Requested_By","eq",userID)
            openRepair = [x for x in response[1] if x['Status'] == 'Open']
            Pending = [x for x in response[1] if x['Status'] == 'Pending Approval']
            Approved = [x for x in response[1] if x['Status'] == 'Released']

        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('auth')
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {"today": self.todays_date, "res": openRepair, "response": Approved,
            "full": userID,"pending": Pending}
        
        return render(request, 'repairReq.html', ctx)
    def post(self, request):
        if request.method == 'POST':
            try:
                employeeNo = request.session['Employee_No_']
                myUserId = request.session['User_ID']
                requisitionNo = request.POST.get('requisitionNo')
                orderDate = datetime.strptime(
                    request.POST.get('orderDate'), '%Y-%m-%d').date()
                reason = request.POST.get('reason')
                myAction = request.POST.get('myAction')

                response = self.zeep_client(request).service.FnRepairRequisitionHeader(
                    requisitionNo, orderDate, employeeNo, reason, myUserId, myAction)
                if response !=False:
                    messages.success(request, "Success")
                    return redirect('RepairDetail', pk=response)
                messages.error(request, response)
                return redirect('repair')
            except KeyError:
                messages.info(request, "Session Expired. Please Login")
                return redirect('auth')
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('repair')
        return redirect('repair')

class RepairRequestDetails(UserObjectMixin,View):
    def get(self, request,pk):
        try:
            empNo = request.session['Employee_No_']
            userID = request.session['User_ID']

            Access_Point = config.O_DATA.format(f"/QyRepairRequisitionHeaders?$filter=No_%20eq%20%27{pk}%27%20and%20Requested_By%20eq%20%27{userID}%27")
            response = self.get_object(Access_Point)
            for document in response['value']:
                res = document

            Assets = config.O_DATA.format(f"/QyFixedAssets?$filter=Responsible_Employee%20eq%20%27{empNo}%27")
            Assest_res = self.get_object(Assets)
            my_asset = [x for x in Assest_res['value']]

            Approver = config.O_DATA.format(f"/QyApprovalEntries?$filter=Document_No_%20eq%20%27{pk}%27")
            res_approver = self.get_object(Approver)
            Approvers = [x for x in res_approver['value']]

            Lines_Res = config.O_DATA.format(f"/QyRepairRequisitionLines?$filter=AuxiliaryIndex1%20eq%20%27{pk}%27")
            response_Lines = self.get_object(Lines_Res)
            openLines = [x for x in response_Lines['value'] if x['AuxiliaryIndex1'] == pk]

            Access_File = config.O_DATA.format(f"/QyDocumentAttachments?$filter=No_%20eq%20%27{pk}%27")
            res_file = self.get_object(Access_File)
            allFiles = [x for x in res_file['value']]

            RejectComments = config.O_DATA.format(f"/QyApprovalCommentLines?$filter=Document_No_%20eq%20%27{pk}%27")
            RejectedResponse = self.get_object(RejectComments)
            Comments = [x for x in RejectedResponse['value']]

        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('repair')
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        ctx = {"res": res,"line": openLines,"Approvers": Approvers,
            "file":allFiles,"Comments":Comments}
        return render(request, 'repairDetail.html', ctx)
    def post(self, request,pk):
        if request.method == 'POST':
            try:
                lineNo = int(request.POST.get('lineNo'))
                assetCode = request.POST.get('assetCode')
                OtherAsset = request.POST.get('OtherAsset')
                description = request.POST.get('description')
                attach = request.FILES.getlist('attachment')
                myAction = request.POST.get('myAction')
                tableID = 52177433
            except ValueError:
                messages.error(request, "Missing Input")
                return redirect('RepairDetail', pk=pk)

            if not OtherAsset:
                OtherAsset = ''
            try:
                response = config.CLIENT.service.FnRepairRequisitionLine(
                    pk, lineNo, assetCode, description, myAction,OtherAsset)
                print(response)
                if response !=0 and not attach:
                    messages.success(request, "Request Successful")
                    return redirect('RepairDetail', pk=pk)
                if attach and response != 0:
                    for files in attach:
                        fileName = request.FILES['attachment'].name
                        attachment = base64.b64encode(files.read())
                        try:
                            responses = config.CLIENT.service.FnUploadAttachedDocument(
                                pk +'#'+str(response), fileName, attachment, tableID,request.session['User_ID'])
                            if responses == True:
                                messages.success(request, "Request Successful")
                                return redirect('RepairDetail', pk=pk)
                            else:
                                messages.error(request, "Failed, Try Again")
                                return redirect('RepairDetail', pk=pk)
                        except Exception as e:
                            messages.error(request, e)
                            print(e)
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('RepairDetail', pk=pk)
        return redirect('RepairDetail', pk=pk)


def RepairApproval(request, pk):
    Username = request.session['User_ID']
    Password = request.session['password']
    AUTHS = Session()
    AUTHS.auth = HTTPBasicAuth(Username, Password)
    CLIENT = Client(config.BASE_URL, transport=Transport(session=AUTHS))
    requistionNo = ""
    if request.method == 'POST':
        try:
            requistionNo = request.POST.get('requistionNo')
            myUserID = request.session['User_ID']
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        try:
            response = CLIENT.service.FnRequestInternalRequestApproval(
                myUserID, requistionNo)
            messages.success(request, "Approval Request Sent Successfully")
            print(response)
            return redirect('RepairDetail', pk=pk)
        except Exception as e:
            messages.info(request, e)
            print(e)
            return redirect('RepairDetail', pk=pk)
    return redirect('RepairDetail', pk=pk)

def FnCancelRepairApproval(request, pk):
    requistionNo = ""
    if request.method == 'POST':
        try:
            myUserID = request.session['User_ID']
            requistionNo = request.POST.get('requistionNo')
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        try:
            response = config.CLIENT.service.FnCancelInternalRequestApproval(
                myUserID, requistionNo)
            messages.success(request, "Cancel Approval Successful")
            print(response)
            return redirect('RepairDetail', pk=pk)
        except Exception as e:
            messages.info(request, e)
            print(e)
            return redirect('RepairDetail', pk=pk)
    return redirect('RepairDetail', pk=pk)

def DeleteRepairAttachment(request,pk):
    if request.method == "POST":
        docID = int(request.POST.get('docID'))
        tableID= int(request.POST.get('tableID'))
        try:
            response = config.CLIENT.service.FnDeleteDocumentAttachment(
                pk,docID,tableID)
            print(response)
            if response == True:
                messages.success(request, "Deleted Successfully ")
                return redirect('RepairDetail', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
    return redirect('RepairDetail', pk=pk)


def FnDeleteRepairRequisitionLine(request, pk):
    lineNo = ""
    if request.method == 'POST':
        lineNo = int(request.POST.get('lineNo'))
        try:
            response = config.CLIENT.service.FnDeleteRepairRequisitionLine(
                pk, lineNo)
            messages.success(request, "Successfully Deleted")
            print(response)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('RepairDetail', pk=pk)
    return redirect('RepairDetail', pk=pk)

def FnGenerateRepairReport(request, pk):
    nameChars = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                        for i in range(5))
    if request.method == 'POST':
        filenameFromApp = pk + str(nameChars) + ".pdf"
        try:
            response = config.CLIENT.service.FnGenerateRepairReport(
                pk, filenameFromApp)
            buffer = BytesIO.BytesIO()
            content = base64.b64decode(response)
            buffer.write(content)
            responses = HttpResponse(
                buffer.getvalue(),
                content_type="application/pdf",
            )
            responses['Content-Disposition'] = f'inline;filename={filenameFromApp}'
            return responses
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('RepairDetail', pk=pk)
    return redirect('RepairDetail', pk=pk)

class StoreRequest(UserObjectMixin,View):
    def get(self, request):
        try:
            userID = request.session['User_ID']

            Access_Point = config.O_DATA.format(f"/QyStoreRequisitionHeaders?$filter=Requested_By%20eq%20%27{userID}%27")
            response = self.get_object(Access_Point)
            openStore = [x for x in response['value'] if x['Status'] == 'Open']
            Pending = [x for x in response['value'] if x['Status'] == 'Pending Approval']
            Approved = [x for x in response['value'] if x['Status'] == 'Released']

            counts = len(openStore)
            counter = len(Approved)
            pend = len(Pending)

        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('auth')
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {"today": self.todays_date, "res": openStore,
            "count": counts, "response": Approved,
            "counter": counter,"pend": pend, "pending": Pending,
            "full": userID}
        return render(request, 'storeReq.html', ctx)
    def post(self, request):
        if request.method == 'POST':
            try:
                requisitionNo = request.POST.get('requisitionNo')
                reason = request.POST.get('reason')
                myAction = request.POST.get('myAction')
                myUserId = request.session['User_ID']
                employeeNo = request.session['Employee_No_']
            except ValueError:
                messages.error(request, "Missing Input")
                return redirect('store')
            except KeyError:
                messages.info(request, "Session Expired. Please Login")
                return redirect('auth')
            try:
                response = config.CLIENT.service.FnStoreRequisitionHeader(
                    requisitionNo, employeeNo, reason, myUserId, myAction)
                if response !='0':
                    messages.success(request, "Success")
                    return redirect('StoreDetail', pk=response)
                messages.error(request, "Failed")
                return redirect('store')
            except Exception as e:
                print(e)
                messages.info(request, e)
                return redirect('store')
        return redirect('store')

class StoreRequestDetails(UserObjectMixin, View):
    def get(self, request,pk):
        try:
            userID = request.session['User_ID']
            
            Access_Point = config.O_DATA.format(f"/QyStoreRequisitionHeaders?$filter=No_%20eq%20%27{pk}%27%20and%20Requested_By%20eq%20%27{userID}%27")
            response = self.get_object(Access_Point)
            for document in response['value']:
                res = document

            ItemCategory = config.O_DATA.format("/QyItemCategories")
            Item_Cat = self.get_object(ItemCategory)
            itemsCategory = Item_Cat['value']

            Location = config.O_DATA.format("/QyLocations")
            Loc_res = self.get_object(Location)
            Location = Loc_res['value']

            Approver = config.O_DATA.format(f"/QyApprovalEntries?$filter=Document_No_%20eq%20%27{pk}%27")
            res_approver = self.get_object(Approver)
            Approvers = [x for x in res_approver['value']]

            Lines_Res = config.O_DATA.format(f"/QyStoreRequisitionLines?$filter=AuxiliaryIndex1%20%20eq%20%27{pk}%27")
            response_Lines = self.get_object(Lines_Res)
            openLines = [x for x in response_Lines['value'] if x['AuxiliaryIndex1'] == pk]

            Access_File = config.O_DATA.format(f"/QyDocumentAttachments?$filter=No_%20eq%20%27{pk}%27")
            res_file = self.get_object(Access_File)
            allFiles = [x for x in res_file['value']]

            RejectComments = config.O_DATA.format(f"/QyApprovalCommentLines?$filter=Document_No_%20eq%20%27{pk}%27")
            RejectedResponse = self.get_object(RejectComments)
            Comments = [x for x in RejectedResponse['value']]

        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('auth')
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {"today": self.todays_date, "res": res,"line": openLines,
            "Approvers": Approvers, "loc": Location,"full": userID,
            "itemsCategory": itemsCategory,"file":allFiles,
            "Comments":Comments}
        return render(request, 'storeDetail.html', ctx)
    def post(self, request,pk):
        if request.method == 'POST':
            try:
                requisitionNo = pk
                lineNo = int(request.POST.get('lineNo'))
                itemCode = request.POST.get('itemCode')
                quantity = int(request.POST.get('quantity'))
                myAction = request.POST.get('myAction')
                Unit_of_Measure = request.POST.get('Unit_of_Measure')
            except ValueError:
                messages.error(request, "Missing Input")
                return redirect('StoreDetail', pk=pk)
            if not Unit_of_Measure:
                Unit_of_Measure = ''
            try:
                response = config.CLIENT.service.FnStoreRequisitionLine(
                    requisitionNo, lineNo, itemCode, quantity, myAction,Unit_of_Measure)
                messages.success(request, "Request Successful")
                print(response)
                return redirect('StoreDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('StoreDetail', pk=pk)
        return redirect('StoreDetail', pk=pk)



def itemCategory(request):
    session = requests.Session()
    session.auth = config.AUTHS
    Item = config.O_DATA.format("/QyItems")
    text = request.GET.get('ItemCode')
    try:
        Item_res = session.get(Item, timeout=10).json()
        return JsonResponse(Item_res)

    except  Exception as e:
        pass
    return redirect('store')

def itemUnitOfMeasure(request):
    session = requests.Session()
    session.auth = config.AUTHS
    Item = config.O_DATA.format("/QyItemUnitOfMeasure")
    text = request.GET.get('ItemNumber')
    try:
        Item_res = session.get(Item, timeout=10).json()
        print(Item_res)
        return JsonResponse(Item_res)

    except  Exception as e:
        pass
    return redirect('dashboard')

def StoreApproval(request, pk):
    Username = request.session['User_ID']
    Password = request.session['password']
    AUTHS = Session()
    AUTHS.auth = HTTPBasicAuth(Username, Password)
    CLIENT = Client(config.BASE_URL, transport=Transport(session=AUTHS))
    requistionNo = ""
    if request.method == 'POST':
        try:
            requistionNo = request.POST.get('requistionNo')
            myUserID = request.session['User_ID']
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        try:
            response = CLIENT.service.FnRequestInternalRequestApproval(
                myUserID, requistionNo)
            messages.success(request, "Approval Request Sent Successfully")
            print(response)
            return redirect('StoreDetail', pk=pk)
        except Exception as e:
            messages.info(request, e)
            print(e)
            return redirect('StoreDetail', pk=pk)
    return redirect('StoreDetail', pk=pk)


def FnCancelStoreApproval(request, pk):
    requistionNo = ""
    if request.method == 'POST':
        try:
            requistionNo = request.POST.get('requistionNo')
            myUserID = request.session['User_ID']
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        try:
            response = config.CLIENT.service.FnCancelInternalRequestApproval(
                myUserID, requistionNo)
            messages.success(request, "Cancel Approval Successful")
            print(response)
            return redirect('StoreDetail', pk=pk)
        except Exception as e:
            messages.info(request, e)
            print(e)
            return redirect('StoreDetail', pk=pk)
    return redirect('StoreDetail', pk=pk)

def FnDeleteStoreRequisitionLine(request, pk):
    lineNo = ""
    if request.method == 'POST':
        lineNo = int(request.POST.get('lineNo'))
        requisitionNo = pk
        try:
            response = config.CLIENT.service.FnDeleteStoreRequisitionLine(
                requisitionNo, lineNo)
            messages.success(request, "Successfully Deleted")
            print(response)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('StoreDetail', pk=pk)
    return redirect('StoreDetail', pk=pk)


def FnGenerateStoreReport(request, pk):
    nameChars = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                        for i in range(5))
    filenameFromApp = ''
    if request.method == 'POST':
        try:
            filenameFromApp = pk + str(nameChars) + ".pdf"
            response = config.CLIENT.service.FnGenerateStoreReport(
                pk, filenameFromApp)
            buffer = BytesIO.BytesIO()
            content = base64.b64decode(response)
            buffer.write(content)
            responses = HttpResponse(
                buffer.getvalue(),
                content_type="application/pdf",
            )
            responses['Content-Disposition'] = f'inline;filename={filenameFromApp}'
            return responses
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('StoreDetail', pk=pk)
    return redirect('StoreDetail', pk=pk)

def UploadStoreAttachment(request, pk):
    response = ""
    fileName = ""
    attachment = ""
    
    if request.method == "POST":
        try:
            attach = request.FILES.getlist('attachment')
            tableID = 52177432
        except Exception as e:
            return redirect('StoreDetail', pk=pk)
        for files in attach:
            fileName = request.FILES['attachment'].name
            attachment = base64.b64encode(files.read())
            try:
                response = config.CLIENT.service.FnUploadAttachedDocument(
                    pk, fileName, attachment, tableID,request.session['User_ID'])
            except Exception as e:
                messages.error(request, e)
                print(e)
        if response == True:
            messages.success(request, "File(s) Uploaded Successfully")
            return redirect('StoreDetail', pk=pk)
        else:
            messages.error(request, "Failed, Try Again.")
            return redirect('StoreDetail', pk=pk)
    return redirect('StoreDetail', pk=pk)

def DeleteStoreAttachment(request,pk):
    if request.method == "POST":
        docID = int(request.POST.get('docID'))
        tableID= int(request.POST.get('tableID'))
        try:
            response = config.CLIENT.service.FnDeleteDocumentAttachment(
                pk,docID,tableID)
            print(response)
            if response == True:
                messages.success(request, "Deleted Successfully ")
                return redirect('StoreDetail', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
    return redirect('StoreDetail', pk=pk)

class GeneralRequisition(UserObjectMixins,View):
    def get(self, request):
        try:
            userID = request.session['User_ID']

            response = self.one_filter("/QyGeneralRequisitionHeaders","Requested_By","eq",userID)
            openRequest = [x for x in response[1] if x['Status'] == 'Open']
            Pending = [x for x in response[1] if x['Status'] == 'Pending Approval']
            Approved = [x for x in response[1] if x['Status'] == 'Released']

            counts = len(openRequest)
            counter = len(Approved)
            pend = len(Pending)

        except requests.exceptions.RequestException as e:
            print(e)
            messages.error(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('auth')
        except KeyError as e:
            print(e)
            messages.info(request, e)
            return redirect('auth')
        

        ctx = {
            "today": self.todays_date, "res": openRequest,
            "count": counts, "response": Approved,
            "counter": counter, "pend": pend,
            "pending": Pending,
            "full": userID
            }
        return render(request,"generalReq.html",ctx)
    def post(self,request):
        if request.method == 'POST':
            try:
                requisitionNo = request.POST.get('requisitionNo')
                myUserId = request.session['User_ID']
                orderDate = datetime.strptime(
                    request.POST.get('orderDate'), '%Y-%m-%d').date()
                reason = request.POST.get('reason')
                myAction = request.POST.get('myAction')
            
                response = config.CLIENT.service.FnGeneralRequisitionHeader(
                    requisitionNo, orderDate, reason, myUserId, myAction)
                if response != "0":
                    messages.success(request, "Request Successful")
                    return redirect('GeneralRequisition')
                messages.success(request, "False")
                return redirect('GeneralRequisition')
            except KeyError:
                messages.info(request, "Session Expired. Please Login")
                return redirect('auth')
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('GeneralRequisition')
        return redirect('GeneralRequisition')

class GeneralRequisitionDetails(UserObjectMixin,View):
    def get(self, request,pk):
        try:
            userID = request.session['User_ID']

            Access_Point = config.O_DATA.format(f"/QyGeneralRequisitionHeaders?$filter=No_%20eq%20%27{pk}%27%20and%20Requested_By%20eq%20%27{userID}%27")
            response = self.get_object(Access_Point)
            for document in response['value']:
                res = document
            
            ItemCategory = config.O_DATA.format("/QyItemCategories")
            Item_Cat = self.get_object(ItemCategory)
            itemsCategory = Item_Cat['value']

            Approver = config.O_DATA.format(f"/QyApprovalEntries?$filter=Document_No_%20eq%20%27{pk}%27")
            res_approver = self.get_object(Approver)
            Approvers = [x for x in res_approver['value']]


            Access_File = config.O_DATA.format(f"/QyDocumentAttachments?$filter=No_%20eq%20%27{pk}%27")
            res_file = self.get_object(Access_File)
            allFiles = [x for x in res_file['value']]

            RejectComments = config.O_DATA.format(f"/QyApprovalCommentLines?$filter=Document_No_%20eq%20%27{pk}%27")
            RejectedResponse = self.get_object(RejectComments)
            Comments = [x for x in RejectedResponse['value']]

            Lines_Res = config.O_DATA.format(f"/QyGeneralRequisitionLines?$filter=AuxiliaryIndex1%20eq%20%27{pk}%27")
            response_Lines = self.get_object(Lines_Res)
            openLines = [x for x in response_Lines['value'] if x['AuxiliaryIndex1'] == pk]
 
        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('purchase')
        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {
            "today": self.todays_date, "res": res,"Approvers": Approvers,
            "file":allFiles,"Comments":Comments,"full":userID,
               "itemsCategory":itemsCategory,"openLines":openLines}
        return render(request,"generalDetails.html",ctx)
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                requisitionNo = pk
                lineNo = int(request.POST.get('lineNo'))
                itemTypes = request.POST.get('itemTypes')
                itemNo = request.POST.get('itemNo')
                specification = request.POST.get('specification')
                quantity = int(request.POST.get('quantity'))
                myUserId = request.session['User_ID']
                myAction = request.POST.get('myAction')
                Unit_of_Measure = request.POST.get('Unit_of_Measure')
            except ValueError:
                messages.error(request, "Missing Input")
                return redirect('GeneralRequisitionDetails', pk=pk)

            class Data(enum.Enum):
                values = itemTypes
            itemType = (Data.values).value

            if not Unit_of_Measure:
                Unit_of_Measure = ''
            try:
                response = config.CLIENT.service.FnGeneralRequisitionLine(
                    requisitionNo, lineNo,itemType,itemNo,specification, quantity,myUserId, myAction,Unit_of_Measure)
                print(response)
                if response == True:
                    messages.success(request, "Request Successful")
                    return redirect('GeneralRequisitionDetails', pk=pk)
                else:
                    messages.error(request, "Not Sent")
                    return redirect('GeneralRequisitionDetails', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('GeneralRequisitionDetails', pk=pk)
        return redirect('GeneralRequisitionDetails', pk=pk)

def FnDeleteGeneralRequisitionLine(request, pk):
    if request.method == 'POST':
        try:
            lineNo = int(request.POST.get('lineNo'))
            requisitionNo = pk
        
            response = config.CLIENT.service.FnDeleteGeneralRequisitionLine(
                requisitionNo, lineNo)

            if response == True:
                messages.success(request, "Successfully Deleted")
                return redirect('GeneralRequisitionDetails', pk=pk)

            messages.error(request, "Not Sent")
            return redirect('GeneralRequisitionDetails', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('GeneralRequisitionDetails', pk=pk)
    return redirect('GeneralRequisitionDetails', pk=pk)

def UploadGeneralAttachment(request, pk):   
    if request.method == "POST":
        try:
            attach = request.FILES.getlist('attachment')
            tableID = 52177432
        except Exception as e:
            return redirect('GeneralRequisitionDetails', pk=pk)
        for files in attach:
            fileName = request.FILES['attachment'].name
            attachment = base64.b64encode(files.read())
            try:
                response = config.CLIENT.service.FnUploadAttachedDocument(
                    pk, fileName, attachment, tableID,request.session['User_ID'])
                if response == True:
                    messages.success(request, "File(s) Uploaded Successfully")
                    return redirect('GeneralRequisitionDetails', pk=pk)
                else:
                    messages.error(request, "Failed, Try Again.")
                    return redirect('GeneralRequisitionDetails', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
    return redirect('GeneralRequisitionDetails', pk=pk)

def DeleteGeneralAttachment(request,pk):
    if request.method == "POST":
        docID = int(request.POST.get('docID'))
        tableID= int(request.POST.get('tableID'))
        try:
            response = config.CLIENT.service.FnDeleteDocumentAttachment(
                pk,docID,tableID)
            print(response)
            if response == True:
                messages.success(request, "Deleted Successfully ")
                return redirect('GeneralRequisitionDetails', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
    return redirect('GeneralRequisitionDetails', pk=pk)

def GeneralApproval(request, pk):
    Username = request.session['User_ID']
    Password = request.session['password']
    AUTHS = Session()
    AUTHS.auth = HTTPBasicAuth(Username, Password)
    CLIENT = Client(config.BASE_URL, transport=Transport(session=AUTHS))
    requistionNo = ""
    if request.method == 'POST':
        try:
            requistionNo = request.POST.get('requistionNo')
            myUserID = request.session['User_ID']
        except ValueError as e:
            messages.error(request, "Missing Input")
            return redirect('GeneralRequisitionDetails', pk=pk)
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        try:
            response = CLIENT.service.FnRequestInternalRequestApproval(
                myUserID, requistionNo)
            messages.success(request, "Approval Request Sent Successfully")
            print(response)
            return redirect('GeneralRequisitionDetails', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('GeneralRequisitionDetails', pk=pk)
    return redirect('GeneralRequisitionDetails', pk=pk)

def FnCancelGeneralApproval(request, pk):
    if request.method == 'POST':
        requistionNo = request.POST.get('requistionNo')
        try:
            response = config.CLIENT.service.FnCancelInternalRequestApproval(
                request.session['User_ID'], requistionNo)
            messages.success(request, "Cancel Approval Successful")
            print(response)
            return redirect('GeneralRequisitionDetails', pk=pk)
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('GeneralRequisitionDetails', pk=pk)
    return redirect('GeneralRequisitionDetails', pk=pk)

def FnGenerateGeneralReport(request, pk):
    nameChars = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                        for i in range(5))
    if request.method == 'POST':
        filenameFromApp = pk + str(nameChars) + ".pdf"
        try:
            response = config.CLIENT.service.FnGenerateRequisitionReport(
                pk, filenameFromApp)
            buffer = BytesIO.BytesIO()
            content = base64.b64decode(response)
            buffer.write(content)
            responses = HttpResponse(
                buffer.getvalue(),
                content_type="application/pdf",
            )
            responses['Content-Disposition'] = f'inline;filename={filenameFromApp}'
            return responses
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('GeneralRequisitionDetails', pk=pk)
    return redirect('GeneralRequisitionDetails', pk=pk)