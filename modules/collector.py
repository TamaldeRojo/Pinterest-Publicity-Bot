import os
from modules.base import Pinterest
from google.oauth2.service_account import Credentials
from bs4 import BeautifulSoup 
import requests

class Collector(Pinterest):
    
    def __init__(self,projectFolderName) -> None:
        super().__init_(projectFolderName)
        
    def __call__(self) -> None:
        ...
    
    def _getGoogleCreds(self):
        jsonKeyPath = os.path.join(self.dataPath,'keyfile.json')
        scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
        
        credentials = Credentials.from_service_account_file(jsonKeyPath,scopes=scopes)
        return credentials
    
    def collectData(self,url):
        request = requests.get(url)
        soup = BeautifulSoup(request.content)
        header = soup.find('h1')
        
    
    def writeData(self,data):
        data = ''
        self.writeCsv(data,self.UPLOADING_DATA_FILE)
    