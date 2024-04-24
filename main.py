
from modules.base import Pinterest
from modules.imgGen import Template1ImgGen, Template2ImgGen

def imgGeneration(projectFolder,mode):
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
    
if __name__ == '__main__':
    projectFolderName = 'temu'
    
    writing(projectFolderName,googleSheet=True)
    generatorModes = ['template1','template2']
    imgGeneration(projectFolderName,generatorModes[0])