import base64
from django.shortcuts import render, redirect
from datetime import datetime
import requests
from requests import Session
import json
from django.conf import settings as config
import datetime as dt
from django.contrib import messages
import enum
import secrets
import string
from django.http import HttpResponse
import io as BytesIO
from django.views import View
from myRequest.views import UserObjectMixins

# Create your views here.
class ImprestRequisition(UserObjectMixins,View):
    def get(self,request):
        try:
            userID =  request.session['User_ID']

            response = self.one_filter("/Imprests","User_Id","eq",userID)
            openImprest = [x for x in response[1] if x['Status'] == 'Open']
            Pending = [x for x in response[1] if x['Status'] == 'Pending Approval']
            Approved = [x for x in response[1] if x['Status'] == 'Released']

        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('auth')
        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {
            "today": self.todays_date, "res": openImprest,
            "response": Approved,"pending": Pending,
            "full": userID
            }
        return render(request, 'imprestReq.html', ctx)
    def post(self,request):
        if request.method == 'POST':
            try:
                accountNo = request.session['Customer_No_']
                responsibilityCenter = request.session['User_Responsibility_Center']
                usersId = request.session['User_ID']
                personalNo = request.session['Employee_No_']
                imprestNo = request.POST.get('imprestNo')
                travelType = int(request.POST.get('travelType'))
                purpose = request.POST.get('purpose')
                isImprest = eval(request.POST.get('isImprest'))
                isDsa = eval(request.POST.get('isDsa'))
                myAction = request.POST.get('myAction')
                imprestNo = request.POST.get('imprestNo')

                if isImprest == False and isDsa == False:
                    messages.info(request,"Both DSA and Imprest cannot be empty.")
                    return redirect('imprestReq')

                response = self.zeep_client(request).service.FnImprestHeader(
                    imprestNo, accountNo, responsibilityCenter, travelType, purpose,
                     usersId, personalNo, isImprest, isDsa, myAction)
                if response !='0':
                    messages.success(request, "Request Successful")
                    return redirect('IMPDetails', pk=response)
                messages.error(request, response)
                return redirect('imprestReq')
            except KeyError:
                messages.info(request, "Session Expired. Please Login")
                return redirect('auth')
            except Exception as e:
                messages.error(request, e)
                return redirect('imprestReq')
        return redirect('imprestReq')


class ImprestDetails(UserObjectMixins, View):
    def get(self, request,pk):
        try:
            userID = request.session['User_ID']

            response = self.double_filtered_data("/Imprests","No_","eq",pk,
                        "and","User_Id","eq",userID)
            for imprest in response[1]:
                res = imprest

            Imprest_RES = self.one_filter("/QyReceiptsAndPaymentTypes","Type","eq","Imprest")
            res_type = [x for x in Imprest_RES[1]]

            Dimension = config.O_DATA.format("/QyDimensionValues")
            Dimension_RES = self.get_object(Dimension)
            Area = [x for x in Dimension_RES['value'] if x['Global_Dimension_No_'] == 1]
            BizGroup = [x for x in Dimension_RES['value'] if x['Global_Dimension_No_'] == 2]

            destination = config.O_DATA.format("/QyDestinations")
            res_dest = self.get_object(destination)
            Local = [x for x in res_dest['value'] if x['Destination_Type'] == 'Local']
            ForegnDest = [x for x in res_dest['value'] if x['Destination_Type'] == 'Foreign']

            res_approver = self.one_filter("/QyApprovalEntries","Document_No_","eq",pk)
            Approvers = [x for x in res_approver[1]]

            responses = self.one_filter("/QyImprestLines","AuxiliaryIndex1","eq",pk)
            openLines = [x for x in responses[1] if x['AuxiliaryIndex1'] == pk]

            res_file = self.one_filter("/QyDocumentAttachments","No_","eq",pk)
            allFiles = [x for x in res_file[1]]

            RejectedResponse = self.one_filter("/QyApprovalCommentLines","Document_No_","eq",pk)
            Comments = [x for x in RejectedResponse[1]]
        except Exception as e:
            print(e)
            messages.info(request, e)
            return redirect('imprestReq')
                        
        ctx = {"today": self.todays_date, "res": res,"line": openLines,"Approvers": Approvers,
               "type": res_type,"area": Area, "biz": BizGroup,"Local": Local,
               "full": userID, "Foreign": ForegnDest, "dest": destination,"file":allFiles,"Comments":Comments}
        return render(request, 'imprestDetail.html', ctx)
    def post(self, request,pk):
        if request.method == 'POST':
            try:
                lineNo = int(request.POST.get('lineNo'))
                destination = request.POST.get('destination')
                imprestTypes = request.POST.get('imprestType')
                requisitionType = request.POST.get('requisitionType')
                DSAType= request.POST.get('DSAType')
                travelDate = datetime.strptime(
                    request.POST.get('travel'), '%Y-%m-%d').date()
                amount = float(request.POST.get("amount"))
                returnDate = datetime.strptime(
                    request.POST.get('returnDate'), '%Y-%m-%d').date()
                myAction = request.POST.get('myAction')

                class Data(enum.Enum):
                    values = imprestTypes
                imprestType = (Data.values).value

                if not amount:
                    amount = 0
            
                if not imprestType:
                    messages.info(request,"Both Imprest and DSA can't be empty.")
                    return redirect('IMPDetails', pk=pk)

                if DSAType:
                    requisitionType = DSAType

                response = self.zeep_client(request).service.FnImprestLine(
                    lineNo, pk, imprestType, destination, travelDate, returnDate, requisitionType,
                    float(amount), myAction)
                if response == True:
                    messages.success(request, "Request Successful")
                    return redirect('IMPDetails', pk=pk)
                messages.error(request, response)
                return redirect('IMPDetails', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('IMPDetails', pk=pk)
        return redirect('IMPDetails', pk=pk)



class UploadAttachment(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == "POST":
            try:
                attach = request.FILES.getlist('attachment')
                tableID = 52177430
                for files in attach:
                    fileName = request.FILES['attachment'].name
                    attachment = base64.b64encode(files.read())
                    response = self.zeep_client(request).service.FnUploadAttachedDocument(
                            pk, fileName, attachment, tableID,request.session['User_ID'])

                if response == True:
                    messages.success(request, "File(s) Upload Successful")
                    return redirect('IMPDetails', pk=pk)
                messages.error(request, "Failed, Try Again")
                return redirect('IMPDetails', pk=pk)
            except Exception as e:
                print(e)
                messages.error(request, e)
                return redirect('IMPDetails', pk=pk)
        return redirect('IMPDetails', pk=pk)

class FnDeleteImprestLine(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                lineNo = int(request.POST.get('lineNo'))

                response = self.zeep_client(request).service.FnDeleteImprestLine(
                    lineNo, pk)
                if response == True:
                    messages.success(request, "Deleted Successfully")
                    return redirect('IMPDetails', pk=pk)
                messages.error(request, response)
                return redirect('IMPDetails', pk=pk)
            except Exception as e:
                messages.info(request, e)
                print(e)
                return redirect('IMPDetails', pk=pk)
        return redirect('IMPDetails', pk=pk)


class FnGenerateImprestReport(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                nameChars = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                            for i in range(5))
                filenameFromApp = pk + str(nameChars) + ".pdf"
                response = self.zeep_client(request).service.FnGenerateImprestReport(
                    request.session['Employee_No_'], filenameFromApp, pk)
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
                return redirect('auth')
        return redirect('IMPDetails', pk=pk)

class DeleteImprestAttachment(UserObjectMixins,View):
    def post(self,request,pk):
        if request.method == "POST":
            try:
                docID = int(request.POST.get('docID'))
                tableID= int(request.POST.get('tableID'))
                response = self.zeep_client(request).service.FnDeleteDocumentAttachment(
                    pk,docID,tableID)
                if response == True:
                    messages.success(request, "Deleted Successfully")
                    return redirect('IMPDetails', pk=pk)
                messages.error(request, response)
                return redirect('IMPDetails', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('IMPDetails', pk=pk)

class FnRequestPaymentApproval(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                requisitionNo = request.POST.get('requisitionNo')
                response = self.zeep_client(request).service.FnRequestPaymentApproval(
                    request.session['Employee_No_'], requisitionNo)
                if response == True:
                    messages.success(request, "Approval Request Sent Successfully")
                    return redirect('IMPDetails', pk=pk)
                messages.success(request, response)
                return redirect('IMPDetails', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('IMPDetails', pk=pk)


class FnCancelPaymentApproval(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                requisitionNo = request.POST.get('requisitionNo')

                response = self.zeep_client(request).service.FnCancelPaymentApproval(
                    request.session['Employee_No_'], requisitionNo)
                if response == True:
                    messages.success(request, "Cancel Approval Successful")
                    return redirect('IMPDetails', pk=pk)
                messages.success(request, response)
                return redirect('IMPDetails', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('IMPDetails', pk=pk)


class ImprestSurrender(UserObjectMixins,View):
    def get(self,request):
        try:
            userID = request.session['User_ID']

            response = self.one_filter("/QyImprestSurrenders","User_Id","eq",userID)
            openSurrender = [x for x in response[1] if x['Status'] == 'Open']
            Pending = [x for x in response[1] if x['Status'] == 'Pending Approval']
            Approved = [x for x in response[1] if x['Status'] == 'Released']

            Released = self.double_filtered_data("/Imprests","User_Id","eq",userID,
                        "and","Status","eq","Released")
            APPImp=[x for x in Released[1] if x['Imprest'] == True and x['Surrendered'] ==False and x['Posted'] == True ]

        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, "Whoops! Something went wrong. Please Login to Continue")
            return redirect('auth')
        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {
            "today": self.todays_date, "res": openSurrender,
            "full": userID,"response": Approved,
            "app": APPImp,"pending": Pending
            }
        
        return render(request, 'imprestSurr.html', ctx)
    def post(self,request):
        if request.method == 'POST':
            try:
                usersId = request.session['User_ID']
                staffNo = request.session['Employee_No_']
                accountNo = request.session['Customer_No_']
                surrenderNo = request.POST.get('surrenderNo')
                imprestIssueDocNo = request.POST.get('imprestIssueDocNo')
                purpose = request.POST.get('purpose')
                myAction = request.POST.get('myAction')

                if not imprestIssueDocNo:
                    messages.error(request, "Select Imprest to Surrender")
                    return redirect('imprestSurr')

                response = self.zeep_client(request).service.FnImprestSurrenderHeader(
                    surrenderNo, imprestIssueDocNo, accountNo, purpose, usersId, staffNo, myAction)
                if response != '0':
                    messages.success(request, "Request Successful")
                    return redirect('IMPSurrender', pk=response)
                messages.error(request, response)
                return redirect('imprestSurr')
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('imprestSurr')
        return redirect('imprestSurr')
    


class SurrenderDetails(UserObjectMixins, View):
    def get(self, request,pk):
        try:
            userID = request.session['User_ID']

            response = self.double_filtered_data("/QyImprestSurrenders","No_","eq",pk,
                                        "and","User_Id","eq",userID)
            for imprest in response[1]:
                res = imprest
            Imprest_RES = self.one_filter("/QyReceiptsAndPaymentTypes","Type","eq","Imprest")
            res_type = [x for x in Imprest_RES[1]]

            res_approver = self.one_filter("/QyApprovalEntries","Document_No_","eq",pk)
            Approvers = [x for x in res_approver[1]]

            res_file = self.one_filter("/QyDocumentAttachments","No_","eq",pk)
            allFiles = [x for x in res_file[1]]

            RejectedResponse = self.one_filter("/QyApprovalCommentLines","Document_No_","eq",pk)
            Comments = [x for x in RejectedResponse[1]]

            responses = self.one_filter("/QyImprestSurrenderLines","No","eq",pk)
            openLines = [x for x in responses[1] if x['No'] == pk]
  

        except requests.exceptions.ConnectionError as e:
            print(e)
            return redirect('imprestSurr')
        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {"today": self.todays_date, "res": res,"line": openLines,
            "Approvers": Approvers, "type": res_type, "full": userID,"file":allFiles,"Comments":Comments}
        
        return render(request, 'SurrenderDetail.html', ctx)
    def post(self, request,pk):
        if request.method == 'POST':
            try:
                lineNo = int(request.POST.get('lineNo'))
                actualSpent = float(request.POST.get('actualSpent'))

                response = self.zeep_client(request).service.FnImprestSurrenderLine(
                    lineNo, pk, actualSpent)
                if response == True:
                    messages.success(request, "Request Successful")
                    return redirect('IMPSurrender', pk=pk)
                messages.error(request, response)
                return redirect('IMPSurrender', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('IMPSurrender', pk=pk)
        return redirect('IMPSurrender', pk=pk)


class UploadSurrenderAttachment(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == "POST":
            try:
                tableID = 52177430
                attach = request.FILES.getlist('attachment')
                for files in attach:
                    fileName = request.FILES['attachment'].name
                    attachment = base64.b64encode(files.read())
                    response = self.zeep_client(request).service.FnUploadAttachedDocument(
                            pk, fileName, attachment, tableID,request.session['User_ID'])

                if response == True:
                    messages.success(request, "File(s) Upload Successful")
                    return redirect('IMPSurrender', pk=pk)
                messages.error(request, "Failed, Try Again")
                return redirect('IMPSurrender', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('IMPSurrender', pk=pk)
        return redirect('IMPSurrender', pk=pk)

class DeleteSurrenderAttachment(UserObjectMixins,View):
    def post(self,request,pk):
        if request.method == "POST":
            docID = int(request.POST.get('docID'))
            tableID= int(request.POST.get('tableID'))
            try:
                response = self.zeep_client(request).service.FnDeleteDocumentAttachment(
                    pk,docID,tableID)
                if response == True:
                    messages.success(request, "Deleted Successfully")
                    return redirect('IMPSurrender', pk=pk)
                messages.success(request, "Deleted Successfully")
                return redirect('IMPSurrender', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('IMPSurrender', pk=pk)

class FnGenerateImprestSurrenderReport(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                nameChars = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                            for i in range(5))
                filenameFromApp = pk + str(nameChars) + ".pdf"
                response = self.zeep_client(request).service.FnGenerateImprestSurrenderReport(
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
                return redirect('IMPSurrender', pk=pk)
        return redirect('IMPSurrender', pk=pk)


class SurrenderApproval(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                requisitionNo = request.POST.get('requisitionNo')

                response = self.zeep_client(request).service.FnRequestPaymentApproval(
                    request.session['Employee_No_'], requisitionNo)
                if response == True:
                    messages.success(request, "Approval Request Sent Successfully")
                    return redirect('IMPSurrender', pk=pk)
                messages.error(request, response)
                return redirect('IMPSurrender', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('IMPSurrender', pk=pk)


class FnCancelSurrenderApproval(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                requisitionNo = request.POST.get('requisitionNo')

                response = self.zeep_client(request).service.FnCancelPaymentApproval(
                    request.session['Employee_No_'], requisitionNo)
                if response == True:
                    messages.success(request, "Cancel Approval Successful")
                    return redirect('IMPSurrender', pk=pk)
                messages.success(request, response)
                return redirect('IMPSurrender', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('IMPSurrender', pk=pk)


class StaffClaim(UserObjectMixins,View):
    def get(self, request):
        try:
            userID = request.session['User_ID']

            response = self.one_filter("/QyStaffClaims","User_Id","eq",userID)
            openClaim = [x for x in response[1] if x['Status'] == 'Open']
            Pending = [x for x in response[1] if x['Status'] == 'Pending Approval']
            Approved = [x for x in response[1] if x['Status'] == 'Released']

            res_claim = self.comparison_double_filter("/QyImprestSurrenders","User_Id","eq",userID,
                                "and", "Actual_Amount_Spent","gt","Imprest_Amount")
            My_Claim = [x for x in res_claim[1]]
                
        except requests.exceptions.ConnectionError as e:
            print(e)
            messages.info(request,e)
            return redirect('auth')
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {
            "today": self.todays_date, "res": openClaim,
            "response": Approved,"my_claim": My_Claim,
            "pending": Pending,
            "full": userID
            }
        return render(request, 'staffClaim.html', ctx)
    def post(self,request):
        if request.method == 'POST':
            try:
                accountNo = request.session['Customer_No_']
                usersId = request.session['User_ID']
                staffNo = request.session['Employee_No_']
                claimNo = request.POST.get('claimNo')
                claimType = int(request.POST.get('claimType'))
                imprestSurrDocNo = request.POST.get('imprestSurrDocNo')
                purpose = request.POST.get('purpose')
                myAction = request.POST.get('myAction')

                if not imprestSurrDocNo:
                    imprestSurrDocNo = " "

                response = self.zeep_client(request).service.FnStaffClaimHeader(
                    claimNo, claimType, accountNo, purpose, usersId, staffNo, imprestSurrDocNo, myAction)
                if response == True:
                    messages.success(request, "Request Successful")
                    return redirect('claim')
                messages.success(request, response)
                return redirect('claim')
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('claim')


class ClaimDetails(UserObjectMixins, View):
    def get(self, request,pk):
        try:
            userID = request.session['User_ID']

            response = self.double_filtered_data("/QyStaffClaims","No_","eq",pk,
                            "and","User_Id","eq",userID)
            for claim in response[1]:
                res = claim

            Claim_RES = self.one_filter("/QyReceiptsAndPaymentTypes","Type","eq","Claim")
            res_type = [x for x in Claim_RES[1]]
            
            res_approver = self.one_filter("/QyApprovalEntries","Document_No_","eq",pk)
            Approvers = [x for x in res_approver[1]]

            res_file = self.one_filter("/QyDocumentAttachments","No_","eq",pk)
            allFiles = [x for x in res_file[1]]

            RejectedResponse = self.one_filter("/QyApprovalCommentLines","Document_No_","eq",pk)
            Comments = [x for x in RejectedResponse[1]]

            res_Line = self.one_filter("/QyStaffClaimLines","No","eq",pk)
            openLines = [x for x in res_Line[1] if x['No'] == pk]
 
        except requests.exceptions.ConnectionError as e:
            print(e)
            return redirect('claim')
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')

        ctx = {"today": self.todays_date, "res": res,
              "res_type": res_type,"Approvers": Approvers, "line": openLines,
            "full": userID,"file":allFiles,"Comments":Comments}
        
        return render(request, "ClaimDetail.html", ctx)
    def post(self, request,pk):
        if request.method == 'POST':
            try:
                claimNo = pk
                accountNo = request.session['Customer_No_']
                lineNo = int(request.POST.get('lineNo'))
                claimType = request.POST.get('claimType')
                amount = float(request.POST.get('amount'))
                expenditureDate = datetime.strptime(
                    request.POST.get('expenditureDate'), '%Y-%m-%d').date()
                expenditureDescription = request.POST.get('expenditureDescription')
                attach = request.FILES.getlist('attachment')
                myAction = request.POST.get('myAction')
                tableID = 52177431
                claimReceiptNo = ""
                dimension3 = ''

                response = self.zeep_client(request).service.FnStaffClaimLine(
                    lineNo, claimNo, claimType, accountNo, amount, claimReceiptNo, dimension3, expenditureDate, expenditureDescription, myAction)

                if response != 0:
                    for files in attach:
                        fileName = request.FILES['attachment'].name
                        attachment = base64.b64encode(files.read())
                        try:
                            responses = self.zeep_client(request).service.FnUploadAttachedDocument(
                                pk +'#'+str(response), fileName, attachment, tableID,request.session['User_ID'])
                            if responses == True:
                                messages.success(request, "Request Successful")
                                return redirect('ClaimDetail', pk=pk)
                            messages.error(request, "Failed, Try Again")
                            return redirect('ClaimDetail', pk=pk)
                        except Exception as e:
                            messages.error(request, e)
                            print(e)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('ClaimDetail', pk=pk)

class ClaimApproval(UserObjectMixins, View):
    def post(self, request,pk):
        if request.method == 'POST':
            try:
                requisitionNo = request.POST.get('requisitionNo')

                response = self.zeep_client(request).service.FnRequestPaymentApproval(
                    request.session['Employee_No_'], requisitionNo)
                if response == True:
                    messages.success(request, "Approval Request Sent Successfully")
                    return redirect('ClaimDetail', pk=pk)
                messages.error(request, response)
                return redirect('ClaimDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('ClaimDetail', pk=pk)

class DeleteClaimAttachment(UserObjectMixins,View):
    def post(self, request,pk):
        if request.method == "POST":
            try:
                docID = int(request.POST.get('docID'))
                tableID= int(request.POST.get('tableID'))
                response = self.zeep_client(request).service.FnDeleteDocumentAttachment(
                    pk,docID,tableID)
                if response == True:
                    messages.success(request, "Deleted Successfully")
                    return redirect('ClaimDetail', pk=pk)
                messages.error(request, response)
                return redirect('ClaimDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('ClaimDetail', pk=pk)

class FnCancelClaimApproval(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                requisitionNo = request.POST.get('requisitionNo')

                response =self.zeep_client(request).service.FnCancelPaymentApproval(
                    request.session['Employee_No_'], requisitionNo)
                print("response",response)
                if response == True:
                    messages.success(request, "Cancel Approval Successful")
                    return redirect('ClaimDetail', pk=pk)
                messages.success(request, response)
                return redirect('ClaimDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('ClaimDetail', pk=pk)

class FnDeleteStaffClaimLine(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                lineNo = int(request.POST.get('lineNo'))
                response = self.zeep_client(request).service.FnDeleteStaffClaimLine(lineNo,pk)
                if response == True:
                    messages.success(request, "Successfully Deleted")
                    return redirect('ClaimDetail', pk=pk)
                messages.error(request, response)
                return redirect('ClaimDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('ClaimDetail', pk=pk)


class FnGenerateStaffClaimReport(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                nameChars = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                            for i in range(5))
                filenameFromApp = pk + str(nameChars) + ".pdf"
                response = self.zeep_client(request).service.FnGenerateStaffClaimReport(
                    request.session['Employee_No_'], filenameFromApp, pk)
                messages.success(request, "Successfully Sent")
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
        return redirect('ClaimDetail', pk=pk)
