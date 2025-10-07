from patchright.async_api import Page
from langchain_core.tools import tool


def make_tools(page:Page):

    @tool
    async def search_google(query):
        """
        Arugument should be a python list [] with the string you want to search in google 
        ex: ["youtube"], ["laptop amazon"], ["reddit what is the best watch"], etc
        Use this function only when you are on google search and not any other website
        """
        return 0
    
    @tool 
    async def search_website(query):
        """
        Arguemnt should be a python list [] with the thing you want to search on websites
        ex: ["rtx 5050 laptops"], ["how to solve segmentation fault"], ["phone forums"], etc. NOT A LIST IN A LIST
        Use this function only when on websites like amazon, stackoverflow, flipkart , etc and not google search
        """
    
    @tool
    async def get_google_page_links():
        """
        Takes no arguments
        you will get all the links from the google search page,
        cannot be used anywhere except for getting links from google search pages
        """
        return 0
    
    @tool
    async def goto_link(URL):
        """
        the argument should be a python list with the url you want to visit
        ex ["https://www.amazon.in/"], ["www.flipkart.com"], ["www.youtube.com"] etc
        Use this function to go to links, only one link at a time is allowed
        """
        return 0
    
    @tool 
    async def get_page_text():
        """
        This function takes no arguments
        It will extract all the text from the page for you to analyze
        """
        return 0
    
    @tool 
    async def write_to_context(text):
        """
        this function takes in a python list [] as the argument with the text you want to write to your context.
        ex ["visited the reddit page and gathered that blah blah laptop has these feature where this other laptop ............."],
        Write to context after every step ["i visited this website <describe the website and what you see in it >"]
        Be very verbose with you what you want to store into context because this is your memory whatever you choose to write in this you will have access for the entire 
        duration of your agent cycle
        """
        return 0
    
    @tool
    async def ask_user(question):
        """
        this function takes in a python list [] as the arguemnt with the question you want to ask the user 
        Use this function to get clarification on the task asked by the user, ex ["You mentioned you want a laptop, what are you gonna use it for ? "], ["you mentioned LA what were to reffering you ?"], etc
        DO NOT ask the user things you are supposed to do like ["can you give me the link"], ["can you mention the tag for this button"], etc
        """
        return 0
    
    @tool
    async def get_ui_element(query):
        """you can use this function to query for UI elements, eg query : "where do i click login "
        it will return the TOP 3 matches with the tag, the text, class, playwright handle etc etc, which you can use to analyze
        eg2 : "where to click bestsellers" will return the top 3 matches for you to choose again,
        **IMPORTANT** ALWAYS use get page text so YOU CAN DECIDE WHAT TEXT TO QUERY FOR"""
        return 0
    
    @tool
    async def click_thing(selector: str):
        """argument should be a python list
            use this function ONLY after using get_ui_element function, 
            it will take in the arguments ['locator_str = 'a.nav_a[href="https://sell.amazon.in/grow-your-business/amazon-global-selling.html?ld=AZIN_Footer_V1&ref=AZIN_Footer_V1"]:has-text("Amazon Global Selling")']
            Which is a playwright selector and that selector will be clicked use this for buttons mainly
            """
        return 0
    
    @tool 
    async def fill_thing(selector:str, text:str):
        """
        arugement should be a python list
        use this function ONLY after using get_ui_element function,
        it will take in the arguments ['label.a-form-label:has-text("Email or mobile phone 'number")' , "example@gmail.com"] , ['label.a-form-label', "example name"]
        Which is a playwright selector and the text you want to enter use this to fill forms applications etc
        """
        return 0

    return [search_google, get_google_page_links,
            goto_link, search_website,
            get_page_text, write_to_context,
            ask_user, get_ui_element,
            click_thing, fill_thing]