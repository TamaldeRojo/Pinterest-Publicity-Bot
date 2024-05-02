import csv
import json
import mimetypes
import os
import random
import shutil
import time
import uuid


from requests_toolbelt import MultipartEncoder
from modules.base import Pinterest
from py3pin.Pinterest import Pinterest as Py3Pin
import undetected_chromedriver as uc
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException,TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC 


UPLOAD_IMAGE_FILE = 'https://u.pinimg.com/'
VIP_RESOURCE = 'https://www.pinterest.com/resource/VIPResource/get/'

class PinnerBase(Pinterest):
    
    LOGIN_URL = "https://pinterest.com/login"
    UPLOAD_URL = 'https://www.pinterest.com.mx/pin-creation-tool/'
    PIN_IDEA_RESOURCE_CREATE = 'https://www.pinterest.com/resource/ApiResource/create/'
    
    def __init__(self, projectFolderName,email) -> None:
        super().__init__(projectFolderName)
        
        
        self.email = email
        self.cookiesPath = os.path.join(self.dataPath,'cookies')
        self.py3pinCookiesFilePath = os.path.join(self.cookiesPath,self.email)
        self.cookiesFilePath = os.path.join(self.cookiesPath,f"{self.email}.json")
    
    
    
    @staticmethod
    def _cookiesExist(cookiesFilePath):
        return os.path.isfile(cookiesFilePath)
    
    def _loadCookies(self):
        with open(self.cookiesFilePath,'r') as f:
            cookies = json.load(f)
        return cookies
    
    def _saveCookies(self,cookies):
        with open(self.cookiesFilePath,'w') as f:
            json.dump(cookies,f)

    def _setDriver(self,useragent,proxy,headless):
        chromeOptions = uc.ChromeOptions()
        chromeOptions.headless = headless
        chromeOptions.add_argument('--lang=en')
        
        chromeOptions.add_experimental_option("prefs",{"credentials_enable_service": False,"profile.default_content_setting_values.notifications" : 2})
        
        if useragent:
            chromeOptions.add_argument(f'user-agent={useragent}')
        
        if proxy and self._formatProxy(proxy):
            proxyOptions = {
                'proxy':{
                    'http':proxy,
                    'https':proxy,
                    'no_proxy':'localhost:127.0.0.1'
                }
            }
        else:
            proxyOptions = None
            
        driver = uc.Chrome(options=chromeOptions,seleniumwire_options=proxyOptions)
        
        return driver
        
    def _formatProxy(self,proxyString):
        try:
            parts = proxyString.split(':')
            
            if not proxyString.lower().startswith("http://") and not proxyString.lower().startswith("socket5://"):
                self._log_message('[-] Incorrect proxy scheme, It should be http or sock5.')
                return None
            
            if len(parts) not in (4,2):
                self._log_message('[-] Incorrect proxy format. Use the format: http://username:password@proxy ip:proxy port')
                return None
            
            if len(parts) == 4:
                if '@' not in parts[2]:
                    self._log_message('[-] Incorrect proxy format. Use the format: http://username:password@proxy ip:proxy port')
                    return None
            proxyType = parts[0].lower()
            proxyDict = { proxyType: proxyString}
            return proxyDict
        except Exception as e:
            self._log_error(f"[-] Error while forming proxy dictionary: {e}")
            return None
    
    
    def _registerMediaUploadBatch(self,uuid1,uuid2=None,duration=None):
        
        mediaInfoList = '[{"id":"' +uuid1+ '","media_type:"image-story-pin"},{"id:"'+uuid2+'","media_type":"image-story-pin"}]'
        
        data = {
            'source_url':"/pin-creation-tool/",
            'data': json.dumps({
                "options": {
                    "url":"/v3/media/uploads/register/batch/",
                    "data":{
                        "media_info_list": mediaInfoList
                    }
                },
                "context": {}
            })
        }
        return self.post(url=self.PIN_IDEA_RESOURCE_CREATE, data=data)
    
    def _validate_upload_data(self, uploading_data, pins):
        if len(uploading_data) < pins:
            pins = len(uploading_data)
            self._log_message(f'The specified number of Pins exceeds the number of rows in the data table.\n'
                              f'{pins} Pins will be pinned.\n')
        return uploading_data[:pins]
    
    
    def _create_uploading_data(self, data, random_boards, global_link):
        # random_board = self._get_random_board(random_boards)

        return UploadingData(
            # file_path=data.get('file_path', ''),
            # board_name=random_board if random_board else data.get('board_name', ''),
            # hashtag=data.get('keyword', ''),
            pin_title=data.get('Title', ''),
            pin_description=data.get('Desc', ''),
            pin_link=global_link if global_link else data.get('Link', ''),
            # mode=data.get('mode', ''),
            keyword=data.get('Categoria', '')
        )
        
    @staticmethod    
    def _check_csv_delimiter(file_path):
        # Open the file in read mode
        with open(file_path, 'r') as file:
            # Read the first line and remove leading/trailing whitespaces
            first_line = file.readline().strip()

            # Check for the presence of a comma (',') as the delimiter
            if ',' in first_line:
                return ','
            # Check for the presence of a semicolon (';') as the delimiter
            elif ';' in first_line:
                return ';'
            # If neither comma nor semicolon is found, default to comma
            else:
                 return ','
    
    
    def _after_success_pin(self, file_path):
        try:
            input_file = os.path.join(self.projectPath, self.GENERATOR_DATA_FILE)
            output_file = os.path.join(self.projectPath, self.UPLOADED_FILE)

            rows_to_save = self._process_csv(file_path, input_file, output_file)

            self._save_csv(rows_to_save, input_file)
            self._log_message('[+] The uploaded Pin data has been moved to the uploaded.csv file.')

            self._move_uploaded_file(file_path)
        except:
            print('An exception occurred')
    
    
    def _move_uploaded_file(self, file_path):
        destination_file_path = os.path.join(self.pinned_path, os.path.basename(file_path))
        if os.path.exists(destination_file_path):
            os.remove(destination_file_path)
        shutil.move(file_path, self.pinned_path)
        
    def _process_csv(self, file_path, input_file, output_file):
        rows_to_save = []

        delimiter = self._check_csv_delimiter(input_file)

        with open(input_file, 'r', newline="") as file:
            reader = csv.reader(file, delimiter=delimiter)
            headers = next(reader)
            rows_to_save.append(headers)

            for row in reader:
                if row[4] == file_path:
                    with open(output_file, 'a', newline='') as out_file:
                        writer = csv.writer(out_file, delimiter=';')
                        writer.writerow(row)

                    # or
                    # self.write_csv(row, self.UPLOADED_FILE)
                else:
                    rows_to_save.append(row)

        return rows_to_save
    
    def _updateCookies(self,cookies):
        self.http.cookies.clear()
        for cookie in cookies:
            self.http.cookies.set(cookie["name"], cookie["value"])

        self.registry.update_all(self.http.cookies.get_dict())
    

    
    
class RequestPinner(PinnerBase,Py3Pin):
    def __init__(self, projectFolderName, email="",password="",username="",user_agent=None,proxies=None,randomBoards='',globalLink='') -> None:
        super().__init__(projectFolderName,email)
        formattedProxy = self._formatProxy(proxies) if proxies else None
        Py3Pin.__init__(self,
            email=email,
            password=password,
            username=username,
            user_agent=user_agent if user_agent else None,
            proxies=formattedProxy,
            cred_root="data/cookies",
            )
        
        self.email = email
        self.username = username
        self.proxy = proxies
        self.userAgent = user_agent
        self.randomBoards = randomBoards
        self.globalLink = globalLink
        
        
    
    def login(self, headless=True, wait_time=15, proxy=None, lang="en"):
        
        # driver = self._setDriver(self.userAgent,self.proxy,headless)
        if not self._cookiesExist(self.py3pinCookiesFilePath):
            driver = self._setDriver(self.userAgent,self.proxy,headless)
            try:
                
                wait = WebDriverWait(driver,wait_time)
                
                driver.get(self.LOGIN_URL)
                inputEmail = wait.until(EC.element_to_be_clickable((By.ID,'email')))
                inputEmail.send_keys(self.email)
                
                inputPassword = driver.find_element(By.ID,'password')
                inputPassword.send_keys(self.password)
                
                #/html/body/div[1]/div/div[1]/div/div/div/div[3]/div/div/div[3]/form/div[7]/button/div/div/div
                loginBtn = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/div/div/div/div[3]/div/div/div[3]/form/div[7]/button/div/div/div[contains(text(), 'Log in')]")
                loginBtn.click()
                print("[+] Logged In")
                
                wait.until(EC.invisibility_of_element_located((By.ID,'email')))
                
                driver.get(self.UPLOAD_URL)

                cookies = driver.get_cookies()
                print("[+] -- : ",cookies)
                self._saveCookies(cookies)
                self._updateCookies(cookies)
                
                
            except Exception as e:
                self._log_error(f"[-] Login error: {e}",e)
            finally:
                print('[+] Finally Statement')
                driver.close()
                
    
    
    @staticmethod
    def _generate_uuid():
        # Generate a random UUID
        generated_uuid = uuid.uuid4()
        # Formatting the UUID into the desired format
        formatted_uuid = '-'.join(
            [str(generated_uuid)[:8], str(generated_uuid)[9:13], str(generated_uuid)[14:18], str(generated_uuid)[19:23],
             str(generated_uuid)[24:]])
        return formatted_uuid
    
    @staticmethod
    def _extractDataFromResponse(json_response, file_uuid):
        # Extracting upload data corresponding to the specified file_uuid from the JSON response
        upload_data = json_response['resource_response']['data'].get(file_uuid, {})

        # Extracting required parameters from the upload_data dictionary
        extracted_data = {
            'x-amz-date': upload_data.get('upload_parameters', {})['x-amz-date'],
            'x-amz-signature': upload_data.get('upload_parameters', {})['x-amz-signature'],
            'x-amz-security-token': upload_data.get('upload_parameters', {})['x-amz-security-token'],
            'x-amz-algorithm': upload_data.get('upload_parameters', {})['x-amz-algorithm'],
            'key': upload_data.get('upload_parameters', {})['key'],
            'policy': upload_data.get('upload_parameters', {})['policy'],
            'x-amz-credential': upload_data.get('upload_parameters', {})['x-amz-credential'],
            'Content-Type': 'multipart/form-data',
        }

        # Returning the extracted data dictionary
        return extracted_data


    @staticmethod
    def _delete_file(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file '{file_path}': {e}")


    def _confirm_uploading(self, upload_id):
        options = {
            "upload_ids": [upload_id],
        }

        source_url = '/pin-creation-tool/'

        url = self.req_builder.buildGet(url=VIP_RESOURCE, options=options, source_url=source_url)

        return self.get(url=url).json()
    
    def _pinterestMediaUpload(self, file_path, data):
        file_name = os.path.basename(file_path)
        mime_type = mimetypes.guess_type(file_path)[0]

        with open(file_path, 'rb') as file:
            form_data = MultipartEncoder(
                fields={
                    **data,
                    "file": (file_name, file, mime_type),  
                }
            )

            headers = {
                'Accept': '*/*',
                "Content-Length": str(form_data.len),
                "Content-Type": form_data.content_type,
            }

           
            return self.post(url=UPLOAD_IMAGE_FILE,data=form_data, headers=headers)
    

    def upload(self, uploadingData, pins=10,shuffle=False,timeout=(0,3),emoji=True,moveDataAfterUpload=True):
        if shuffle:
            random.shuffle(uploadingData)
        uploadingData = self._validate_upload_data(uploadingData,pins)
 
        for i, elem in enumerate(uploadingData, start=1):
            pin_data = self._create_uploading_data(elem, self.randomBoards, self.globalLink)

            board = pin_data.board_name

            try:
                self.upload_pin(board_id=board,
                                image_file=pin_data.file_path,
                                description=self._prepare_emoji(
                                    pin_data.pin_description) if emoji else pin_data.pin_description,
                                title=self._prepare_emoji(pin_data.pin_title) if emoji else pin_data.pin_title,
                                link=pin_data.pin_link)
                self._log_message(f'[+] {i} Image pin created')

                # Move data after successful upload if enabled
                if moveDataAfterUpload:
                    self._after_success_pin(pin_data.file_path)
            except Exception as e:
                self._log_error('[-] An error occurred while creating image pin.', e)

            if i != len(uploadingData):
                delay_min, delay_max = timeout
                self._random_delay(delay_min, delay_max)
                
                
                
   
class SeleniumPinner(PinnerBase):
    def __init__(self, projectFolderName='', email='',password='',username='',user_agent=None,randomBoards='',globalLink='',proxy=None,headless=True) -> None:
        super().__init__(projectFolderName, email)
        self.email = email
        self.password = password
        self.randomBoards = randomBoards
        self.globalLink = globalLink
        self.driver = self._setDriver(user_agent,proxy,headless=headless)
        
    def _waitForElementLocated(self,by,value,timeout=15):
        try:
            element = WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located((by,value)))
            return element
        except TimeoutException:
            raise NoSuchElementException(f"[-] Element not found: {by}={value}")
        
    def _waitForElementClickable(self,by,value,timeout=15):
        try:
            element = WebDriverWait(self.driver,timeout).until(EC.element_to_be_clickable((by,value)))
            return element
        except TimeoutException:
            raise NoSuchElementException(f"[-] Element not found: {by}={value}")

    def _waitForElementInvisiable(self,by,value,timeout=15):
        try:
            element = WebDriverWait(self.driver,timeout).until(EC.invisibility_of_element((by,value)))
            return element
        except:
            self._log_message('[-] Element did not disappear within the specified timeout')                
            
    def login(self, headless=True, wait_time=15):
        
        if not self._cookiesExist(self.py3pinCookiesFilePath):
            # driver = self._setDriver(self.userAgent,self.proxy,headless)
            driver = self.driver
            try:
                
                wait = WebDriverWait(driver,wait_time)
                
                driver.get(self.LOGIN_URL)
                inputEmail = wait.until(EC.element_to_be_clickable((By.ID,'email')))
                inputEmail.send_keys(self.email)
                
                inputPassword = driver.find_element(By.ID,'password')
                inputPassword.send_keys(self.password)
                
                #/html/body/div[1]/div/div[1]/div/div/div/div[3]/div/div/div[3]/form/div[7]/button/div/div/div
                loginBtn = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/div/div/div/div[3]/div/div/div[3]/form/div[7]/button/div/div/div[contains(text(), 'Log in')]")
                loginBtn.click()
                print("[+] Logged In")
                
                wait.until(EC.invisibility_of_element_located((By.ID,'email')))
                self.driver.refresh()
                driver.get(self.UPLOAD_URL)

                cookies = driver.get_cookies()
                # print("[+] -- : ",cookies)
                self._saveCookies(cookies)
                # self._updateCookies(cookies)
                
                
            except Exception as e:
                self._log_error(f"[-] Login error: {e}",e)
        else:
            self._log_message('Cookies found. Logging into the account with the cookies...')

            cookies = self._load_cookies()

            self.driver.get(self.LOGIN_URL)
            for cookie in cookies:
                self.driver.add_cookie(cookie)

            self.driver.refresh()
        
 

    def _input_title(self, title, wait_time, max_attempts=5):
        attempt = 0
        while attempt < max_attempts:
            try:
                title_box = self._waitForElementClickable(By.CSS_SELECTOR, 'input[id="storyboard-selector-title"]',
                                                           wait_time)
                title_box.send_keys(title)
                break
            except StaleElementReferenceException:
                self._log_message("[+] StaleElementReferenceException occurred. Retrying...")
                attempt += 1
        else:
            raise Exception("[-] Failed to input title after multiple attempts.")

    def _input_description(self, description, max_attempts=5):
        attempt = 0
        while attempt < max_attempts:
            try:
                text_div = self.driver.find_element(By.XPATH, '//div[@aria-autocomplete="list"]')
                text_div.clear()
                text_div.send_keys(description)
                text_div.send_keys(Keys.ENTER)
                break
            except StaleElementReferenceException:
                self._log_message("[+] StaleElementReferenceException occurred. Retrying...")
                attempt += 1
        else:
            raise Exception("[-] Failed to input description after multiple attempts.")

    def _input_link(self, link):
        link_box = self.driver.find_element(By.ID, "WebsiteField")
        link_box.send_keys(link)

    def _inputKeywords(self,keyword):
        linkBox = self.driver.find_element(By.ID,'storyboard-selector-interest-tags')
        linkBox.send_keys(keyword)
        linkBox.send_keys(Keys.ENTER)
        
    def _input_board(self, board):
        dropdown_menu = self.driver.find_element(By.CSS_SELECTOR, 'button[data-test-id="board-dropdown-select-button"]')
        dropdown_menu.click()
        search_field = self._waitForElementClickable(By.ID, 'pickerSearchField')
        search_field.send_keys(board)
        board_element = self._waitForElementClickable(By.CSS_SELECTOR, 'div[data-test-id*="board-row"]')
        board_element.click()

    def _dragImage(self, imgPath, wait_time):
        print('[+] in progress')
        time.sleep(4)
        #/html/body/div[1]/div/div[1]/div/div[2]/div/div/div/div[2]/div[3]/div/div/div[3]/div/div/div[1]/div/div/div[1]/div/input
        upload_area = self._waitForElementLocated(By.ID, "storyboard-upload-input",wait_time)
        print('[+] Almost done')
        currentImgPath = os.path.join(self.saveImagePath,imgPath[0]) 
        upload_area.send_keys(currentImgPath)

    def _upload_pin(self, uploading_data,index, wait_time=15):
        # print('INDEX---- ',index-1)
        file_path = [pin for pin in os.listdir(self.saveImagePath) if int(pin.split("_")[1]) == index-1]
        # print("INDEX----",file_path)
        title = uploading_data.pin_title
        link = uploading_data.pin_link
        
        self.driver.get(self.UPLOAD_URL)
        
        rawKeywords = uploading_data.keyword
        keywords = rawKeywords.split(',')
        
        keywords2Desc = ''
        for i,k in enumerate(keywords):
            keywords2Desc = keywords2Desc + ' #'+ keywords[i]
                    
        description = uploading_data.pin_description + f" ---> {link} {keywords2Desc}"
        
        
        print(self.UPLOAD_URL)
        time.sleep(3)
        self._log_message('Uploading the pin...')
        self._dragImage(file_path, wait_time)

        self._log_message('Entering the title...')
        self._input_title(title, wait_time, 5)

        self._log_message('Entering the description...')
        self._input_description(description, 5)

        if link:
            self._log_message('Entering the link...')
            self._input_link(link)

        self._log_message('Entering Keywords...')
        self._inputKeywords(keywords[0])
        
        self.driver.find_element(By.XPATH,'/html/body/div[1]/div/div[1]/div/div[2]/div/div/div/div[2]/div[3]/div/div/div[3]')
        time.sleep(4)
        publishBtn = self._waitForElementClickable(By.XPATH,'/html/body/div[1]/div/div[1]/div/div[2]/div/div/div/div[2]/div[3]/div/div/div[2]/div[4]/div[2]/div/button')
        publishBtn.click()
        self._log_message('Waiting for the upload to complete...')

        time.sleep(10)

    def upload(self, uploading_data, pins=10, shuffle=False, timeout=(3, 8), move_data_after_upload=True):
        if shuffle:
            random.shuffle(uploading_data)

        uploading_data = self._validate_upload_data(uploading_data, pins)

        for i, elem in enumerate(uploading_data, start=1):
            pin_data = self._create_uploading_data(elem, self.randomBoards, self.globalLink)

            try:
                self._upload_pin(pin_data,index=i, wait_time=120)
                self._log_message(f'{i} Pin created')

                if move_data_after_upload:
                    self._after_success_pin(pin_data.file_path)
            except Exception as e:
                self._log_error('An error occurred while creating pin.', e)

            if i != len(uploading_data):
                delay_min, delay_max = timeout
                self._random_delay(delay_min, delay_max)

        self.driver.close()




class UploadingData:
    def __init__(self, file_path='', board_name='', hashtag='', pin_title='', pin_description='',
                 pin_link='', mode='', keyword=''):
        self.file_path = file_path
        self.board_name = board_name
        self._hashtag = self._prepare_hashtags(hashtag)
        self.pin_title = self._truncate_text(pin_title, 95)
        self.pin_description = self._prepare_description(pin_description, self._hashtag, 495, 400)
        self.pin_link = pin_link
        self.mode = mode
        self.keyword = keyword

    @staticmethod
    def _truncate_text(text, max_length):
        if len(text) <= max_length:
            return text
        else:
            return text[:max_length]

    @staticmethod
    def _prepare_hashtags(input_string):
        if not input_string:
            return ""

        if ',' in input_string:
            hashtags = input_string.split(',')
        else:
            hashtags = input_string.split()

        hashtags = [tag.strip().capitalize() for tag in hashtags]
        hashtags = ['#' + tag if not tag.startswith('#') else tag for tag in hashtags]
        result_string = ' '.join(hashtags)

        first_hashtag = '#' + ''.join(word.capitalize() for word in input_string.split())

        return f'{first_hashtag} {result_string}'

    @staticmethod
    def _prepare_description(description, hashtags, max_length, min_length_description):
        if len(description) + len(hashtags) <= max_length:
            return f'{description} {hashtags}'

        if len(description) > min_length_description:
            new_description = description[:min_length_description]
        else:
            remaining_space = max_length - len(hashtags)
            new_description = description[:remaining_space]

        if len(new_description) + len(hashtags) <= max_length:
            return f'{new_description} {hashtags}'
        else:
            remaining_space = max_length - len(new_description)
            new_hashtags = hashtags[:remaining_space]
            return f'{new_description} {new_hashtags}'
         