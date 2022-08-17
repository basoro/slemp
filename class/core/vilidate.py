#!/usr/bin/env python
# coding: utf-8

import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class vieCode:
    __fontSize = 20
    __width = 120
    __heigth = 45
    __length = 4
    __draw = None
    __img = None
    __code = None
    __str = None
    __inCurve = True
    __inNoise = True
    __type = 2
    __fontPatn = 'class/fonts/2.ttf'

    def GetCodeImage(self, size=80, length=4):
        '''Get the verification code picture
           @param int size verification code size
           @param int length verification code length
        '''
        self.__length = length
        self.__fontSize = size
        self.__width = self.__fontSize * self.__length
        self.__heigth = int(self.__fontSize * 1.5)

        self.__createCode()
        self.__createImage()
        self.__createNoise()
        self.__printString()
        self.__cerateFilter()

        return self.__img, self.__code

    def __cerateFilter(self):
        '''Obfuscation'''
        self.__img = self.__img.filter(ImageFilter.BLUR)
        filter = ImageFilter.ModeFilter(8)
        self.__img = self.__img.filter(filter)

    def __createCode(self):
        '''Create captcha characters'''
        if not self.__str:
            number = "3456789"
            srcLetter = "qwertyuipasdfghjkzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
            srcUpper = srcLetter.upper()
            if self.__type == 1:
                self.__str = number
            else:
                self.__str = srcLetter + srcUpper + number

        self.__code = random.sample(self.__str, self.__length)

    def __createImage(self):
        '''Create a canvas'''
        bgColor = (random.randint(200, 255), random.randint(
            200, 255), random.randint(200, 255))
        self.__img = Image.new('RGB', (self.__width, self.__heigth), bgColor)
        self.__draw = ImageDraw.Draw(self.__img)

    def __createNoise(self):
        '''Draw distraction points'''
        if not self.__inNoise:
            return
        font = ImageFont.truetype(self.__fontPatn, int(self.__fontSize / 1.5))
        for i in range(5):
            noiseColor = (random.randint(150, 200), random.randint(
                150, 200), random.randint(150, 200))
            putStr = random.sample(self.__str, 2)
            for j in range(2):
                size = (random.randint(-10, self.__width),
                        random.randint(-10, self.__heigth))
                self.__draw.text(size, putStr[j], font=font, fill=noiseColor)
        pass

    def __createCurve(self):
        '''draw interference lines'''
        if not self.__inCurve:
            return
        x = y = 0

        a = random.uniform(1, self.__heigth / 2)
        b = random.uniform(-self.__width / 4, self.__heigth / 4)
        f = random.uniform(-self.__heigth / 4, self.__heigth / 4)
        t = random.uniform(self.__heigth, self.__width * 2)
        xend = random.randint(self.__width / 2, self.__width * 2)
        w = (2 * math.pi) / t

        color = (random.randint(30, 150), random.randint(
            30, 150), random.randint(30, 150))
        for x in range(xend):
            if w != 0:
                for k in range(int(self.__heigth / 10)):
                    y = a * math.sin(w * x + f) + b + self.__heigth / 2
                    i = int(self.__fontSize / 5)
                    while i > 0:
                        px = x + i
                        py = y + i + k
                        self.__draw.point((px, py), color)
                        i -= i

    def __printString(self):
        '''print verification code string'''
        font = ImageFont.truetype(self.__fontPatn, self.__fontSize)
        x = 0
        for i in range(self.__length):
            color = (random.randint(30, 150), random.randint(
                30, 150), random.randint(30, 150))
            x = random.uniform(self.__fontSize * i * 0.95,
                               self.__fontSize * i * 1.1)
            y = self.__fontSize * random.uniform(0.3, 0.5)
            self.__draw.text((x, y), self.__code[i], font=font, fill=color)
