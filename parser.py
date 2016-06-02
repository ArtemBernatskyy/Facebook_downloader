#coding: utf-8
try:
    import sys
    import re
    import os
    import time
    import requests
    from PIL import Image
    from Queue import Queue
    from threading import Thread
    from StringIO import StringIO
    from selenium import webdriver
    import math
    import urllib
    from ConfigParser import SafeConfigParser
except Exception as e:
    print e
    raw_input('press ENTER')
    sys.exit()

reload(sys)
sys.setdefaultencoding("utf-8")



#################### credentials section for Facebook
parser = SafeConfigParser()
parser.read('credentials.txt')
login = parser.get('credentials_facebook', 'login')
password = parser.get('credentials_facebook', 'password')
max_number = int(parser.get('credentials_facebook', 'max_number_per_album'))


if __name__ == "__main__":

    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.cache.disk.enable", False)
    profile.set_preference("browser.cache.memory.enable", False)
    profile.set_preference("browser.cache.offline.enable", False)
    profile.set_preference("network.http.use-cache", False)

    cookies = {}
    baseURL = "http://facebook.com/"
    max_workers = 8


    print '!!!!!!!!!!!!! starting program !!!!!!!!!!'


    class DownloadWorker(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while True:
                link, user_name_or_id = self.queue.get()
                doing = True
                while doing:
                    try:
                        r = requests.get('https://www.facebook.com/photo/download/?fbid=' + link, cookies=cookies)
                        i = Image.open(StringIO(r.content))
                        i.save(os.path.join('data', user_name_or_id, link + '.jpg'))
                        self.queue.task_done()
                        doing = False
                    except Exception as e:
                        # print e
                        pass

    # starting threads for later speed download
    queue = Queue()

    for x in range(max_workers):
        worker = DownloadWorker(queue)
        worker.daemon = True
        worker.start()


    def album_downloader(albumLink, user_name_or_id, facebook_name):
        driver.get(baseURL)
        all_cookies = driver.get_cookies()
        for s_cookie in all_cookies:
            cookies[s_cookie["name"]] = s_cookie["value"]

        # print "[Loading Album]"
        driver.get(albumLink)

        # get album name
        try:
            albumName = driver.find_element_by_class_name("fbPhotoAlbumTitle").text
        except:
            # print "can't get album name"
            pass

        # create album path
        if not os.path.exists(os.path.join('data', facebook_name)):
            os.makedirs(os.path.join('data', facebook_name))
        # print "[Getting Image Links]"
        # scroll to bottom
        previousHeight = 0
        reachedEnd = 0

        while reachedEnd != None:
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            currentHeight = driver.execute_script("return document.body.scrollHeight")
            if previousHeight == currentHeight:
                reachedEnd = None
            previousHeight = currentHeight
            time.sleep(0.6)

        linkImages = driver.execute_script("list = []; Array.prototype.forEach.call(document.querySelectorAll('.uiMediaThumb'), function(el) { var src = el.getAttribute('id'); if(src && src.indexOf('pic_') > -1) list.push(src.split('_')[1]); }); return list;")
        totalImages = len(linkImages)

        # limiting max number of photos
        linkImages = linkImages[:max_number]
        # print "[Found: " + str(len(linkImages)) + "]"
        for fullRes in linkImages:
            queue.put((fullRes, facebook_name))

        # print "[Downloading...]"
        queue.join()




    driver = webdriver.Firefox(profile)
    raw_input('enter something to pass, waiting for entering proxy credentials')


    # login
    driver.get('https://mobile.facebook.com/')
    driver.find_element_by_xpath(
        '/html/body/div/div/div[3]/div/table/tbody/tr/td/div[2]/div/form/ul/li[1]/input').send_keys(login)
    driver.find_element_by_xpath(
        '/html/body/div/div/div[3]/div/table/tbody/tr/td/div[2]/div/form/ul/li[2]/div/input').send_keys(password)
    driver.find_element_by_xpath(
        '/html/body/div/div/div[3]/div/table/tbody/tr/td/div[2]/div/form/ul/li[3]/input').click()
    # print 'waiting 5 seconds'
    time.sleep(5)

    friends_list = []

    driver.get('https://mobile.facebook.com/')
    # getting user home url something like Artem.Wozniak bla bla
    user_url = driver.find_element_by_xpath('/html/body/div/div/div[2]/div/div/a[3]').get_attribute('href').replace('https://mobile.facebook.com/', '').split('?')[0]
    print 'Welcome:', user_url
    # 24 friends per page
    driver.get('https://mobile.facebook.com/'+ str(user_url) +'/friends')
    number_of_friends = re.findall(r'\d+', driver.find_element_by_xpath('/html/body/div/div/div[3]/div/div/div[2]/h3').text)[0]


    def friends_scan():
        # getting friends on the first page
        driver.get('https://mobile.facebook.com/' + str(user_url) + '/friends?startindex=' + str(0))
        time.sleep(1)
        for n in range(1,25):
            try:
                friends_list.append(driver.find_element_by_xpath('/html/body/div/div/div[3]/div/div/div[2]/div[2]/div['+str(n)+']/table/tbody/tr/td[2]/a').get_attribute('href'))
            except Exception as e:
                # print e
                return friends_list

        temp = 24
        # iterating over after first friends page
        for number in range(int(math.ceil((float(number_of_friends)-24)/36))):
            number = number*36 + temp
            driver.get('https://mobile.facebook.com/' + str(user_url) + '/friends?startindex=' + str(number))
            for n in range(1, 37):
                try:
                    friends_list.append(driver.find_element_by_xpath('/html/body/div/div/div[3]/div/div/div[2]/div[' + str(n) + ']/table/tbody/tr/td[2]/a').get_attribute('href'))
                except Exception as e:
                    pass

        return friends_list

    friends_list = friends_scan()

    friends_ids = []

    for friend in friends_list:
        friends_ids.append(str(friend).replace('https://mobile.facebook.com/', '').replace('?fref=fr_tab', '').replace('profile.php?id=', '').replace('&fref=fr_tab', ''))


    # getting friends albums iterating over the friends
    for id in range(len(friends_list)):

        try:
            driver.get(friends_list[id])  # visiting authors page
            name = driver.find_element_by_xpath(
                '/html/body/div/div/div[3]/div/div/div[1]/div[2]/div/div[2]/span[1]/strong').text
            # facebookname = u"".join(x for x in name if x.isalnum())  # safe file name
            facebookname = name.replace(' ', '').replace('.', '')
            try:
                driver.find_element_by_xpath('/html/body/div/div/div[3]/div/div/div[1]/div[4]/a[3]').click()    # entering albums section
                # gettiing facebook name

                albums_list = []

                time.sleep(1)
                # getting albums hrefs
                for i in range(1, 100):
                    try:
                        href = driver.find_element_by_xpath(
                            '/html/body/div/div/div[3]/div/div[2]/div[3]/div/ul/li['+str(i)+']/table/tbody/tr/td/span/a').get_attribute(
                            'href')
                        # converting to desktop version for custom downloader
                        href = str(href).replace('mobile', 'www')
                        albums_list.append(href)
                    except:break


                # getting albums hrefs, facebook is a weird place not for children, here we trying other div ???
                for i in range(1, 100):
                    try:
                        href = driver.find_element_by_xpath(
                            '/html/body/div/div/div[3]/div/div[2]/div[2]/div/ul/li['+str(i)+']/table/tbody/tr/td/span/a').get_attribute(
                            'href')
                        # converting to desktop version for speed up downloader
                        href = str(href).replace('mobile', 'www')
                        albums_list.append(href)
                    except:break


                print 'starting downloading', friends_ids[id], 'photos'

                for album in albums_list:
                    try:
                        album_downloader(album, friends_ids[id], facebookname)
                    except Exception as e:
                        # print e
                        pass
                print '\n'
            except Exception as e:
                # print e
                print "we haven't permission to view albums"
        except Exception as e:
            # print e
            pass
