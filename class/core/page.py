# coding: utf-8

import math
import string


class Page():
    #--------------------------
    # Pagination class - JS callback version
    #--------------------------
    __PREV = 'Prev'
    __NEXT = 'Next'
    __START = 'Start'
    __END = 'End'
    __COUNT_START = 'Count Start'
    __COUNT_END = 'Count End'
    __FO = 'From'
    __LINE = 'Item'
    __LIST_NUM = 4
    SHIFT = None
    ROW = None
    __C_PAGE = None
    __COUNT_PAGE = None
    __COUNT_ROW = None
    __URI = None
    __RTURN_JS = False
    __START_NUM = None
    __END_NUM = None

    def __init__(self):
        if False:
            self.__PREV = tmp['PREV']
            self.__NEXT = tmp['NEXT']
            self.__START = tmp['START']
            self.__END = tmp['END']
            self.__COUNT_START = tmp['COUNT_START']
            self.__COUNT_END = tmp['COUNT_END']
            self.__FO = tmp['FO']
            self.__LINE = tmp['LINE']

    def GetPage(self, pageInfo, limit='1,2,3,4,5,6,7,8'):
        self.__RTURN_JS = pageInfo['return_js']
        self.__COUNT_ROW = pageInfo['count']
        self.ROW = pageInfo['row']
        self.__C_PAGE = self.__GetCpage(pageInfo['p'])
        self.__START_NUM = self.__StartRow()
        self.__END_NUM = self.__EndRow()
        self.__COUNT_PAGE = self.__GetCountPage()
        self.__URI = self.__SetUri(pageInfo['uri'])
        self.SHIFT = self.__START_NUM - 1

        keys = limit.split(',')
        pages = {}
        pages['1'] = self.__GetStart()
        pages['2'] = self.__GetPrev()
        pages['3'] = self.__GetPages()
        pages['4'] = self.__GetNext()
        pages['5'] = self.__GetEnd()

        pages['6'] = "<span class='Pnumber'>" + \
            str(self.__C_PAGE) + "/" + \
            str(self.__COUNT_PAGE) + "</span>"

        pages['7'] = "<span class='Pline'>" + str(self.__FO) + \
            str(self.__START_NUM) + "-" + \
            str(self.__END_NUM) + str(self.__LINE) + "</span>"

        pages['8'] = "<span class='Pcount'>" + str(self.__COUNT_START) + \
            str(self.__COUNT_ROW) + str(self.__COUNT_END) + "</span>"

        retuls = '<div>'
        for value in keys:
            retuls += pages[value]
        retuls += '</div>'

        return retuls

    def __GetEnd(self):
        endStr = ""
        if self.__C_PAGE >= self.__COUNT_PAGE:
            endStr = ''
        else:
            if self.__RTURN_JS == "":
                endStr = "<a class='Pend' href='" + self.__URI + "p=" + \
                    str(self.__COUNT_PAGE) + "'>" + str(self.__END) + "</a>"
            else:
                endStr = "<a class='Pend' onclick='" + self.__RTURN_JS + \
                    "(" + str(self.__COUNT_PAGE) + ")'>" + \
                    str(self.__END) + "</a>"
        return endStr

    def __GetNext(self):
        nextStr = ""
        if self.__C_PAGE >= self.__COUNT_PAGE:
            nextStr = ''
        else:
            if self.__RTURN_JS == "":
                nextStr = "<a class='Pnext' href='" + self.__URI + "p=" + \
                    str(self.__C_PAGE + 1) + "'>" + str(self.__NEXT) + "</a>"
            else:
                nextStr = "<a class='Pnext' onclick='" + self.__RTURN_JS + \
                    "(" + str(self.__C_PAGE + 1) + ")'>" + \
                    str(self.__NEXT) + "</a>"

        return nextStr

    def __GetPages(self):
        pages = ''
        num = 0
        if (self.__COUNT_PAGE - self.__C_PAGE) < self.__LIST_NUM:
            num = self.__LIST_NUM + \
                (self.__LIST_NUM - (self.__COUNT_PAGE - self.__C_PAGE))
        else:
            num = self.__LIST_NUM
        n = 0
        for i in range(num):
            n = num - i
            page = self.__C_PAGE - n
            if page > 0:
                if self.__RTURN_JS == "":
                    pages += "<a class='Pnum' href='" + self.__URI + \
                        "p=" + str(page) + "'>" + str(page) + "</a>"
                else:
                    pages += "<a class='Pnum' onclick='" + self.__RTURN_JS + \
                        "(" + str(page) + ")'>" + str(page) + "</a>"

        if self.__C_PAGE > 0:
            pages += "<span class='Pcurrent'>" + \
                str(self.__C_PAGE) + "</span>"

        if self.__C_PAGE <= self.__LIST_NUM:
            num = self.__LIST_NUM + (self.__LIST_NUM - self.__C_PAGE) + 1
        else:
            num = self.__LIST_NUM
        for i in range(num):
            if i == 0:
                continue
            page = self.__C_PAGE + i
            if page > self.__COUNT_PAGE:
                break
            if self.__RTURN_JS == "":
                pages += "<a class='Pnum' href='" + self.__URI + \
                    "p=" + str(page) + "'>" + str(page) + "</a>"
            else:
                pages += "<a class='Pnum' onclick='" + self.__RTURN_JS + \
                    "(" + str(page) + ")'>" + str(page) + "</a>"

        return pages

    def __GetPrev(self):
        startStr = ''
        if self.__C_PAGE == 1:
            startStr = ''
        else:
            if self.__RTURN_JS == "":
                startStr = "<a class='Ppren' href='" + self.__URI + "p=" + \
                    str(self.__C_PAGE - 1) + "'>" + str(self.__PREV) + "</a>"
            else:
                startStr = "<a class='Ppren' onclick='" + self.__RTURN_JS + \
                    "(" + str(self.__C_PAGE - 1) + ")'>" + \
                    str(self.__PREV) + "</a>"
        return startStr

    def __GetStart(self):
        startStr = ''
        if self.__C_PAGE == 1:
            startStr = ''
        else:
            if self.__RTURN_JS == "":
                startStr = "<a class='Pstart' href='" + \
                    self.__URI + "p=1'>" + str(self.__START) + "</a>"
            else:
                startStr = "<a class='Pstart' onclick='" + \
                    self.__RTURN_JS + "(1)'>" + str(self.__START) + "</a>"
        return startStr

    def __GetCpage(self, p):
        if p:
            return p
        return 1

    def __StartRow(self):
        return (self.__C_PAGE - 1) * self.ROW + 1

    def __EndRow(self):
        if self.ROW > self.__COUNT_ROW:
            return self.__COUNT_ROW
        return self.__C_PAGE * self.ROW

    def __GetCountPage(self):
        return int(math.ceil(self.__COUNT_ROW / float(self.ROW)))

    def __SetUri(self, sinput):
        uri = '?'
        for key in sinput:
            if key == 'p':
                continue
            uri += key + '=' + sinput[key] + '&'
        return str(uri)
