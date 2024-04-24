import os
import requests
import gspread
from modules.base import Pinterest
from google.oauth2.service_account import Credentials
import g4f

class Writer(Pinterest):
    def __init__(self, projectFolderName) -> None:
        super().__init__(projectFolderName)
        
    def openData(self,googleSheet=True,tableId=None):
        if googleSheet:
            self._log_message(f"[+] GoogleSheet On. . .")

            creds = self._getGoogleCreds()
            client = gspread.authorize(creds)
            table = client.open_by_key(tableId)
            
            worksheet = table.get_worksheet(0)
             
            allValues = worksheet.get_all_values()
            data = self._parseRows(allValues)
            
        else:
            self._log_message(f"[+] GoogleSheet Off then csv. . .")
            filename = self.UPLOADING_DATA_FILE
            data = self.openCsv(filename)
            print(data)
        return data
    
    @staticmethod
    def _parseRows(rows):
        data = []
        
        for i,row in enumerate(rows):
            if i == 0:
                continue            
            rowDict = {
                'Categoria':row[0],
                'Desc': row[1],
                'Imagen': row[2],
                'Link' : row[3]
            }   
            data.append(rowDict)
        return data
    
    def _getGoogleCreds(self):
        jsonKeyPath = os.path.join(self.dataPath,'keyfile.json')
        scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
        
        credentials = Credentials.from_service_account_file(jsonKeyPath,scopes=scopes)
        return credentials
    
    
    def writeSinglePrompt(self,prompt):
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_35_turbo,
            messages=[{'role':'user','content':prompt}]
        )
        return response
    
    def downloadImage(self,url,index):
        res = requests.get(url)
        filename = os.path.join(self.temuTemps,str(index) + '_'+url.split('/')[-1])
        if res.status_code == 200:
            with open(filename,'wb') as f:
                f.write(res.content)
            print(f'[+] Image downloaded and saved as {filename.split('/')[-1]}')
        else:
            print('[-] Failed to download image numer: {index} ')
            
    def write(self,row):
        
        results = {
            "filePath":'',
            'boardName':'',
            'Link':''
        }
    
        try:
            self._log_message('[+] Writing prompted title...')
            tempToPrompt = results['Desc'] = row.get('Desc')
            prompt = f"Crea un titulo llamativo simple de esta descripcion: {tempToPrompt} "
            title = self.writeSinglePrompt(prompt)
            results['title'] = title.strip('"') if title else ''
            
            self._log_message('[+] Writing img...')
            results['Img'] = row.get('Imagen')
            
            self._log_message('[+] Writing Link...')
            results['Link'] = row.get('Link')
            
            self._log_message('[+] Writing Categoria...')
            results['Categoria'] = row.get('Categoria')
            
            
            
        except Exception as e:
          print(f'An exception occurred {e}')
        filename = self.GENERATOR_DATA_FILE
        
        self.writeCsv(results,filename)
    