import csv
import os
import random
from time import sleep

import requests

class Pinterest:
    
    UPLOADING_DATA_FILE = 'uploadingData.csv'
    GENERATOR_DATA_FILE = 'generatorData.csv'
    UPLOADED_FILE = 'uploated.csv'
    
    GENERATOR_MODE_1 = 'template1'
    GENERATOR_MODE_2 = 'template2'
    
    UPLOADER_MODE_1 = 'requests'
    UPLOADER_MODE_2 = 'selenium'
    
    
    def __init__(self,projectFolderName) -> None:
        self.projectPath = os.path.join(os.path.abspath('projects'),projectFolderName)
        # self.promptsPath = os.path.join(self.projectPath,'prompts')
        self.dataPath = os.path.abspath('data')
        
        self.assetsPath = os.path.join(self.projectPath,'assets')
        self.temuTemps = os.path.join(self.assetsPath,'temuTemps')
        self.saveImagePath = os.path.join(self.projectPath,'pinterestPins')

        os.makedirs(self.projectPath,exist_ok=True)
        # os.makedirs(self.promptsPath,exist_ok=True)
        os.makedirs(self.dataPath,exist_ok=True)
        
    @staticmethod  
    def _log_message(message):
        print(message)
        
    @staticmethod  
    def _log_error(message,error):
        redColor = "\033[91m"
        resetColor = "\033[0m"
        
        print(f"{redColor}{message}{resetColor}\n{error}\n")
        
        
    def openCsv(self,filename):
        dataFilePath = self._getDataFilePath(filename)
        if not os.path.exists(dataFilePath):
            raise FileNotFoundError(f"File {filename} not found: {dataFilePath}")
        delimiter = self._checkCsvDelimiter(dataFilePath)
        
        results = []
        with open(dataFilePath,'r',encoding='utf-8',newline='') as data:
            heading = next(data)
            reader = csv.reader(data,delimiter=delimiter)
            if filename == self.GENERATOR_DATA_FILE:
                for row in reader:
                    rowDict = {
                    'Title':row[0],
                    'Desc': row[1],
                    'Img': row[2],
                    'Link' : row[3],
                    'Categoria': row[4]
                    }  
                    results.append(rowDict)
            else:
                rowDict = {
                'Categoria':row[0],
                'Desc': row[1],
                'Imagen': row[2],
                'Link' : row[3]
                }  
                results.append(rowDict)
        return results

    def writeCsv(self,data,filename):
        dataFilePath = self._getDataFilePath(filename)
        uploadingDataHeader = ['Title','Desc','Img',"Link","Categoria"]

        if os.path.isfile(dataFilePath) and os.stat(dataFilePath).st_size == 0:
            self._writeHeader(dataFilePath,uploadingDataHeader)
            
        order = ['title','Desc','Img',"Link","Categoria","filePath","boardName"]
        with open(dataFilePath,'a',encoding='utf-8',newline='') as f:
            writer = csv.DictWriter(f,fieldnames=order,delimiter=';')
            print(data)
            # return
            writer.writerow(data)
        self._log_message(f'Data has been successfully written to {filename}.\n')
            
    def _save_csv(rows_to_save, input_file):
        with open(input_file, 'w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerows(rows_to_save)

    @staticmethod
    def _writeHeader(filePath,header):
        with open(filePath,'a',encoding='utf-8',newline='') as f:
            writer = csv.writer(f,delimiter=';')
            writer.writerow(header)
    
    def _getDataFilePath(self,filename):
        return os.path.join(self.projectPath,filename)

    def downloadImage(self,url, filename):
        response = requests.get(url)
        if response.status_code == 200:
            os.makedirs(self.projectPath+'/imgs', exist_ok=True)
            file_extension = url.split('.')[-1]
            
            filepath = os.path.join(self.projectPath+'/imgs', f"{filename}.{file_extension}")
            
            with open(filepath, 'wb') as file:
                file.write(response.content)
            print(f"[+] Image downloaded successfully as '{filepath}'")
        else:
            print("[-] Failed to download the image")

    @staticmethod
    def _checkCsvDelimiter(filePath):    
        with open(filePath,'r') as file:
            firstLine = file.readline().strip()
            
            if ',' in firstLine:
                return ','
            elif ';' in firstLine:
                return ';'
            else:
                return ','
    
    @staticmethod
    def _random_delay(min_timeout, max_timeout, no_print=False):
        time_out = random.uniform(min_timeout, max_timeout)
        if not no_print:
            print(f'\nTimeout {time_out} seconds...\n')
        sleep(time_out)

    
    def _resetPins(self,rawPath):
        try:
            filepath = os.path.join(self.projectPath,rawPath)
            with open(filepath, 'w', newline='') as csvfile:
                pass  
            print("[+] CSV file emptied successfully.")
            
            
            for element in os.listdir(self.saveImagePath):
                removeImg = os.path.join(self.saveImagePath,element)
                os.remove(removeImg)
            
        except Exception as e:
            print("[-] An error occurred:", e)
