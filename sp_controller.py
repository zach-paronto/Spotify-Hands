from selenium import webdriver 
from selenium.webdriver import Keys, ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
#sleep statements added for testing; may remove and replace with another method to ensure functions are not rapidly called

class SPController():
    def login(self, username, password):
        self.driver.get("https://accounts.spotify.com/login?login_hint=" + username + "&allow_password=1")

        self.driver.find_element("xpath", "/html/body/div[1]/div/div/div/div/div[2]/div[1]/div[2]/div[2]/input").send_keys(password)
        self.driver.find_element("xpath", "/html/body/div[1]/div/div/div/div/div[2]/div[2]/button").click()

        #open the interactive web player page
        self.driver.find_element("xpath", "/html/body/div/div/div/div/div/button[2]").click()
        self.player_body = self.driver.find_element("xpath", "/html/body")

    def pause_play(self):
        self.player_body.send_keys(" ")
        time.sleep(1)

    #TODO: doesn't work if the web browser is used while a desktop app is playing the song
    #does work in the browser
    #an image is sent whenever a NEW song is laoded. It may be easy enough to simply wait until a request for that file type is sent/received
    #since we don't know for sure how long this request will take to send, it's probably not a good method
    #instead, we may be able to pause the playback, get the current song, issue the chain, check if the span has changed, then maybe issue another chain
    def rewind(self):
        current_song = self.driver.find_element("xpath", "/html/body/span").text
        if(current_song == "Advertisement"):
            return
        ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.LEFT).key_up(Keys.CONTROL).key_up(Keys.LEFT).perform()
        
        #web-player controlling a desktop app is causing issues bc of inherent delays
        new_song = self.driver.find_element("xpath", "/html/body/span").text
        while( (new_song == current_song) and (new_song != "Advertisement") ):
            ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.LEFT).key_up(Keys.CONTROL).key_up(Keys.LEFT).perform()
            #some form of waiting is necessary in the event that the web-player of spotify controls a separate spotify player
            # else the loop will rapidly invoke ActionChains, causing undefined behavior 
            time.sleep(1) 
            new_song = self.driver.find_element("xpath", "/html/body/span").text
        print(current_song + " : " + new_song)
        time.sleep(1)

    def skip(self):
        ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.RIGHT).key_up(Keys.CONTROL).key_up(Keys.RIGHT).perform()
        time.sleep(1)


    def __init__(self, username, password):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.login(username, password)