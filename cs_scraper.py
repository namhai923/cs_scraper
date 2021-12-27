import os, time, re, json
import pdfplumber
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

download_path = 'C:\courses_description' #Change download location here

chrome_options = Options()
chrome_options.add_experimental_option('prefs', {
  'download.default_directory': download_path,
  'download.prompt_for_download': False, #To auto download the file
  'download.directory_upgrade': True,
  'plugins.always_open_pdf_externally': True #It will not show PDF directly in chrome
})

s = Service('C:\Program Files (x86)\chromedriver.exe')
driver = webdriver.Chrome(service=s, chrome_options=chrome_options)

def scraper():
  pdf_links = []
  driver.get('https://sci.umanitoba.ca/cs/courses-2/')
  years = [1, 2, 3, 4]
  for year in years:
    if year != 1:
      button = driver.find_element(By.ID, f'tab-1{year}')
      button.click()
    try:
      course_panel = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, f'panel-1{year}'))
      )
      courses = course_panel.find_elements(By.CSS_SELECTOR, '.course-label.course')
      for course in courses:
        course_link = course.find_element(By.TAG_NAME, 'a').get_attribute('href')
        pdf_links.append(course_link)
    except Exception as e:
      print(e)
  return pdf_links

def download():
  links = scraper()
  for link in links:
    driver.get(link)
  time.sleep(1)
  download_finish = False
  while not download_finish:
    download_finish = not any([filename.endswith('.crdownload') for filename in os.listdir(download_path)])
  driver.close()

def get_text(file_path):
  pdf = pdfplumber.open(file_path)
  whole_text = []
  for page_num in range(0, len(pdf.pages)):
    page_text = pdf.pages[page_num].extract_text()
    page_text = [line.strip() for line in page_text.split('\n') if line.strip() != '']
    whole_text += page_text
  return whole_text

def split_content(file_content, attributes):
  contents = []
  line_num = 0
  while line_num < len(file_content):
    for title in attributes:
      words = title.split(' ')
      if line_num < len(file_content):
        if all(re.search(word, file_content[line_num], re.IGNORECASE) for word in words):
          title_content = ''
          while line_num < len(file_content):
            if title != attributes[-1]:
              next_title = attributes[attributes.index(title) + 1]
              words = next_title.split(' ')
              if all(re.search(word, file_content[line_num], re.IGNORECASE) for word in words):
                break
            title_content += file_content[line_num] + ' '
            line_num += 1
          contents.append(title_content)     
    line_num += 1
  return contents

def get_course_data(file_path):
  file_content = get_text(file_path)
  attributes = ['Calendar Description', 'Prerequisite', 'Outline']
  course_title = file_content[0]
  course_data = dict()
  course_data[course_title] = {}
  attribute_content = split_content(file_content, attributes)
  for attribute in attributes:
    words = attribute.split(' ')
    for content in attribute_content:
      if all(re.search(word, content, re.IGNORECASE) for word in words):
        match = re.search(words[-1], content, re.IGNORECASE)
        course_data[course_title][attribute] = content[(match.end() + 1):].strip()
  return course_data

def pdf_extract():
  output_data = {}
  for filename in os.listdir(download_path):
    file_path = download_path + f'\{filename}'
    course_data = get_course_data(file_path)
    output_data.update(course_data)
  with open('courses_description.json', 'w') as output_file:
    json.dump(output_data, output_file, indent=2)

def main():
  download()
  pdf_extract()

if __name__ == '__main__':
  main()