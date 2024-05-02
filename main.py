



import os
import time
from modules.pinner import SeleniumPinner
from modules.base import Pinterest


def uploading(projectFolderName,mode,pins,shuffle,headless,timeout):
    from modules.pinner import RequestPinner

    accounts = [
    ]

    for account in accounts:
        base = Pinterest(account['projectFolderName'])
        dataToUpload = base.openCsv(base.GENERATOR_DATA_FILE)

        if mode == base.UPLOADER_MODE_2:

            # pinner = RequestPinner(**account)
            pinn = SeleniumPinner(**account,headless=headless)
            pinn.login()
            time.sleep(5)
            pinn.upload(dataToUpload,pins=pins,shuffle=shuffle,timeout=timeout)

            print('[+] Done uploading')
            
            
            base._resetPins(base.GENERATOR_DATA_FILE)
            print('[+] Done Formating')
            
        else:
            raise ValueError(f"[-] Invalid mode: {mode}. Check the available modes in the base class.")

def imgGeneration(projectFolder,mode):
    from modules.base import Pinterest
    from modules.imgGen import Template1ImgGen, Template2ImgGen
    #Obtain the data that we'lll feed into the generator
    try:
        base = Pinterest(projectFolderName)
        # print(base.GENERATOR_DATA_FILE)
        data = base.openCsv(base.GENERATOR_DATA_FILE)

        commonParams = {
            'width':1080,
            'height':1080,
            'save':False,
            'show':True,
            'writeUploadingData':False
        }

        generators = {
            base.GENERATOR_MODE_1: Template1ImgGen,
            base.GENERATOR_MODE_2: Template2ImgGen
        }
        if mode in generators:
            generatorClass = generators[mode]
            generator = generatorClass(projectFolder,**commonParams)

            for i,row in enumerate(data):
                generator.generateImg(row,i)

    except Exception as e:
        raise ValueError(f"[-] In main.py ImgGeneration function: {e}")

def writing(projectFolderName,googleSheet):
    from modules.writer import Writer

    tableId = '1JcjfIn0ZZsx3KjstPe8ovtMz9YzMzaL7Ww24bQdCqSU'
    writer = Writer(projectFolderName)
    data = writer.openData(googleSheet=googleSheet,tableId=tableId)

    for i,row in enumerate(data):
        writer.write(row)
        writer.downloadImage(row['Imagen'],index=i)

def resetData(projectFolderName):
    base = Pinterest(projectFolderName)
    base._resetPins(base.GENERATOR_DATA_FILE)
    print('[+] Pins formated')
    
    
    
    
if __name__ == '__main__':
    projectFolderName = 'temu'
    pinnerModes = ['requests','selenium']

    choice = input("Enter '1' to run the Writer,\n" "'2' to run the Image Gen, \n" "'3' to run the Pinner,\n '4' to run a reset,\n" )
    match choice:
        case '1':
            writing(projectFolderName,googleSheet=True)
        case '2':
            generatorModes = ['template1','template2']
            imgGeneration(projectFolderName,generatorModes[0])            
        case '3':
            uploading(projectFolderName,mode=pinnerModes[1],pins=10,shuffle=False,headless=False,timeout=(3,8))   
        case '4':
            resetData(projectFolderName)   
        case _:                            
            while True:
                    writing(projectFolderName,googleSheet=True)
                    generatorModes = ['template1','template2']
                    try:
                        imgGeneration(projectFolderName,generatorModes[0]) 
                    except:
                        print('[-] ')
                    finally:
                        uploading(projectFolderName,mode=pinnerModes[1],pins=10,shuffle=False,headless=True,timeout=(3,8))            

