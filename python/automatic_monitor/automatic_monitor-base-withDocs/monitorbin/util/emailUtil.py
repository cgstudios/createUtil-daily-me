#!/usr/bin/python3
#coding=utf-8

import sys
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

#author: cg错过
#time: 2017-09-30

class EmailUtil:

    #发送邮件模块

    def __init__(self, dictNeedRunMsg, fileUtilObj):

        #dictNeedRunMsg:存放从配置文件中读取到的数据，其数据是本次检测运行所需要的数据
        #fileUtilObj: FileUtil的对象(脚本从运行到结束都只有这一个FileUtil对象)
        #其中的key有
        #smtp_server:
        #mail_sendAddr:
        #mail_sendPasswd:
        #mail_toAddr:

        self.fileUtilObj = fileUtilObj
        dictEmailMsg = self.getForEmailMsg(dictNeedRunMsg)
        listEmailContentMsg = self.checkAndGetForEmailListMsg()

        strServerName = dictEmailMsg.get('servername')
        strUserName = dictEmailMsg.get('username')
        listNewEmailContentMsg = self.fileUtilObj.reWriterForEmail(listEmailContentMsg, dictEmailMsg)
        
        self.choiceSend(dictEmailMsg, listNewEmailContentMsg)
        
    def getForEmailMsg(self, dictNeedRunMsg):

        #将从配置文件的完全读取到的数据中，抽取出发送邮件需要的数据，存放为dict类型并返回
        #dictNeedRunMsg: 存放从配置文件中读取到的数据，其数据是本次检测运行所需要的数据
        #因为有可能并不是所有项目都配置了需要运行

        dictMsgForEmail = {}
        for keyItem in dictNeedRunMsg:
            if((keyItem == 'email_sendaddr') | (keyItem == 'email_sendpasswd') |
               (keyItem == 'smtp_server') | (keyItem == 'ToEmail') | (keyItem == 'logpath') |
               (keyItem == 'servername') | (keyItem == 'username')):
                dictMsgForEmail[keyItem] = dictNeedRunMsg.get(keyItem)
    
        return dictMsgForEmail

    def checkAndGetForEmailListMsg(self):

        #检查是否存在日志，并读取该日志进行返回
        #返回格式:如无错误日志list长度为2，有错误日志list长度为3
        #list[0]: Hour或者Second或者no
        #list[1]: 需要发送的邮件内容(仅运行日志)
        #list[2]: 错误日志的相对路径地址
        
        #产生的日志文件中，在每分钟和每小时的两种情况中，只会运行一种情况
        #也就是只会产生一个日志
        
        listSendContent = []
        intExistsContent = self.fileUtilObj.checkFileExists(self.fileUtilObj.strlogContentName)
        intExistsContentS = self.fileUtilObj.checkFileExists(self.fileUtilObj.strlogContentSecondName)
        if(intExistsContent == 1):
            listSendContent.append('Hour')
            print(self.fileUtilObj.strlogContentName)
            strContent = self.fileUtilObj.readFileContent(self.fileUtilObj.strlogContentName)
            listSendContent.append(strContent)
            
            intExistsErr = self.fileUtilObj.checkFileExists(self.fileUtilObj.strlogErrName)
            if(intExistsErr == 1):
                print("每小时，有错误，附件")
                listSendContent.append(self.fileUtilObj.strlogErrName)
            else:
                print("每小时，无错误")
        elif(intExistsContentS == 1):
            listSendContent.append('Second')
            print(self.fileUtilObj.strlogContentSecondName)
            strContentS = self.fileUtilObj.readFileContent(self.fileUtilObj.strlogContentSecondName)
            listSendContent.append(strContentS)
            
            intExistsErrS = self.fileUtilObj.checkFileExists(self.fileUtilObj.strlogErrSecondName)
            if(intExistsErrS == 1):
                print("每分钟，有错误，附件")
                listSendContent.append(self.fileUtilObj.strlogErrSecondName)
            else:
                print("每分钟，无错误")

        else:
            listSendContent.append('no')
            strContent = "未产生日志文件"
            self.fileUtilObj.writerContent("未产生日志文件", 'runErr')
            listSendContent.append(strContent)
        print("未重构......")
        print(listSendContent)

        return listSendContent


    def choiceSend(self, dictEmailMsg, listEmailContent):

        #选择发送类型(有无附件)
        #dictEmailMsg: 发送和接受邮件账户，及smtp服务器地址
        #listEmailContent: 发送的邮件内容，主题，附件

        strSmtpServer = dictEmailMsg.get('smtp_server')
        strSendAddr = dictEmailMsg.get('email_sendaddr')
        strPasswd = dictEmailMsg.get('email_sendpasswd')
        listToAddr = dictEmailMsg.get('ToEmail')
        strSubject = listEmailContent[1]
        strContent = listEmailContent[2]

        if(len(listEmailContent) == 3):
            if(listEmailContent[0] != 'no'):
                self.sendEmailByString(strSmtpServer, strSendAddr, strPasswd,
                               listToAddr, strSubject, strContent)
            else:
                self.fileUtilObj.writerContent("邮件未发送", 'runErr')
        else:
            strErrFilePath = listEmailContent[3]
            self.sendEmailByStringAndFile(strSmtpServer, strSendAddr, strPasswd,
                               listToAddr, strSubject, strContent, strErrFilePath)
        
        #print(self.fileUtilObj.strlogContentSecondName)


    def sendEmailByString(self, strSmtpServer, strSendAddr, strPasswd,
                          listToAddr, strSubject, strContent):

        #用字符串来发送邮件
        #strSmtpServer: smtp服务器地址
        #strSendAddr: 邮件发送地址
        #strPasswd: 发送地址的登陆授权码
        #listToAddr: 接受邮件的地址，为list集合
        #strSubject: 邮件主题
        #strContent: 邮件内容字符串类型
        #message对象中的三个key('From','To','Subject')最好都要有，不然容易被识别为垃圾邮件
        
        #mail_port = '465'
        
        message = MIMEText(strContent, "plain", "utf-8")
        message['Subject'] = Header(strSubject, 'utf-8')
        message['From'] = Header('monitor<%s>' % strSendAddr, 'utf-8')
        message['To'] = Header('monitor.admin', 'utf-8')

        try:
            smtpObj = SMTP_SSL(strSmtpServer)
            #smtpObj.set_debuglevel(1)
            smtpObj.ehlo(strSmtpServer)
            smtpObj.login(strSendAddr, strPasswd)
            if(len(listToAddr) > 0):
                smtpObj.sendmail(strSendAddr, listToAddr, message.as_string())
                smtpObj.quit()
            else:
                self.fileUtilObj.writerContent("接收邮件地址为空", 'runErr')
            #self.fileUtilObj.writerContent("邮件发送成功")
        except:
            print(sys.exc_info()[0])
            self.fileUtilObj.writerContent("邮件发送失败", 'runErr')


    def sendEmailByStringAndFile(self, strSmtpServer, strSendAddr, strPasswd,
                          listToAddr, strSubject, strContent, strErrFilePath):

        #发送有附件的邮件
        #strSmtpServer: smtp服务器地址
        #strSendAddr: 邮件发送地址
        #strPasswd: 发送地址的登陆授权码
        #listToAddr: 接受邮件的地址，为list集合
        #strSubject: 邮件主题
        #strContent: 邮件内容字符串类型
        #message对象中的三个key('From','To','Subject')最好都要有，不然容易被识别为垃圾邮件
        
        #mail_port = '465'

        message = MIMEMultipart()
        message['Subject'] = Header(strSubject, 'utf-8')
        message['From'] = Header('monitor<%s>' % strSendAddr, 'utf-8')
        message['To'] = Header('monitor.admin', 'utf-8')

        message.attach(MIMEText(strContent, 'plain', 'utf-8'))

        annexFile = MIMEText(open(strErrFilePath, 'rb').read(), 'base64', 'utf-8')
        annexFile["Content-Type"] = 'application/octet-stream'
        annexFile["Content-Disposition"] = 'attachment; filename="err_logs.txt"'
        message.attach(annexFile)

        try:
            smtpObj = SMTP_SSL(strSmtpServer)
            #smtpObj.set_debuglevel(1)
            smtpObj.ehlo(strSmtpServer)
            smtpObj.login(strSendAddr, strPasswd)
            if(len(listToAddr) > 0):
                smtpObj.sendmail(strSendAddr, addrItem, message.as_string())
                smtpObj.quit()
            else:
                self.fileUtilObj.writerContent("接受邮件地址为空", 'runErr')
            #self.fileUtilObj.writerContent("附件邮件发送成功")
        except:
            print(sys.exc_info()[0])
            self.fileUtilObj.writerContent("附件邮件发送失败", 'runErr')
        
        
