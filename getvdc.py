import os
import csv
import requests
import base64
import pandas
import xml.etree.ElementTree as ET
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


def onError():
    tk.messagebox.showerror("Error", "Please input require data")

def onEnd():
    tk.messagebox.showinfo("OK", "Report is ready, please check your current folder")

def getmaindata():
    if len(edt_url.get()) == 0:
        onError()
    elif len(edt_login.get()) == 0:
        onError()
    elif len(edt_pass.get()) == 0:
        onError()
    else:
        btn_result.config(text="Get report again!")

        #======<AUTHENTIFICATION>=========================================
        url = edt_url.get()
        # Standard Base64 Encoding


        login=edt_login.get()
        passwd=edt_pass.get()
        codestr=login+':'+passwd
        encodedBytes = base64.b64encode(codestr.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")

        # Get input headers
        headers_auth = { 'Authorization' : 'Basic %s' %  encodedStr,
                         'Accept' : 'application/*;version=31.0'
                         }

        # Get token
        auth = requests.post(url+"sessions",headers=headers_auth, verify=False)
        if auth.status_code != 200:
            tk.messagebox.showinfo("Error", "Connection failed, check input data")
        else:
            token=auth.headers['X-VMWARE-VCLOUD-ACCESS-TOKEN']
            #======<END OF AUTHENTIFICATION>=========================================

            #==========GET MAIN DATA=================================================
            headers_maindata={ 'Authorization' : 'Bearer %s' %  token,
                             'Accept' : 'application/*;version=31.0'
                             }
            params_maindata={'pageSize' : '128'}
            maindata=requests.get(url+"vms/query", params=params_maindata, headers=headers_maindata, verify=False)
            maintree=ET.fromstring(maindata.content)

            #=======TXT result file=================
            fulldate=datetime.now()
            month_today=fulldate.strftime("%B")
            datestring = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
            resultfile = open('VCDresult_' + datestring + '.csv', 'w')
            resultfile_name = resultfile.name

            writer = csv.DictWriter(
                resultfile, fieldnames=["vApp", "Name", "status","ip","month_today","cpu","Memory,GB","HDD,GB",], delimiter=";")
            writer.writeheader()

            #=======end of TXT result file=================

            for form in maintree.findall("{http://www.vmware.com/vcloud/v1.5}VMRecord"):
                vapp=form.get('containerName')
                vmname=form.get('name')
                status=form.get('status')
                ipAddress=form.get('ipAddress')
                numberOfCpus=form.get('numberOfCpus')
                memoryMB=form.get('memoryMB')
                memoryGB=int(memoryMB)/1024
                hrefvm=form.get('href')

                #=======GET DISK DATA=================================================
                diskdata = requests.get(hrefvm + "/virtualHardwareSection/disks", params=params_maindata, headers=headers_maindata, verify=False)
                disktree = ET.fromstring(diskdata.content)
                sum = 0
                for Item in disktree:
                    for ItemChild in Item.iter(
                            '{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData}HostResource'):
                        capacity = ItemChild.get('{http://www.vmware.com/vcloud/v1.5}capacity')
                        sum = sum + int(capacity)
                diskGB = int(sum) / 1024
                # =======END OF GET DISK DATA=================================================
                print(vapp, vmname, status, ipAddress, month_today, numberOfCpus, memoryGB, diskGB, sep=';', file=resultfile)
            resultfile.close()
            #=======Excel result file=================
            df = pandas.read_csv(resultfile_name,sep=';')
            df.to_excel('VCDresult_'+datestring+'.xlsx', 'Sheet1')
            #=======end of Excel result file=================
            os.remove(resultfile_name)
            onEnd()



# ======================GUI========================================
rootwin = tk.Tk()
rootwin.title("Получение отчета с VCD")
rootwin.geometry("820x130")

lbl_url = tk.Label(rootwin, text="API URL:", font=("Arial Bold", 12))
lbl_url.grid(column=0, row=0)

edt_url = tk.Entry(rootwin, width=40)
edt_url.grid(column=1, row=0)

lbl_login_url = tk.Label(rootwin, text=" symbol   /  at the end is mandatory, example:  https://vcloudurl.com/api/", font=("Arial Bold", 10))
lbl_login_url.grid(column=2, row=0)

lbl_login = tk.Label(rootwin, text="Login:", font=("Arial Bold", 12))
lbl_login.grid(column=0, row=1)

edt_login = tk.Entry(rootwin, width=40)
edt_login.grid(column=1, row=1)

lbl_login_com = tk.Label(rootwin, text="*must be in <username>@<organization in VCD>  format, example ivanov@org", font=("Arial Bold", 9))
lbl_login_com.grid(column=2, row=1)

lbl_pass = tk.Label(rootwin, text="Password:", font=("Arial Bold", 12))
lbl_pass.grid(column=0, row=2)

edt_pass = tk.Entry(rootwin, show='X', width=40)
edt_pass.grid(column=1, row=2)
login_str=edt_login.get()

btn_result = tk.Button(rootwin, text="Get Report!", width=30, font=("Arial Bold", 13), command=getmaindata)
btn_result.grid(column=1, row=3)

rootwin.mainloop()
