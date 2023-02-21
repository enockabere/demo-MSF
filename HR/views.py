import asyncio
import base64
import logging
from django.shortcuts import render, redirect
from datetime import datetime
import requests
import json
from django.conf import settings as config
import datetime as dt
from django.contrib import messages
from django.http import HttpResponse
from io import BytesIO
from asgiref.sync import sync_to_async
from django.views import View
from myRequest.views import UserObjectMixins
import aiohttp
# Create your views here.

class Leave_Planner(UserObjectMixins,View):
    def get(self,request):
        try:
            userId = request.session['User_ID']
            empNo =request.session['Employee_No_']

            response = self.one_filter("/QyLeavePlannerHeaders","Employee_No_","eq",empNo)
            Plans = response[1]
        except requests.exceptions.Timeout:
            messages.error(request, "Server timeout,retry,restart server.")
            return redirect('dashboard')
        except requests.exceptions.ConnectionError:
            messages.error(request, "Connection/network error,retry")
            return redirect('dashboard') 
        except requests.exceptions.TooManyRedirects:
            messages.error(request, "Server busy, retry")
            return redirect('dashboard')
        except KeyError as e:
            messages.info(request, "Session Expired. Please Login")
            print(e)
            return redirect('auth')
        except Exception as e:
            print(e)
            messages.info(request, e)
            return redirect('auth')
        ctx = {
            "today": self.todays_date,
            "res": Plans,
            "full": userId
            }
        return render(request, 'planner.html', ctx)

    def post(self,request):
        try:
            plannerNo = request.POST.get('plannerNo')
            empNo = request.session['Employee_No_']
            myAction = request.POST.get('myAction')

            response = self.zeep_client(request).service.FnLeavePlannerHeader(
                plannerNo, empNo, myAction)
            if response !=False:
                messages.success(request, "Success")
                return redirect('PlanDetail',pk=response)
            messages.error(request, response)
            return redirect('LeavePlanner')   
        except requests.exceptions.Timeout:
            messages.error(request, "Server timeout,retry,restart server.")
            return redirect('dashboard')
        except requests.exceptions.ConnectionError:
            messages.error(request, "Connection/network error,retry")
            return redirect('dashboard') 
        except requests.exceptions.TooManyRedirects:
            messages.error(request, "Server busy, retry")
            return redirect('dashboard')
        except KeyError as e:
            messages.info(request, "Session Expired. Please Login")
            print(e)
            return redirect('auth')
        except Exception as e:
            messages.info(request, e)
            print(e)
            return redirect('auth')
        return redirect('LeavePlanner')


class PlanDetail(UserObjectMixins,View):
    def get(self,request,pk):
        fullname = request.session['User_ID']
        empNo =request.session['Employee_No_']
        
        try:
            response = self.double_filtered_data("/QyLeavePlannerHeaders","No_","eq",pk,"and",
                                                    "Employee_No_","eq",empNo)
            for plan in response[1]:
                res=plan

            LinesRes = self.double_filtered_data("/QyLeavePlannerLines","Document_No_","eq",pk,"and",
                                                    "Employee_No_","eq",empNo)
            openLines = LinesRes[1]

        except requests.exceptions.Timeout:
            messages.error(request, "Server timeout,retry,restart server.")
            return redirect('dashboard')
        except requests.exceptions.ConnectionError:
            messages.error(request, "Connection/network error,retry")
            return redirect('dashboard') 
        except requests.exceptions.TooManyRedirects:
            messages.error(request, "Server busy, retry")
            return redirect('dashboard')
        except KeyError as e:
            messages.info(request, "Session Expired. Please Login")
            print(e)
            return redirect('auth')
        except Exception as e:
            messages.info(request, e)
            print(e)
            return redirect('auth')
        ctx = {
            "today": self.todays_date, 
            "full": fullname,
            "line": openLines,"res":res
            }
        return render(request, 'planDetails.html', ctx)

    def post(self,request, pk):
        try:
            plannerNo = pk
            lineNo = int(request.POST.get('lineNo'))
            startDate = datetime.strptime((request.POST.get('startDate')), '%Y-%m-%d').date()
            endDate = datetime.strptime((request.POST.get('endDate')), '%Y-%m-%d').date()
            myAction = request.POST.get('myAction')

            response = self.zeep_client(request).service.FnLeavePlannerLine(
            lineNo, plannerNo, startDate, endDate, myAction)
            print(response)

            if response == True:
                messages.success(request, "Request Successful")
                return redirect('PlanDetail', pk=pk)
            messages.success(request, response)
            return redirect('PlanDetail', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
        return redirect('PlanDetail', pk=pk)
        


class FnDeleteLeavePlannerLine(UserObjectMixins, View):
    def post(self,request, pk):
        if request.method == 'POST':
            try:
                lineNo = int(request.POST.get('lineNo'))
                response = self.zeep_client(request).service.FnDeleteLeavePlannerLine(pk,lineNo)
                if response == True:
                    messages.success(request, "Successfully  Deleted")
                    return redirect('PlanDetail', pk=pk)
                messages.error(request, response)
                return redirect('PlanDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('PlanDetail', pk=pk)
       
class myLeave(UserObjectMixins,View):
    """View not implemented

        Returns:
            _type_: Detailed info for user when making
            leave applications
    """
    def get(self, request):
        fullname = request.session['User_ID']
        ctx = {
            "today": self.todays_date, 
             "full": fullname,
            }
        return render(request,"myLeave.html",ctx)

class Leave_Request(UserObjectMixins,View):
    def get(self,request):
        try:
            UserId = request.session['User_ID']
            empNo =request.session['Employee_No_']

            response = self.one_filter("/QyLeaveApplications","User_ID","eq",UserId)
            openLeave = [x for x in response[1] if x['Status'] == 'Open']
            pendingLeave = [x for x in response[1] if x['Status'] == 'Pending Approval']
            approvedLeave = [x for x in response[1] if x['Status'] == 'Released']

            LeaveTypes = config.O_DATA.format("/QyLeaveTypes")
            res_types = self.get_object(LeaveTypes)
            Leave = [x for x in res_types['value']]

            res_planner = self.one_filter("/QyLeavePlannerLines","Employee_No_","eq",empNo)
            Plan = [x for x in res_planner[1]]

        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except requests.exceptions.ConnectionError as e:
            print(e)
        
        ctx = {
            "today": self.todays_date, "res": openLeave,
            "response": approvedLeave,'leave': Leave,
            "plan": Plan,"pending": pendingLeave,
            "full": UserId
            }
        return render(request, 'leave.html', ctx)
        
    def post(self, request):
        if request.method == 'POST':
            try:
                dimension3 = ''
                employeeNo = request.session['Employee_No_']
                usersId = request.session['User_ID']
                applicationNo = request.POST.get('applicationNo')
                leaveType = request.POST.get('leaveType')
                plannerStartDate = request.POST.get('plannerStartDate')
                daysApplied = request.POST.get('daysApplied')
                isReturnSameDay = eval(request.POST.get('isReturnSameDay'))
                myAction = request.POST.get('myAction')
                if not daysApplied:
                    daysApplied = 0
                plannerStartDate =  datetime.strptime(plannerStartDate, '%Y-%m-%d').date()
            
                response = self.zeep_client(request).service.FnLeaveApplication(
                    applicationNo, employeeNo, usersId, dimension3, leaveType,
                     plannerStartDate, int(daysApplied), isReturnSameDay, myAction)
                if response !=False:
                    messages.success(request, "Success")
                    return redirect('LeaveDetail', pk=response)
                messages.error(request, response)
                return redirect('leave')
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('leave')



class LeaveDetail(UserObjectMixins,View):
    def get(self,request,pk):
        try:
            userId = request.session['User_ID']

            response = self.double_filtered_data("/QyLeaveApplications","Application_No","eq",pk,
                                        "and","User_ID","eq",userId)
            for leave in response[1]:
                res=leave

            res_approver = self.one_filter("/QyApprovalEntries","Document_No_","eq",pk)
            Approvers = [x for x in res_approver[1]]

            res_file = self.one_filter("/QyDocumentAttachments","No_","eq",pk)
            allFiles = [x for x in res_file[1]]

            RejectedResponse = self.one_filter("/QyApprovalCommentLines","Document_No_","eq",pk)
            Comments = [x for x in RejectedResponse[1]]
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except requests.exceptions.ConnectionError as e:
                print(e)
                messages.error(request,"500 Server Error, Try Again")
                return redirect('leave')

        ctx = {
            "today": self.todays_date, "res": res,
            "Approvers": Approvers,
            "full": userId,"file":allFiles,"Comments":Comments
            }
        return render(request, 'leaveDetail.html', ctx)

    def post(self,request,pk):
        if request.method == "POST":
            try:
                attach = request.FILES.getlist('attachment')
                docNo = pk
                tableID = 52177494
                for files in attach:
                    fileName = request.FILES['attachment'].name
                    attachment = base64.b64encode(files.read())

                    response = self.zeep_client(request).service.FnUploadAttachedDocument(
                            docNo, fileName, attachment, tableID,request.session['User_ID'])
                if response == True:
                    messages.success(request, "Uploaded successfully")
                    return redirect('LeaveDetail', pk=pk)
                messages.error(request, response)
                return redirect('LeaveDetail', pk=pk)    
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('LeaveDetail', pk=pk)
    
    
class DeleteLeaveAttachment(UserObjectMixins,View):
    def post(self,request,pk):
        if request.method == "POST":
            try:
                docID = int(request.POST.get('docID'))
                tableID= int(request.POST.get('tableID'))
                response = self.zeep_client(request).service.FnDeleteDocumentAttachment(
                    pk,docID,tableID)
                if response == True:
                    messages.success(request, "Deleted Successfully")
                    return redirect('LeaveDetail', pk=pk)
                messages.error(request, response)
                return redirect('LeaveDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('LeaveDetail', pk=pk)

class LeaveApproval(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                employeeNo = request.session['Employee_No_']
                applicationNo = request.POST.get('applicationNo')

                response = self.zeep_client(request).service.FnRequestLeaveApproval(
                        employeeNo, applicationNo)
                if response == True:
                    messages.success(request, "Request Successful")
                    return redirect('LeaveDetail', pk=pk)
                messages.error(request, response)
                return redirect('LeaveDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('LeaveDetail', pk=pk)


class LeaveCancelApproval(UserObjectMixins, View):
    def post(self,request,pk):
        try:
            if request.method == 'POST':
                employeeNo = request.session['Employee_No_']
                applicationNo = request.POST.get('applicationNo')

            response = self.zeep_client(request).service.FnCancelLeaveApproval(
                    employeeNo, applicationNo)
            print(response)
            if response == True:
                messages.success(request, "Success")
                return redirect('LeaveDetail', pk=pk)
            messages.error(request, response)
            return redirect('LeaveDetail', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('LeaveDetail', pk=pk)


class Training_Request(UserObjectMixins,View):
    def get(self, request):
        try:
            userId = request.session['User_ID']
            empNo = request.session['Employee_No_']

            response = self.one_filter("/QyTrainingRequests","Employee_No","eq",empNo)
            openTraining = [x for x in response[1] if x['Status'] == 'Open']
            pendingTraining = [x for x in response[1] if x['Status'] == 'Pending Approval']
            approvedTraining = [x for x in response[1] if x['Status'] == 'Released']

            trainingNeed = config.O_DATA.format("/QyTrainingNeeds")
            res_train = self.get_object(trainingNeed)
            trains = [x for x in res_train['value']]

        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except requests.exceptions.ConnectionError as e:
            print(e)
            messages.error(request,"500 Server Error")
            return redirect('dashboard')

        ctx = {
            "today": self.todays_date, "res": openTraining,
            "response": approvedTraining,
            "train": trains,"pending": pendingTraining,
            "full": userId
            }
        return render(request, 'training.html', ctx)
    def post(self,request):
        if request.method == 'POST':
            try:
                employeeNo = request.session['Employee_No_']
                usersId = request.session['User_ID']
                requestNo = request.POST.get('requestNo')
                isAdhoc = eval(request.POST.get('isAdhoc'))
                trainingNeed = request.POST.get('trainingNeed')
                myAction = request.POST.get('myAction')
            
                if not trainingNeed:
                    trainingNeed = ''

                response = self.zeep_client(request).service.FnTrainingRequest(
                    requestNo, employeeNo, usersId, isAdhoc, trainingNeed, myAction)
                if response != False:
                    messages.success(request, "Success")
                    return redirect('TrainingDetail', pk=response)
                messages.error(request, response)
                return redirect('training_request')
            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect('training_request')
        return redirect('training_request')


class TrainingDetail(UserObjectMixins, View):
    def get(self,request,pk):
        try:
            userID = request.session['User_ID']
            empNo = request.session['Employee_No_'] 

            response = self.double_filtered_data("/QyTrainingRequests","Request_No_","eq",pk,
                                    "and","Employee_No","eq",empNo)
            for training in response[1]:
                res = training

            res_approver = self.one_filter("/QyApprovalEntries","Document_No_","eq",pk)
            Approvers = [x for x in res_approver[1]]

            destination = config.O_DATA.format("/QyDestinations")
            res_destination = self.get_object(destination)
            Local = [x for x in res_destination['value'] if x['Destination_Type'] == 'Local']
            Foreign = [x for x in res_destination['value'] if x['Destination_Type'] == 'Foreign']

            RejectedResponse = self.one_filter("/QyApprovalCommentLines","Document_No_","eq",pk)
            Comments = [x for x in RejectedResponse[1]]

            responseNeeds = self.double_filtered_data("/QyTrainingNeedsRequest","Source_Document_No","eq",pk,
                                                "and","Employee_No","eq",empNo)
            openLines = [x for x in responseNeeds[1]]

            res_file = self.one_filter("/QyDocumentAttachments","No_","eq",pk)
            allFiles = [x for x in res_file[1]]


        except requests.exceptions.ConnectionError as e:
            print(e)
            messages.error(request,"500 Server Error, Try Again in a few")
            return redirect('training_request')
        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('training_request')

        ctx = {
            "today": self.todays_date, "res": res,
            "Approvers": Approvers, "full": userID,"file":allFiles,
            "line": openLines,"local":Local,"foreign":Foreign,"Comments":Comments
            }
        return render(request, 'trainingDetail.html', ctx)
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                requestNo = pk
                no = ""
                employeeNo = request.session['Employee_No_']
                myAction = "insert"
                trainingName = request.POST.get('trainingName')
                startDate = datetime.strptime((request.POST.get('startDate')), '%Y-%m-%d').date()
                endDate = datetime.strptime((request.POST.get('endDate')), '%Y-%m-%d').date()
                trainingArea = request.POST.get('trainingArea')
                trainingObjectives = request.POST.get('trainingObjectives')
                venue = request.POST.get('venue')
                sponsor = request.POST.get('sponsor')
                destination = request.POST.get('destination')
                OtherDestinationName = request.POST.get('OtherDestinationName')
                provider = request.POST.get('provider')
                trainingCost = float(request.POST.get('trainingCost'))

          
                if not sponsor:
                    sponsor = 0
                sponsor = int(sponsor)

                if not destination:
                    destination = 'none'
                
                if not venue:
                    venue = "Online"

                if OtherDestinationName:
                    destination = OtherDestinationName
                if not trainingCost:
                    trainingCost = 0
  
                response = self.zeep_client(request).service.FnAdhocTrainingNeedRequest(
                    requestNo,no, employeeNo, trainingName, trainingArea, trainingObjectives,
                     venue, provider, myAction,sponsor,startDate,endDate,destination,trainingCost)
                if response == True:
                    messages.success(request, "Success")
                    return redirect('TrainingDetail', pk=pk)
                messages.error(request, response)
                return redirect('TrainingDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('TrainingDetail', pk=pk)
   
class UploadTrainingAttachment(UserObjectMixins, View):
    def post(self,request,pk):
        try:
            attachments = request.FILES.getlist('attachment')
            soap_headers = request.session['soap_headers']
            tableID = 52177501
            attachment_names = []
            response = False

            for file in attachments:
                fileName = file.name
                attachment_names.append(fileName)
                attachment = base64.b64encode(file.read())

                response = self.make_soap_request(soap_headers,'FnUploadAttachedDocument',
                        pk, fileName, attachment, tableID, request.session['User_ID'])
                
            if response is not None:
                if response == True:
                    messages.success(request, "Uploaded {} attachments successfully".format(len(attachments)))
                    return redirect('TrainingDetail', pk=pk)
                messages.error(request, "Upload failed: {}".format(response))
                return redirect('TrainingDetail', pk=pk)
            messages.error(request, "Upload failed: Response from server was None")
            return redirect('TrainingDetail', pk=pk)
        except Exception as e:
            messages.error(request, "Upload failed: {}".format(e))
            logging.exception(e)
            return redirect('TrainingDetail', pk=pk)


class FnAdhocLineDelete(UserObjectMixins, View):
    def post(self,request,pk):
        try:
            soap_headers = request.session['soap_headers']
            requestNo = pk
            needNo = request.POST.get('needNo')

            response = self.make_soap_request(soap_headers,'FnDeleteAdhocTrainingNeedRequest',
                needNo,requestNo)
            if response == True:
                messages.success(request, "Successfully Deleted")
                return redirect('TrainingDetail', pk=pk)
            messages.success(request, response)
            return redirect('TrainingDetail', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('TrainingDetail', pk=pk)


class TrainingApproval(UserObjectMixins, View):
    def post(self,request,pk):
        try:
            soap_headers = request.session['soap_headers']
            myUserID = request.session['User_ID']
            trainingNo = request.POST.get('trainingNo')

            response = self.make_soap_request(soap_headers,'FnRequestTrainingApproval',
                myUserID, trainingNo)
            if response == True:
                messages.success(request, "Approval Request Sent")
                return redirect('training_request')
            messages.error(request, response)
            return redirect('TrainingDetail', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('TrainingDetail', pk=pk)


class TrainingCancelApproval(UserObjectMixins, View):
    def post(self,request,pk):
        try:
            soap_headers = request.session['soap_headers']
            myUserID = request.session['User_ID']
            trainingNo = request.POST.get('trainingNo')

            response = self.make_soap_request(soap_headers,'FnCancelTrainingApproval',
            myUserID, trainingNo)
            if response == True:
                messages.success(request, "Approval Request Cancelled")
                return redirect('TrainingDetail', pk=pk)
            messages.error(request, response)
            return redirect('TrainingDetail', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('TrainingDetail', pk=pk)


class PNineRequest(UserObjectMixins,View):
    def get(self,request):
        try:
            userID = request.session['User_ID']
            
            Access_Point = config.O_DATA.format("/QyPayrollPeriods")
            response = self.get_object(Access_Point)
            res = response['value']
            
        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('pNine')
        ctx = {"today": self.todays_date,"full": userID,"res":res}
        return render(request, "p9.html", ctx)
    def post(self,request):
        try:
            soap_headers = request.session['soap_headers']
            employeeNo = request.session['Employee_No_']
            startDate = request.POST.get('startDate')[0:4]

            filenameFromApp = "P9_For_" + str(year) + ".pdf"
            year = int(startDate)
        
            response = self.make_soap_request(soap_headers,'FnGeneratePNine',
                employeeNo, filenameFromApp, year)
            buffer = BytesIO()
            content = base64.b64decode(response)
            buffer.write(content)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={filenameFromApp}'
            return response
        except Exception as e:
            messages.error(request, e)
            logging.exception(e)
            return redirect('pNine')



class PayslipRequest(UserObjectMixins,View):
    def get(self, request):
        try:
            userID = request.session['User_ID']
            
            Access_Point = config.O_DATA.format("/QyPayrollPeriods?$filter=Closed%20eq%20true")
            response = self.get_object(Access_Point)
            Payslip = [x for x in response['value']]

        except KeyError as e:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('payslip')
                    
        ctx = {"today": self.todays_date,"full": userID,"res":Payslip}
        
        return render(request, "payslip.html", ctx)

    def post(self,request):
            try:
                employeeNo = request.session['Employee_No_']
                soap_headers = request.session['soap_headers']

                paymentPeriod = datetime.strptime(
                    request.POST.get('paymentPeriod'), '%Y-%m-%d').date()


                filenameFromApp = "Payslip_For_" + str(paymentPeriod) + ".pdf"

                response = self.make_soap_headers(soap_headers,'FnGeneratePayslip',
                    employeeNo, filenameFromApp, paymentPeriod)
                buffer = BytesIO()
                content = base64.b64decode(response)
                buffer.write(content)
                response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename={filenameFromApp}'
                return response
            except Exception as e:
                messages.error(request, e)
                logging.exception(e)
                return redirect('payslip')

class FnGenerateLeaveReport(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            soap_headers = request.session['soap_headers']
            employeeNo = request.session['Employee_No_']
            filenameFromApp = 'Leave_Report_For_' + pk + ".pdf"

            response = self.make_soap_request(
                soap_headers, 'FnGenerateLeaveReport', employeeNo, filenameFromApp, pk)

            buffer = BytesIO()
            content = base64.b64decode(response)
            buffer.write(content)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={filenameFromApp}'
            messages.success(request, 'Downloaded successfully')
            return response
        except Exception as e:
            messages.error(request, e)
            logging.exception(e)
            return redirect('LeaveDetail', pk=pk)

class FnGenerateTrainingReport(UserObjectMixins, View):
    def post(self,request,pk):
        try:
            soap_headers = request.session['soap_headers']
            employeeNo = request.session['Employee_No_']

            filenameFromApp = "Training_Report_" + pk + ".pdf"
            response = self.make_soap_request(soap_headers,'FnGenerateTrainingReport',
                employeeNo, filenameFromApp, pk)
            buffer = BytesIO()
            content = base64.b64decode(response)
            buffer.write(content)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={filenameFromApp}'
            return response
        except Exception as e:
            messages.error(request, e)
            logging.exception(e)
            return redirect('TrainingDetail', pk=pk)
                
def Disciplinary(request):
    fullname = request.session['User_ID']
    session = requests.Session()
    session.auth = config.AUTHS

    Access_Point = config.O_DATA.format("/QyEmployeeDisciplinaryCases")
    try:
        response = session.get(Access_Point, timeout=10).json()
        openCase = []
        for case in response['value']:
            if case['Employee_No'] == request.session['Employee_No_'] and case['Posted'] == False and case['Sent_to_employee'] == True and case['Submit'] == False:
                output_json = json.dumps(case)
                openCase.append(json.loads(output_json))
        counts = len(openCase)
        print(counts)
    except requests.exceptions.ConnectionError as e:
        print(e)

    todays_date = dt.datetime.now().strftime("%b. %d, %Y %A")
    ctx = {"today": todays_date, "res": openCase,
           "full": fullname,
           "count": counts}
    return render(request,'disciplinary.html',ctx)

def DisciplineDetail(request,pk):
    fullname = request.session['User_ID']
    session = requests.Session()
    session.auth = config.AUTHS
    res = ''
    Access_Point = config.O_DATA.format("/QyEmployeeDisciplinaryCases")
    try:
        response = session.get(Access_Point, timeout=10).json()
        Case = []
        for case in response['value']:
            if case['Employee_No'] == request.session['Employee_No_'] and case['Posted'] == False and case['Sent_to_employee'] == True and case['Submit'] == False:
                output_json = json.dumps(case)
                Case.append(json.loads(output_json))
                for case in Case:
                    if case['Disciplinary_Nos'] == pk:
                        res = case
    except requests.exceptions.ConnectionError as e:
        print(e)
    Lines_Res = config.O_DATA.format("/QyEmployeeDisciplinaryLines")
    try:
        responses = session.get(Lines_Res, timeout=10).json()
        openLines = []
        for cases in responses['value']:
            if cases['Refference_No'] == pk and cases['Employee_No'] == request.session['Employee_No_']:
                output_json = json.dumps(cases)
                openLines.append(json.loads(output_json))
    except requests.exceptions.ConnectionError as e:
        print(e)
    todays_date = dt.datetime.now().strftime("%b. %d, %Y %A")
    ctx = {"today": todays_date, "res": res, "full": fullname,"line": openLines}
    return render (request, 'disciplineDetail.html',ctx)

def DisciplinaryResponse(request, pk):

    employeeNo = request.session['Employee_No_']
    caseNo = pk
    myResponse = ''
    
    if request.method == 'POST':
        try:
            myResponse = request.POST.get('myResponse')
        except ValueError as e:
            messages.error(request, "Invalid, Try Again!!")
            return redirect('DisciplineDetail', pk=pk)
    try:
        response = config.CLIENT.service.FnEmployeeDisciplinaryResponse(
            employeeNo, caseNo, myResponse)
        messages.success(request, "Response Successful Sent!!")
        print(response)
        return redirect('DisciplineDetail', pk=pk)
    except Exception as e:
        messages.error(request, e)
        print(e)
    return redirect('DisciplineDetail', pk=pk)

class PayrollDocuments(UserObjectMixins,View):
    async def get(self,request):
        try:
            full_name = await sync_to_async(request.session.__getitem__)('full_name')
            res = []
            
            async with aiohttp.ClientSession() as session:
                task_get_closed_payroll_period = asyncio.ensure_future(self.simple_fetch_data(session,
                            '/QyPayrollPeriods?$filter=Closed%20eq%20true%20and%20Status%20eq%20%27Approved%27')) 
                response = await asyncio.gather(task_get_closed_payroll_period)          
                res = [x for x in response[0]]
        except KeyError as e:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, f'{e}')
            logging.exception(e)
            return redirect('pNine')
        ctx = {
            "today": self.todays_date,
            "full": full_name,
            "res":res
            }
        return render(request, "payroll_docs.html", ctx)
    async def post(self,request):
        try:
            soap_headers = await sync_to_async(request.session.__getitem__)('soap_headers')
            employeeNo = await sync_to_async(request.session.__getitem__)('Employee_No_')
            startDate = request.POST.get('startDate')
            document_type =int(request.POST.get('document_type'))

            if document_type == 1:
                paymentPeriod = datetime.strptime(startDate, '%Y-%m-%d').date()
                filenameFromApp = f"P9_For_{paymentPeriod}.pdf"
                response = self.make_soap_request(soap_headers,'FnGeneratePayslip',
                    employeeNo, filenameFromApp, paymentPeriod)
            elif document_type == 2:
                year = int(startDate[0:4])
                filenameFromApp = f"P9_For_{year}.pdf"
                response = self.make_soap_request(soap_headers,'FnGeneratePNine',
                    employeeNo, filenameFromApp,year)
            content = base64.b64decode(response)
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment;filename={filenameFromApp}'
            return response
        except KeyError as e:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, 'Failed, non-200 error')
            logging.exception(e)
            return redirect('PayrollDocuments')