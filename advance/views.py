from django.shortcuts import render, redirect
import requests
from django.conf import settings as config
import json
from django.contrib import messages
import datetime as dt
from django.views import View
from myRequest.views import UserObjectMixins
import base64
import time

class advance(UserObjectMixins,View):
    def get(self,request):
        starting_time = time.time()
        try:
            fullname =  request.session['User_ID']
            empNo =request.session['Employee_No_']

            response = self.one_filter("/QySalaryAdvances","Employee_No","eq",empNo)
            openAdvance = [x for x in response[1] if x['Loan_Status'] == 'Application']
            Pending = [x for x in response[1] if x['Loan_Status'] == 'Being Processed']
            Approved = [x for x in response[1] if x['Loan_Status'] == 'Approved']

            SalaryProducts = config.O_DATA.format("/QyLoanProductTypes")
            SalaryResponse = self.get_object(SalaryProducts)
            salary = SalaryResponse['value']
        except requests.exceptions.RequestException as e:
            print(e)
            messages.info(request, e)
            return redirect('auth')
        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            print(e)
            messages.error(request,e)
            return redirect('auth')
        total_time = time.time() - starting_time
        ctx = {
            "today": self.todays_date, "res": openAdvance,
            "response": Approved,"time": total_time,
            "pending": Pending,
            "full": fullname,"salary":salary
            }
        return render(request,"advance.html",ctx)
    def post(self, request):
        if request.method == "POST":
            try:
                loanNo = request.POST.get('loanNo')
                employeeNo = request.session['Employee_No_'] 
                productType = request.POST.get('productType')
                amountRequested = float(request.POST.get('amountRequested'))
                myUserId = request.session['User_ID']
                installments = int(request.POST.get('installments'))
                myAction = request.POST.get('myAction')

                if installments <=0 or installments > 12:
                    messages.info(request, "Installments cannot be less than 1 or more than 12")
                    return redirect('advance')

                response = self.zeep_client(request).service.FnSalaryAdvanceApplication(
                    loanNo, employeeNo,productType,amountRequested,myUserId,installments, myAction)

                if response != "0":
                    messages.success(request, "Success")
                    return redirect('advanceDetail', pk=response) 
                messages.error(request, response)
                return redirect('advance')
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('advance')

class advanceDetail(UserObjectMixins,View):
    def get(self, request,pk):
        try:
            fullname = request.session['User_ID']
            empNo =request.session['Employee_No_']

            response = self.double_filtered_data("/QySalaryAdvances","Loan_No", "eq",pk,
                            "and","Employee_No","eq",empNo)
            for advance in response[1]:
                res = advance
                state = advance['Loan_Status']

            res_approver = self.one_filter("/QyApprovalEntries","Document_No_","eq",pk)
            Approvers = [x for x in res_approver[1]]

            RejectedResponse = self.one_filter("/QyApprovalCommentLines","Document_No_","eq",pk)
            Comments = [x for x in RejectedResponse[1]]

            res_file = self.one_filter("/QyDocumentAttachments","No_","eq",pk)
            allFiles = [x for x in res_file[1]]

        except requests.exceptions.ConnectionError as e:
            print(e)
            messages.error(request,e)
            return redirect('advance')
        except KeyError as e:
            messages.info(request, "Session Expired. Please Login")
            print(e)
            return redirect('auth')
        except Exception as e:
                messages.error(request, e)
                print(e)
        ctx = {
            "today": self.todays_date, "res": res,
            "Approvers": Approvers, "state": state,"file":allFiles,
            "full": fullname,"Comments":Comments
            }

        return render(request,"advanceDetails.html",ctx)

class FnRequestSalaryAdvanceApproval(UserObjectMixins,View):
    def post(self,request,pk):
        if request.method == "POST":
            try:
                response = self.zeep_client(request).service.FnRequestSalaryAdvanceApproval(
                    request.session['Employee_No_'],pk)
                print(response)
                if response == True:
                    messages.success(request, "Approval Request Sent Successfully ")
                    return redirect('advanceDetail', pk=pk) 
                messages.error(request, response)
                return redirect('advanceDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e) 
                return redirect('advanceDetail', pk=pk)       
        return redirect('advanceDetail', pk=pk)

class FnCancelSalaryAdvanceApproval(UserObjectMixins,View):
    def post(self,request,pk):
        if request.method == "POST":
            try:
                response = self.zeep_client(request).service.FnCancelSalaryAdvanceApproval(
                    request.session['Employee_No_'],pk)
                if response == True:
                    messages.success(request, "Approval Request Sent Successfully")
                    return redirect('advanceDetail', pk=pk)
                messages.errors(request, response)
                return redirect('advanceDetail', pk=pk) 
            except Exception as e:
                messages.error(request, e)
                print(e)        
        return redirect('advanceDetail', pk=pk)

class UploadAdvanceAttachment(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == "POST":
            try:
                tableID = 52177630
                attach = request.FILES.getlist('attachment')
                for files in attach:
                    fileName = request.FILES['attachment'].name
                    attachment = base64.b64encode(files.read())
                    response = config.CLIENT.service.FnUploadAttachedDocument(
                            pk, fileName, attachment, tableID,request.session['User_ID'])
                if response == True:
                    messages.success(request, "File(s) Upload Successful")
                    return redirect('advanceDetail', pk=pk)
                messages.error(request, "Failed, Try Again")
                return redirect('advanceDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('advanceDetail', pk=pk)

class DeleteAdvanceAttachment(UserObjectMixins,View):
    def post(self,request,pk):
        if request.method == "POST":
            try:
                docID = int(request.POST.get('docID'))
                tableID= int(request.POST.get('tableID'))
                response = config.CLIENT.service.FnDeleteDocumentAttachment(
                    pk,docID,tableID)

                if response == True:
                    messages.success(request, "Deleted Successfully")
                    return redirect('advanceDetail', pk=pk)
                messages.error(request, response)
                return redirect('advanceDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('advanceDetail', pk=pk)
