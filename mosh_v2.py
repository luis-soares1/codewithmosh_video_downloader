from headers import headers, cookies
from bs4 import BeautifulSoup as bs
import itertools
import os
import requests
import wget

def scrape_course_links() -> list:
    """_summary_
    On the courses tab, scrapes every course link
    Returns:
        list: List of course links -> [/course/enrolled/1, /course/enrolled/2, /course/enrolled/3...]
    """
    course_page_html = requests.get("https://codewithmosh.com/courses/enrolled/240431", cookies=cookies, headers=headers).text
    soup = bs(course_page_html, "html.parser")
    soup.prettify
    #get every link in the webpage and filter only for the course ones
    return [x['href'] for x in soup.find_all("a") if "/courses/enrolled/" in x['href']]

def scrape_class_links(course_links: list):
    """_summary_

    Args:
        course_links (list): _description_

    Returns:
        _type_: Gets every single class link, so we can access each individually and scrape download links
    """
    class_complete_info = {} 
    
    for link in course_links:
        course_classes = requests.get("https://codewithmosh.com" + link, headers=headers, cookies=cookies)
        print("Web page: ", "https://codewithmosh.com" + link, " Status Code: ", course_classes.status_code)
        soup = bs(course_classes.text, "html.parser")
        course_name = soup.find("div", {"class": "course-sidebar"}).find("h2").text if soup.find("div", {"class": "course-sidebar"}) != None else "None"   
        course_name = trim(course_name)

        course_details = parse_chap_class_link(soup=soup)
        class_complete_info[course_name] = course_details
    return class_complete_info


def parse_chap_class_link(soup: str):
    
    chapter_data = {"course_length": 0, "chapters": []}

    #iterate through each row (chapter) element
    for row in soup.find_all("div", {"class": "row"}):
        #course chapters filtered
        f_chapter = row.find("span", {"class": "section-lock v-middle"}).next_sibling.text 
        f_chapter = trim(f_chapter)
        
        #class names filtered
        f_class = [trim(class_n.text) for class_n in row.find_all("span", {"class": "lecture-name"})]
        
        if f_class:
            trim(f_class[0])
        
        #class links
        class_links = [x['href'] for x in row.find_all("a") if "/lectures/" in x['href']]

        chapter_data['chapters'].append({f_chapter : dict(zip(f_class, class_links))})
        chapter_data["course_length"] = chapter_data["course_length"] + len(class_links)
    return chapter_data

def trim(string_to_trim: str):
    """_summary_
        Makes sure there are no invalid chars for creating a folder
    Args:
        string_to_trim (str): _description_

    Returns:
        _type_: a creating-folder-safe string.
    """
    string_to_return = string_to_trim
    for char in '\|/,:;*"<>?.':
        if char in string_to_return:
            string_to_return = string_to_return.replace(char, "")

    return string_to_return.strip()


def extract_download_link(class_link: str):
    """_summary_
    Receives a class link and returns its download(s) link
    Args:
        class_link (str): class_link, i.e. /courses/1522608/lectures/34900536

    Returns:
        _type_: download link for teachable
    """
    soup = bs(requests.get(class_link, cookies=cookies, headers=headers).text, "html.parser")
    return [d_link['href'] for d_link in soup.find_all("a") if "https://cdn.fs.teachablecdn.com/" in d_link['href']]


def video_downloading_chain(course_info):
    """_summary_
        Responsible for the chain of downloading videos 
    Args:
        course_info (_type_): All the information about a course in a dict format. All the chapters and classes and class links.
    """
    for course in course_info:
        create_course_folder(course)
        [chapter_video_downloader(chapter, course) for chapter in course_info[course]['chapters']]
            

def chapter_video_downloader(chapter_dict: dict, course_name: str):
    """_summary
        Creates a folder and downloads an entire chapter from a course.
    Args:
        chapter_dict (dict): A chapter dict containing chapter name, class name and links to the classes (not download links)
        course_name (str): contains course name
    """
    chapter_name = list(chapter_dict.keys())[0]
    create_chapter_folders(course_name, chapter_name)
    #goes to a class link, extracts download links and creates a list with with them, which is forwarded to a download lib function below.
    dls = [(extract_download_link("https://codewithmosh.com" + x)) for x in list(chapter_dict[chapter_name].values())]
    
    for dl in flat(dls):
        print("DOWNLOADING... ", f"COURSE NAME: {course_name}", f"CHAPTER NAME: {chapter_name}")
        wget.download(dl, out=os.path.join("/", "Users", os.getlogin(), "Downloads", course_name, chapter_name))


def create_chapter_folders(course_name: str, chapter_name: str):
    """_summary_
        Creates a chapter folder within the course folder. Needs both course name and chapter name.
    Args:
        course_name (str): _description_
        chapter_name (str): _description_
    """
    os.mkdir(os.path.join("/", "Users", os.getlogin(), "Downloads", course_name, chapter_name))


def create_course_folder(course_name: str):
    """_summary_
        Creates a folder named with the course.
    Args:
        course_name (str): a course name to name the folder
    """
    os.mkdir(os.path.join("/", "Users", os.getlogin(), "Downloads", course_name))

#flat a list of lists
def flat(list_to_flat: list) -> list:
    """flats lists"""
    return list(itertools.chain.from_iterable(list_to_flat))



video_downloading_chain(scrape_class_links(scrape_course_links()))