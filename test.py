# import requests
# import os

# def downloadImage(url, folder, filename):
#     # Send a GET request to the URL
#     response = requests.get(url)
    
#     # Check if the request was successful (status code 200)
#     if response.status_code == 200:
#         # Create the folder if it doesn't exist
#         os.makedirs(folder, exist_ok=True)
        
#         # Determine the file extension from the URL
#         file_extension = url.split('.')[-1]
        
#         # Construct the file path
#         filepath = os.path.join(folder, f"{filename}.{file_extension}")
        
#         # Open the file in binary write mode and write the content of the response
#         with open(filepath, 'wb') as file:
#             file.write(response.content)
#         print(f"Image downloaded successfully as '{filepath}'")
#     else:
#         print("Failed to download the image")

# # Example usage:
# url = r"https://img.kwcdn.com/product/temu-avi/image-crop/c97126f7-8519-41aa-8a4e-3caa5aa22e62.jpg"
# folder = "images"
# filename = "downloaded_image"
# downloadImage(url, folder, filena
# class Test:
    
#     def __call__(self):
#         print('ola')
 
# a = Test()
# a()
from bs4 import BeautifulSoup
import requests


url = 'https://www.temu.com/affiliate_share_goods.html?_p_rfs=1&query_goods_v2=1&_x_ads_csite=affiliate_seo&_x_sessn_id=72h4moomts&refer_page_name=affiliate_account_activity&refer_page_id=10513_1713288556804_at5ui08a6h&refer_page_sn=10513&is_back=1'
request = requests.get(url)
soup = BeautifulSoup(request.content,features="html.parser")

print(soup)