

import os
import random
from modules.base import Pinterest
from modules.settings import Template1Settings, Template2Settings
from PIL import Image, ImageDraw, ImageFont

class BaseImgGen(Pinterest):

    TEMPLATES = ['template1','template2']
    SUBFOLDER = ['fonts']
    
    
    def __init__(self, projectFolderName,template,width=1000,height=1500,save=True,show=True,writeUploadingData=False) -> None:
        super().__init__(projectFolderName)
        self.template = template
        self.width = width
        self.height = height
        self.save = save
        self.show = show
        self.writeUploadingData = writeUploadingData
        
        self.projectAssetsPath = os.path.join(self.projectPath,'assets')
        self.backgroundPath = os.path.join(self.projectAssetsPath,'backgrounds')
        
        os.makedirs(self.saveImagePath,exist_ok=True)
        os.makedirs(self.backgroundPath,exist_ok=True)
        
        self.imageAssetsPath = os.path.join(self.dataPath,'imageAssets')
        
        for template in self.TEMPLATES:
            templatePath = os.path.join(self.imageAssetsPath,template)
            setattr(self,template,templatePath)

            for subfolder in self.SUBFOLDER:
                subfolderPath = os.path.join(templatePath,subfolder)
                setattr(self,subfolder,subfolderPath)
                os.makedirs(subfolderPath,exist_ok=True)
                
        self.settings = self._getTemplateSettings()
        
        #creates canvas with the attr width and heihgt lol
        self.canvas = Image.new('RGBA',(self.width,self.height))
        
    def _getTemplateSettings(self):
        if self.template == self.GENERATOR_MODE_1:
            return Template1Settings()
        elif self.template == self.GENERATOR_MODE_2:
            return Template2Settings
        else:
            raise ValueError(f"[-] Invalid template mode: {self.template}")
        
    
    def _addGradient(self,gradientColor):
        gradient = Image.new('RGBA',(self.width, self.height),gradientColor)
        alpha = Image.linear_gradient('L').rotate(self.settings.gradient_direction).resize((self.width,self.height))
        gradient.putalpha(alpha)
        self.canvas.alpha_composite(gradient)    
        
    def _fillBackground(self,color):
        draw = ImageDraw.Draw(self.canvas)
        width,height = self.canvas.size
        draw.rectangle((0,0,width,height),fill=color)
    
    def _drawBackground(self):
        if self.settings.overlay_bg:
            bgFiles = self._getBackgroundsFiles(self.backgroundPath)
            if bgFiles:
                bgImgPath = os.path.join(self.backgroundPath,random.choice(bgFiles))
                bgImg = Image.open(bgImgPath).convert('RGBA')
                if self.settings.resize_bg:
                    resizedWdith = self.width
                    resizedHeight = int((resizedWdith/bgImg.width)*bgImg.height)
                    bgImgResized = bgImg.resize((resizedWdith,resizedHeight))
                    self.canvas.paste(bgImgResized,(0,0))
                else:
                    self.canvas.paste(bgImg,(0,0))
                    
                if self.settings.gradient:
                    if self.settings.random_bg_color:
                        randomColor = random.choice(self.settings.random_colors)
                        self._addGradient(randomColor)
                    else:
                        self._addGradient(self.settings.bg_color)
        else:
            if self.settings.random_bg_color:
                randomColor = random.choice(self.settings.random_colors)
                self._fillBackground(randomColor)
            else:
                self._fillBackground(self.settings.bg_color)
    @staticmethod        
    def _wrapText(text,font,maxWidth):
        lines = []
        words = text.split()
        currentLine = words[0]
        
        for word in words[1:]:
            testLine = currentLine + " " + word
            bbox = font.getbbox(testLine)
            
            if bbox[2] - bbox[0] <= maxWidth:
                currentLine = testLine
            else:
                lines.append(currentLine)
                currentLine = word
                
        lines.append(currentLine)
        return '\n'.join(lines)

    
    @staticmethod
    def _getBackgroundsFiles(folderPath):
        return [f for f in os.listdir(folderPath) if os.path.isfile(os.path.join(folderPath,f))]
        
        
    def generateImg(self,data):
        raise NotImplementedError("[+] Subclasses must implement the generateImg method")  
    


class Template1ImgGen(BaseImgGen):
    
    def __init__(self, projectFolderName,width=1000,height=1500,save=True,show=True,writeUploadingData=False) -> None:
        template = self.GENERATOR_MODE_1
        super().__init__(projectFolderName,template,width,height,save,show,writeUploadingData)
        
    def _drawTitle(self,titleText,fontPath,containsLight):
        draw = ImageDraw.Draw(self.canvas)
        font = ImageFont.truetype(fontPath,self.settings.title_font_size)
        wrappedText = self._wrapText(titleText,font,self.settings.title_max_width)
        bbox = draw.multiline_textbbox((0,0),wrappedText,font=font,spacing=self.settings.title_line_spacing)
        
        textWidth = bbox[2]-bbox[0]
        textHeight = bbox[3]-bbox[1]
        
        startY = self.settings.title_margin_from_top
        startX = (self.width - textWidth) // 2
        
        if self.settings.overlay_bg:
            titleFillColor = self.settings.title_text_color_dark if containsLight else self.settings.title_text_color_default
        else:
            titleFillColor = self.settings.title_text_color_default

        draw.text((startX,startY),wrappedText,font=font,fill=titleFillColor,
                  spacing=self.settings.tips_line_spacing,align='center')
        return textHeight
    
    def generateImg(self,data,index):
        
        title = data.get('Title','')
        templatePatch = os.path.join(self.imageAssetsPath,self.template)
        fontPatch = os.path.join(templatePatch, 'fonts')
        titleFontPath = os.path.join(fontPatch,'titleFont.ttf')
        containsLight = self._drawBackground()
        self._drawTitle(title,titleFontPath,containsLight)
        
        imgs = [f for f in os.listdir(self.temuTemps) if f.endswith(".jpg")or f.endswith(".png")]
        img = imgs[index]
        imgPath = os.path.join(self.temuTemps,img)
        imgTemu = Image.open(imgPath)        
        imgTemu.thumbnail((700,700))
        self.canvas.paste(imgTemu,((1080-imgTemu.width)//2,(1350-imgTemu.height)//2))
        imgName = self.saveImagePath+ "/" + f'PinterestPin_{img.split('.')[0]}.png'
        self.canvas.save(imgName)
    
      
        # self.canvas.show()
        
class Template2ImgGen(BaseImgGen):
    
    def __init__(self, projectFolderName,width=1000,height=1500,save=True,show=True,writeUploadingData=False) -> None:
        template = self.GENERATOR_MODE_2
        super().__init__(projectFolderName,template,width,height,save,show,writeUploadingData)
        
    def generateImg(self,data):
        ...
        