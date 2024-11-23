'''
Contains code for the frontend app. This app sends requests to varous
microservices (LLM, STT, TTS) via an API microservice all located on
some backend server. The user can record their audio or enter text
and deliver it to the microservices to get text or audio back. 

Author: 
    Siraj Sabihuddin

Date: 
    June 28, 2024
'''
#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------
import flet as ft
import logging
import httpx
import json
import io
import numpy as np
import sounddevice as sd
import soundfile as sf

#-----------------------------------------------------------------------
# LOGGER CONFIG
#-----------------------------------------------------------------------
logging.basicConfig(
    # Set the logging level to DEBUG
    level=logging.INFO,         
    # Define the log message format
    format='%(levelname)s: (%(name)s[%(funcName)s]) (%(asctime)s): %(message)s',
    # Define the date format 
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        # Log messages to a file
        logging.FileHandler('main.log'),
        # Log messages to the console
        logging.StreamHandler()  
    ]
)

# Create a logger object
logger = logging.getLogger("MAIN")

#-----------------------------------------------------------------------
# FRONTEND CLASS
#-----------------------------------------------------------------------
class Frontend:
    '''
    This class encapsulates all necessary functions to create a mobile 
    frontend for a Voice assistant. Please refer to the following links
    for docs on designing flet apps and related:
        
    1. https://github.com/flet-dev/examples
    2. https://flet.dev/docs/
    3. https://gallery.flet.dev/icons-browser/ 

    Attr:
        page : ft.Page
            The instance of the main page onto which
            this app will be drawn
        title : str
            The title of this app
        scrollbar : ft.Scrollbar
            The scrollbar associated with this app
        menu : ft.Menu
            The menu associated with this app
        appbar : ft.AppBar
            The app bar associated with this app
        textbar : ft.Row
            A row of controls for entering text and
            sending it. 
        conversation_history : list of dict
            A list containing dictionar value of the form
            {role:content}
        card : list of ft.Cards
            A list of Card elements containng the conversation
            history dialogue
        light_color : ft.colors
            The colour associated with the light theme
        dark_color : ft.colors
            The colour associated with the dark theme
    '''
    #-------------------------------------------------------------------
    # CREATE
    #-------------------------------------------------------------------
    def __init__(self, page: ft.Page, title: str, configfile : str):
        '''
        The constructor. Sets up and initializes all page elements
        and class attributes

        Args:
            page : ft.Page
                The page onto which everything is to be drawn
            title : str
                The title of the app
        '''
        # Assign the class variables for page and title
        self.page = page
        self.title = title
        self.configfile = configfile

        # Create conversation history
        self.conversation_history = self.event_getHistory()
        self.card = []

        # Adds the various elements to the page
        self.create_scrollbar()
        self.create_theme()
        self.create_menu()
        self.create_appbar()
        self.create_drawer()
        self.create_textbar()
        self.create_cards()
        self.create_dialogs()
    
    #-------------------------------------------------------------------
    # CREATE_SCROLLBAR
    #-------------------------------------------------------------------
    def create_scrollbar(self):
        '''
        Creates the page scroll bar and adds it to the page
        '''
        logger.info ("Scrollbar Created")

        # Initialize the scrollbar
        self.scrollbar=ft.ScrollbarTheme \
        (
            # The track is the entire scrollbar length
            track_visibility=False,
            # The thumb is just the moving slider inside the track
            thumb_visibility=True
        )

        # Page automatically decides if scrolling should or should not
        # be enabled.
        self.page.scroll = "adaptive"

        # Update the page
        self.page.update()

    #-----------------------------------------------------------------------
    # CREATE_THEME
    #-----------------------------------------------------------------------
    def create_theme(self):
        '''
        Initializes the basic theme elements for the page. These are elements
        that provide the overall colours and feel of the app 
        '''
        logger.info ("Theme Created")

        # Set up various page elements for display
        self.page.title = self.title
        self.page.padding = ft.padding.only(right=0)
        self.page.padding = ft.padding.only(left=10)

        # Identifies the colours for the light and
        # dark themes.
        self.light_color = ft.colors.DEEP_ORANGE
        self.dark_color = ft.colors.INDIGO

        # Setup the current theme mode as dark
        self.page.theme_mode = "dark"

        # Setup the light and dark theme basic configurations
        self.page.theme = ft.theme.Theme(color_scheme_seed=self.light_color, use_material3=True, scrollbar_theme=self.scrollbar)
        self.page.dark_theme = ft.theme.Theme(color_scheme_seed=self.dark_color, use_material3=False, scrollbar_theme=self.scrollbar)

        # Create the theme toggle icon
        if (self.page.theme_mode == "light"):
            self.theme_icon = ft.IconButton(ft.icons.WB_SUNNY, on_click=self.event_toggleTheme)
        else: 
            self.theme_icon = ft.IconButton(ft.icons.WB_SUNNY_OUTLINED,on_click=self.event_toggleTheme)

        # Update the page to redraw it
        self.page.update()

    #-----------------------------------------------------------------------
    # CREATE_MENU
    #-----------------------------------------------------------------------
    def create_menu(self):
        '''
        Initializes the right hand menu for the app. There are two handler
        functions that are called, one by each menu item.
        '''
        logger.info ("Menu Created")

        menu_items = [
            ft.PopupMenuItem(icon=self.theme_icon.icon, text="Toggle Theme", on_click=self.event_toggleTheme),
            ft.PopupMenuItem(icon=ft.icons.CLEAR, text="Clear History", on_click=self.event_clearHistory)
        ]

        # Create a menu with the above menu items. 
        self.menu = ft.PopupMenuButton(items=menu_items)    

        # Update the page
        self.page.update()

    #-----------------------------------------------------------------------
    # CREATE_APPBAR
    #-----------------------------------------------------------------------
    def create_appbar(self):
        '''
        Defines the top fixed bar for the application. This bar provides
        the title along with a few buttons for user interaction.
        '''
        logger.info ("Appbar Created")

        # Create the add various icons 
        drawerButton = ft.IconButton(ft.icons.MENU_ROUNDED, on_click=self.event_showDrawer)
        clearHistoryButton = ft.IconButton(icon=ft.icons.DELETE_OUTLINED, on_click=self.event_clearHistory)
        micButton = ft.IconButton(icon=ft.icons.MIC_OUTLINED, on_click=self.event_recordAudio)
        
        # Create the Appbar object
        self.appbar = ft.AppBar(
            leading=drawerButton,
            leading_width=40,
            title=ft.Text(self.title),
            center_title=True,
            actions=[clearHistoryButton,micButton,self.menu],
        )

        # Add the appbar to the page
        self.page.appbar = self.appbar

        # Update the page
        self.page.update()

    #-----------------------------------------------------------------------
    # CREATE_DRAWER
    #-----------------------------------------------------------------------
    def create_drawer(self):
        '''
        This function defines the left hand side sliding drawer menu. 
        '''
        logger.info ("Drawer Created")

        # Define each item for the drawer and store it in a list
        drawer_items= [
            ft.Container(height=12),
            ft.NavigationDrawerDestination(
                icon_content=ft.Icon(ft.icons.SPATIAL_AUDIO_OUTLINED),
                label="STT",
                selected_icon=ft.Icon(ft.icons.SPATIAL_AUDIO),
            ),
            ft.NavigationDrawerDestination(
                icon_content=ft.Icon(ft.icons.MODEL_TRAINING_OUTLINED),
                label="LLM",
                selected_icon=ft.icons.MODEL_TRAINING,
            ),
            ft.NavigationDrawerDestination(
                icon_content=ft.Icon(ft.icons.TEXT_SNIPPET_OUTLINED),
                label="TTS",
                selected_icon=ft.icons.TEXT_SNIPPET,
            ),
            ft.NavigationDrawerDestination(
                icon_content=ft.Icon(ft.icons.API_OUTLINED),
                label="API",
                selected_icon=ft.icons.API,
            ),
            ft.NavigationDrawerDestination(
                icon_content=ft.Icon(ft.icons.ACCOUNT_CIRCLE_OUTLINED),
                label="Account",
                selected_icon=ft.icons.ACCOUNT_CIRCLE,
            ),
        ]

        # Add the navigation drawer to the page. 
        self.page.drawer = ft.NavigationDrawer(
            controls=drawer_items,
            on_change=self.event_changeDrawer,
            on_dismiss=self.event_dismissDrawer
        )

        # Update the page
        self.page.update()

    #-----------------------------------------------------------------------
    # CREATE_TEXTBAR
    #-----------------------------------------------------------------------
    def create_textbar(self):
        '''
        Defines the top fixed bar for the application. This bar provides
        the title along with a few buttons for user interaction.
        '''
        logger.info ("Textbar Created")
        
        # Create a text field for input
        text = ft.TextField(hint_text="Enter your query", expand=True, border_radius=10)

        # Create a send icon button
        button = ft.IconButton(
            icon=ft.icons.SEND,
            width=48,
            height=48,
            on_click=self.event_sendText
        )

        # Create a row to hold the text field and send button
        self.textbar = ft.Row([text, button])

        # Create a BottomAppBar
        self.page.bottom_appbar = ft.BottomAppBar(
            content=self.textbar,
            padding=10
        )
        
        # Hovering microphone
        self.page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.MIC, on_click=self.event_recordAudio)

        # Update the page
        self.page.update()

    #-----------------------------------------------------------------------
    # CREATE_CARDS
    #----------------------------------------------------------------------- 
    def create_cards(self):
        '''
        Initializes the cards being displayed. These cards contain one item
        of dialogue each. Either by the machine or by the user. 
        '''
        # Iterate through all items in the initial conversation history
        # as stored in the client settings. 
        for i in self.conversation_history:
            logger.info (i)

            # Check which role the particular conversation dialogue is
            # And assign a different profile pic icon accordingly. There
            # are only two roles currently "user" and "system"
            if (i["role"]=="user"):
                icon = ft.CircleAvatar(content=ft.Icon(ft.icons.ACCOUNT_CIRCLE))
            else:
                icon = ft.CircleAvatar(content=ft.Icon(ft.icons.LIGHTBULB_CIRCLE))

            # Create a menu for each card
            menu = ft.PopupMenuButton(
                icon=ft.icons.MORE_VERT,
                items=
                [
                    ft.PopupMenuItem(text="Delete"),
                    ft.PopupMenuItem(text="Edit"),
                ]
            )

            # Create a tile containing an icon, the dialogue related text and
            # the menu for the tile. Use a container to hold the subtitle with padding
            tile = ft.ListTile(
                leading=icon,
                title=ft.Text(i["role"].capitalize()),
                subtitle=ft.Container(ft.Text(i["content"]), padding=ft.padding.only(top=7)),
                trailing=menu
            )

            # Create a card. Use a container to hold content as a responsive row which consists
            # of a single tile object
            c = ft.Card(
                margin = ft.margin.only(right=40),
                content=ft.Container(content=ft.ResponsiveRow([tile]), padding=10),
            )

            # Append the card to a list of cards 
            self.card.append(c)

        # For every card created, add it to the page
        for i in self.card:
            self.page.add(i)

        # Automate the scrolling to the end of the chat window
        self.page.scroll_to(offset=-1, duration=0, curve=ft.AnimationCurve.EASE_IN_OUT)

    #-----------------------------------------------------------------------
    # CREATE_DIALOGS
    #-----------------------------------------------------------------------
    def create_dialogs(self):
        '''
        Creates the dialogues for when the user clicks on a drawer item
        This includes a dialogue to select STT model, LLM model and TTS
        model. Along with configuring the API url and port. 
        '''
        logger.info("Creat Dialogues")

    #-----------------------------------------------------------------------
    # EVENT_TOGGLETHEME
    #-----------------------------------------------------------------------
    def event_toggleTheme(self, e):
        '''
        This is an event handling function that is called whenever the theme
        of the app is changed. It toggles the theme between light and dark

        Args:
            e : ft.event
                The event object associated with this handler. For access to 
                specific details about event if needed
        '''
        logger.info ("Theme Toggled")

        # Toggle the page theme mode variable
        if (self.page.theme_mode == "light"):
            self.page.theme_mode = "dark"
            self.theme_icon.icon = (ft.icons.WB_SUNNY_OUTLINED)
            self.page.dark_theme = ft.theme.Theme(color_scheme_seed=self.dark_color, use_material3=False)
        else:
            self.page.theme_mode = "light"
            self.theme_icon.icon = (ft.icons.WB_SUNNY)
            self.page.theme = ft.theme.Theme(color_scheme_seed=self.light_color, use_material3=True)

        # Update the page items after toggle
        self.page.update()

    #-----------------------------------------------------------------------
    # EVENT_CLEARHISTORY
    #-----------------------------------------------------------------------
    def event_clearHistory(self, e):
        '''
        This is an event handling function that is called when we want to 
        clear the conversation history. It grabs the conversation history
        from the remote location. Parses it and then updates the cards to
        be displayed on screen

        Args:
            e : ft.event
                The event object associated with this handler. For access to 
                specific details about event if needed
        '''
        logger.info("Clear History")

    #-----------------------------------------------------------------------
    # EVENT_SHOWDRAWWER
    #-----------------------------------------------------------------------
    def event_showDrawer(self, e):
        '''
        This is an event handling function that is called when we want to 
        show the drawer for the app

        Args:
            e : ft.event
                The event object associated with this handler. For access to 
                specific details about event if needed
        '''
        logger.info("Show Drawer")
        self.page.drawer.open = True
        self.page.drawer.update()

    #-----------------------------------------------------------------------
    # EVENT_CLEARHISTORY
    #-----------------------------------------------------------------------
    def event_clearHistory(self,e):
        '''
        This is an event handling function that is called when we want to 
        clear the conversation history via the api microservice

        Args:
            e : ft.event
                The event object associated with this handler. For access to 
                specific details about event if needed
        '''
        logger.info("Clear History")

         # Grab the api endpoint details 
        config = self.configLoad(self.configfile)
        api_endpoint = f"http://{config['api_host']}:{config['api_port']}/history/clear"

        # Generate a curl request 
        response = httpx.get(api_endpoint)

        logger.info(self.conversation_history)

        # Update the page
        for i in self.card:
            self.page.controls.remove(i)

        self.conversation_history =[]
        self.card=[]
        self.page.update()

    #-----------------------------------------------------------------------
    # EVENT_RECORDAUDIO
    #-----------------------------------------------------------------------
    def event_recordAudio(self, e):
        '''
        This is an event handling function that is called when we want to 
        record audio. Pressing this once starts the audio recording. Pressing
        it again stops the audio recording and sends it to ther microservice

        Args:
            e : ft.event
                The event object associated with this handler. For access to 
                specific details about event if needed
        '''
        logger.info("Record Audio")

        # Set the threshold. Record in one second time chunks
        # Assume a single channel at 44100 Hz. 
        threshold=0.05
        time=1
        channels= 1
        rate=44100
        
        # Assume that the volume is already at the threshold
        # when starting the recording
        volume = threshold
    
        # Initialize the first recording as an empty array
        recording = np.empty((0, channels))

        # Create an empty list of lists with 'channels' number of columns
        #recording = [[] for _ in range(channels)]

        while (volume >= threshold):
            # Record audio
            recording_ = sd.rec(int(rate * time), samplerate=rate, channels=channels)
            # Wait until recording is finished
            sd.wait()  

            # Calculate peak value for each channel for the small
            # recording chunk
            peak_values = np.max(np.abs(recording_), axis=0)
            #peak_values = [max(abs(value) for value in channel) for channel in zip(*recording_)]

            # Determine the maximum peak value across all channels
            volume = np.max(peak_values)
            #volume = max(peak_values)

            # Print the volume to debug and adjust thresholds
            print (volume)

            # Concatenated to the previous recording
            recording = np.concatenate((recording, recording_), axis=0)
            #recording.extend(recording_)

        # Save recording to a WAV file in memory
        raw_bytes = io.BytesIO()
        sf.write(raw_bytes, recording, rate, format='wav')
        raw_bytes.seek(0)

        # Grab the api endpoint details 
        config = self.configLoad(self.configfile)
        api_endpoint = f"http://{config['api_host']}:{config['api_port']}/transcribe/{config['stt_model']}"

        # Generate a curl request 
        response = httpx.request("GET", api_endpoint, headers={"Content-Type": "application/octet-stream"}, content=raw_bytes.read())

        # Record the response
        logger.info(f"Response: {response.text}")

        # Get the text and feed it into the LLM 
        api_endpoint = f"http://{config['api_host']}:{config['api_port']}/query/{config['llm_model']}/{response.text}"

        # Generate a curl request 
        response = httpx.get(api_endpoint)
        
        # Log the response
        logger.info(f"Response: {response.text}")

        # Get the updated history
        self.conversation_history=self.event_getHistory()

        # Update the page
        self.card=[]
        self.create_cards()

        # Get the text response and convert it to audio
        api_endpoint = f"http://{config['api_host']}:{config['api_port']}/speech/{config['tts_model']}/{response.text}"

        # Generate a curl request 
        response = httpx.post(api_endpoint)
      
        # Use the response content as an in-memory file
        audio_data = io.BytesIO(response.content)

        # Read the audio data
        data, fs = sf.read(audio_data)

        # Play the audio data
        sd.play(data, fs)
        # Wait until the file is done playing
        sd.wait()  

    #-----------------------------------------------------------------------
    # EVENT_CHANGEDRAWER
    #-----------------------------------------------------------------------
    def event_changeDrawer(self, e):
        '''
        This is an event handling function that is called when we want to 
        change the selected drawer item selection.

        Args:
            e : ft.event
                The event object associated with this handler. For access to 
                specific details about event if needed. In this function we 
                grab the index of the control selected. 
        '''
        logger.info(f"Drawer Change: {e.control.selected_index}")

        if (e.control.selected_index==0):
            logger.info(f"Load STT Dialog")
        elif (e.control.selected_index==1):
            logger.info(f"Load LLM Dialog")
        elif (e.control.selected_index==2):
            logger.info(f"Load TTS Dialog")
        elif (e.control.selected_index==3):
            logger.info(f"Load API Dialog")
        else:
            logger.info(f"Load Account Dialog")

    #-----------------------------------------------------------------------
    # EVENT_DISMISSDRAWER
    #-----------------------------------------------------------------------
    def event_dismissDrawer(self, e):
        '''
        This is an event handling function that is called when we want to 
        dismiss the drawer. 

        Args:
            e : ft.event
                The event object associated with this handler. For access to 
                specific details about event if needed. In this function we 
                grab the index of the control selected. 
        '''        
        logger.info("Drawer Dismissed")

    #-----------------------------------------------------------------------
    # EVENT_DISMISSDRAWER
    #-----------------------------------------------------------------------
    def event_sendText(self, e=None):
        '''
        This is an event handling function that is called when we want to 
        dismiss the drawer. 

        Args:
            e : ft.event
                The event object associated with this handler. For access to 
                specific details about event if needed. In this function we 
                grab the index of the control selected. 
        '''        
        logger.info("Send Text")

        # Checks if text has been entered into the textbar textfield
        textfield = self.textbar.controls[0]

        # Grabs the location to which tes
        if (textfield.value):
            # Grab the api endpoint details 
            config = self.configLoad(self.configfile)
            api_endpoint = f"http://{config['api_host']}:{config['api_port']}/query/{config['llm_model']}/{textfield.value}"

            # Generate a curl request 
            response = httpx.get(api_endpoint)
            
            # Log the response
            logger.info(f"Response: {response.text}")

            # Clear the text field
            textfield.value = ""
            textfield.update()

            # Get the updated history
            self.conversation_history=self.event_getHistory()

            # Update the page
            self.card=[]
            self.create_cards()

    #-----------------------------------------------------------------------
    # EVENT_GETHISTORY
    #-----------------------------------------------------------------------
    def event_getHistory(self, e=None):
        '''
        This function grabs the context conversation history data from 
        the api microservice

        Args:
            e :  ft.event
                The event object associated with this handler. For access to 
                specific details about event if needed. In this function it 
                defaults to none because I actually don't use it as an event
                handler.
        '''        
        # Log the text input
        logger.info("Get History")

        # Grab the api endpoint details 
        config = self.configLoad(self.configfile)
        api_endpoint = f"http://{config['api_host']}:{config['api_port']}/history/list"

        # Generate a curl request 
        response = httpx.get(api_endpoint)
        
        # Log the response
        logger.info(f"Response: {response.text}")

        return (json.loads(response.text))

    #-----------------------------------------------------------------------
    # CONFIGLOAD
    #-----------------------------------------------------------------------
    def configLoad(self, config_file):
        '''
        Grab the stored config data in the config file

        Args:
            config_file : str = 
                The path to the JSON config file

        Returns:   
            config : dict = 
                Json dictionary of values from json file

            model_index : int = 
                The index of the active model
        '''
        # Load the configuration fille to get running parameters
        with open(config_file) as json_file:
            config = json.load(json_file)

        # Return dictionary
        return config

    #-----------------------------------------------------------------------
    # CONFIGSTORE
    #-----------------------------------------------------------------------
    def configStore (self, config_file, config):
        '''
        Store the updated config data in the config file

        Args:
            config_file : str = 
                The path to the JSON config file
            
            config : dict = 
                The updated dictionary of configuration
                data
        '''
        # Store the updated config into file
        with open(config_file, 'w') as json_file:
            json.dump(config, json_file, indent=4)

#-----------------------------------------------------------------------
# MAIN
#-----------------------------------------------------------------------
def main(page: ft.Page):
    # Calls the constructor function __init__ in the Frontend
    # class. 
    fe = Frontend(page, "W3NG Personal Assistant", "main.json")

# Create the app
ft.app(target=main, assets_dir="assets")
