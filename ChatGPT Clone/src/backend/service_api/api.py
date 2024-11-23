'''
Contains code that unifies api calls for all other services: LLM, STT and
TTS. Basically it receives requests from the browser or frontend and then
routes them to the individual microservices. These then appropriately
respond. The responses are then routed to the frontend. 

Author: 
    Siraj Sabihuddin

Date: 
    June 28, 2024
'''
#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import sqlite3
import json
import uvicorn
from openai import OpenAI
from io import BytesIO
import pycurl
import time
import logging
import httpx

#-----------------------------------------------------------------------
# LOGGER CONFIG
#-----------------------------------------------------------------------
logging.basicConfig(
    # Set the logging level to DEBUG
    level=logging.DEBUG,         
    # Define the log message format
    format='%(levelname)s: (%(name)s[%(funcName)s]) (%(asctime)s): %(message)s',
    # Define the date format 
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        # Log messages to a file
        logging.FileHandler('api.log'),
        # Log messages to the console
        logging.StreamHandler()  
    ]
)

# Create a logger object
logger = logging.getLogger("API")

#-----------------------------------------------------------------------
# FAST API APP
#-----------------------------------------------------------------------
# Setup fast api app
app = FastAPI()

#-----------------------------------------------------------------------
# GLOBALS
#-----------------------------------------------------------------------
# Global store for conversation history and 
# any configuration information. These are temporary
# variables that will not persist. If they crash 
history = []
confg = []
config_file = 'api.json'

#-----------------------------------------------------------------------
# SPEECH
#-----------------------------------------------------------------------
@app.post("/speech/{model}/{text}")
async def speech(model, text):
    '''
    Sends text data to service for TTS. The service generates
    a speech audio byte buffer object. This can then be saved
    into an audio file for playback

    Route:
        @app.get("/speech/{model}/{text}")

    Args:
        model : str = 
            The model to use for the text to speech converstion

        text : str = 
            The text data to convert into audio 

    Returns:
        response : StreamingResponse = 
            The response object for the audio data 
    '''
    global config

    # Create the endpoint for RESTful request
    api_endpoint_text='http://'+ config["tts_host"] + ':' + config["tts_port"] + '/text/' + model + "/" + text

    # Empty response by default
    response = None

    # We are going to try to connect to our STT service
    try:
        # Call the llm api to change model
        logger.info (f"Sending text to {model} via {api_endpoint_text}")
        response = httpx.post(api_endpoint_text)
        #response = request(url=api_endpoint_text, data=None, method="POST", contenttype="Content-Type: application/text")

        logger.info (f"Response received: {response}")

        # Check that the request has been completed successfully
        if (response):
            # Grab the audio_bytes from the response
            audio_bytes = BytesIO(response.content)
            
            # Debugging by looking at the contents of the response to 
            # make sure that it has been transmitted correctly
            logger.debug(audio_bytes.getvalue()[:20])

            # Confirming conversion
            logger.info (f"Converted text to audio")

            # Create the response object
            response =StreamingResponse(BytesIO(audio_bytes.getvalue()), media_type="audio/wav")
        else:
            logger.info (f"Unable to convert to audio")
            response = None

    except Exception as e:
        # Print an error indicating that there is a problem sending
        # the curl request
        logger.error(f"Error: {e}")

    # Send transcribed response data 
    return response

#-----------------------------------------------------------------------
# TRANSCRIBE
#-----------------------------------------------------------------------
@app.get("/transcribe/{model}")
async def transcribe(model, req : Request):
    '''
    Sends audio data in request body to service that transcribes it
    into text and receives the text back

    Route:
        @app.get("/transcribe/{model}")

    Args:
        model : str = 
            The model to use for the speech to text converstion

        request : Request = 
            The request body containing the audio data. 

    Returns:
        response : str = 
            The string containing the transcribed text
    '''
    global config

    # Create the endpoint for RESTful request
    api_endpoint_audio='http://'+ config["stt_host"] + ':' + config["stt_port"] + '/audio/' + model
    
    # Pull together the request body json
    audio_data = await req.body()

    # Response is empty by default
    response = ""

    # We are going to try to connect to our STT service
    try:
        # Call the llm api to change model
        logger.info (f"Sending audio to {model} via {api_endpoint_audio}")
        #response = httpx.post(api_endpoint_audio)
        response=request(url=api_endpoint_audio, data=audio_data, method="POST", contenttype="Content-Type: application/octet-stream")

        # Check that the request has been completed successfully
        if (response): 
            logger.info (f"Transcribed data: {response}")
        else:
            logger.info (f"Unable to transcribe audio")

    except Exception as e:
        # Print an error indicating that there is a problem sending
        # the curl request
        logger.error(f"Error: {e}")

    # Send transcribed response data 
    return response

#-----------------------------------------------------------------------
# QUERY
#-----------------------------------------------------------------------
@app.get("/query/{model}/{prompt}")
async def query(prompt, model):
    '''
    Sends text from given request file to an LLM model of your choice (internal or external). 
    A key is used to access the model if needed. The resulting response of the LLM is stored. 
    In the case of local internal models, if the local model is not running an error is thrown. 
    Before this function is called with a local model, that local model should be run using the 
    run() function. 

    Route:
        @app.get("/query/{model}/{prompt}")

    Args:
        prompt : str = 
            The input query text

        model : str = 
            The model to use. If the the model is a local model specify 
            the path to the local model

        key : str = 
            The API key if needed.

        host : str = 
            The url end point to the API location relevant to querying the model
    
    Returns:
        response : str = 
            The string response to the query
    '''
    # Load the global variable
    global config, history

    # Record start time
    starttime = time.time()

    # Create the query dictionary
    query = {"role": "user", "content": prompt}

    # Append the most recent prompt to the conversation history
    history.append(query)

    # Store the latest prompt
    historyStore(model=model, max_tokens=config['llm_maxtokens'], role="user", content=prompt)

    # Define the model switchiing data structure
    json_data_model = None

    # Define the chat completions data structure
    # This is a JSON data structure for the query in the followin
    # format: 
    # {
    #     "model": "string",                      // The name of the model you want to use (e.g., "gpt-4").
    #     "messages": [                           // An array of message objects.
    #         {
    #         "role": "system|user|assistant",    // The role of the message author. Options are "system", "user", or "assistant".
    #         "content": "string"                 // The content of the message.
    #         }
    #     ],
    #     "temperature": number,                  // (Optional) Sampling temperature, between 0 and 2.
    #     "top_p": number,                        // (Optional) An alternative to sampling with temperature, where the model considers the results of the tokens with top_p probability mass.
    #     "n": integer,                           // (Optional) Number of chat completion choices to generate for each input message.
    #     "stream": boolean,                      // (Optional) If set, partial message deltas will be sent as data-only server-sent events as they become available.
    #     "stop": "string or array",              // (Optional) Up to 4 sequences where the API will stop generating further tokens.
    #     "max_tokens": integer,                  // (Optional) The maximum number of tokens to generate in the chat completion.
    #     "presence_penalty": number,             // (Optional) Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
    #     "frequency_penalty": number,            // (Optional) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, reducing the model's likelihood to repeat the same line verbatim.
    #     "logit_bias": {                         // (Optional) Modify the likelihood of specified tokens appearing in the completion.
    #         "token_id": bias                    // Token ID mapped to its bias value (-100 to 100).
    #     },
    #     "user": "string"                        // (Optional) A unique identifier representing your end-user, which can help OpenAI monitor and detect abuse.
    # }
    json_data_query = '{"model":"' + model + '", "messages":' + json.dumps(history) + ', "max_tokens":' + config["llm_maxtokens"] + '}'
    logger.debug (json_data_query)

    # Create an api endpoint
    api_endpoint_model='http://'+ config["llm_host"] + ':' + config["llm_port"] + '/model/' + model
    api_endpoint_query='http://'+ config["llm_host"] + ':' + config["llm_port"] + '/relay/v1/chat/completions'

    # We are going to try to connect to our LLM service. If for some reason the 
    # connection is refused. We will try to start the LLM and re-attempt
    # a connection. If still, there are problems then we just terminate
    try:
        # Call the llm api to change model
        logger.info (f"Changing model to {model} via {api_endpoint_model}")
        response = request(url=api_endpoint_model, data=json_data_model, method="PUT", contenttype="Content-Type: application/json")

        # Check that the request has been completed successfully
        if (response): 
            logger.info (f"Model has been changed to {model}")
        else:
            logger.info (f"Unable to change model to {model}")

        # Call the llm api to make a request to the model selected
        logger.debug (f"Sending prompt {prompt} via {api_endpoint_query}")
        response = request(api_endpoint_query, data=json_data_query, method="POST", contenttype="Content-Type: application/json")

        # Extract the summary from the OpenAI API response.
        response = response['choices'][0]['message']['content']
        logger.debug(f"Obtained response {response} for prompt")

    except Exception as e:
        # Print an error indicating that there is a problem sending
        # the curl request
        logger.error("Error. The model may not have started: " + str(e))

    if (response):
        # Append the most recent prompt to the conversation history
        history.append({
            "role": "system",
            "content": response
        })

    # Store the latest response into the database
    historyStore(model=model, max_tokens = config['llm_maxtokens'], role="system",content=response)

    # End time
    endtime = time.time()
    totaltime = endtime - starttime

    # Print the response and response time
    logger.debug (f"Total time: {totaltime}")
    logger.info (f"Response: {response}")
    return response

#-----------------------------------------------------------------------
# REQUEST
#-----------------------------------------------------------------------
def request(url, data, method, contenttype):
    '''
    This function creates a http request to the particular url endpoint 
    with request body as in the data variable

    Args:
        url : str = 
            The endpoint url for the request 

        data : str
            The json request body 

        method : str
            The method to use for the request
            e.g. POST, GET, PUT etc.

        contenttype : str =
            String of format: "Content-Type: application/json" or 
            similar. 

    Returns
        response : str = 
            The json response body. If no response body
            returns None
    '''
    # Construct the cURL for specifying meme type
    httpheader=[
        contenttype
    ]

    try:
        # Just a storage buffer
        buffer = BytesIO()

        # Sends request for getting chat completion 
        crl = pycurl.Curl()

        # The url where the request should be sent
        crl.setopt(crl.URL, url)        

        # The http header                  
        crl.setopt(crl.HTTPHEADER, httpheader)            
        
        if method == "POST":
            # Set to send POST request
            crl.setopt(crl.POST, 1)                           
            # Set POST fields (JSON data)
            if (data):
                crl.setopt(crl.POSTFIELDS, data)  

        elif method == "PUT":
            # Set to send PUT request
            crl.setopt(crl.CUSTOMREQUEST, "PUT")  
            # Set PUT fields (JSON data)    
            if (data):        
                crl.setopt(crl.POSTFIELDS, data)                  

        elif method == "GET":
            # Set to send GET request
            crl.setopt(crl.HTTPGET, 1)                        

        # Buffer to receive responses
        crl.setopt(crl.WRITEDATA, buffer)                 
        
        # Perform the request
        crl.perform()                                   

        # Get the HTTP response status code
        http_response_code = crl.getinfo(pycurl.HTTP_CODE)

        # Check if the response is JSON and decode it
        try:
            logger.info ("Attempting to encode as UTF-8")
            response = json.loads(buffer.getvalue().decode('utf-8'))
            logger.info (f"Response: {response}")
        except json.JSONDecodeError:
            logger.info ("Contains binary data")
            # If decoding fails, return the raw bytes
            response = buffer.getvalue()


        # Resets the pycurl instance for next request
        crl.reset()

        # Closes the request connection
        crl.close()    

        # Resets the buffers. 
        buffer.flush()
        buffer.seek(0)

        return response

    except Exception as e:
        # Print an error indicating that there is a problem sending
        # the curl request
        logger.error(f"Request error: {e}")
        return None

#-----------------------------------------------------------------------
# HISTORYSTORE
#-----------------------------------------------------------------------
def historyStore (model, max_tokens, role, content):
    '''
    Adds a record of the history to the sqlite database on the api 
    server. This can then be retrieved by the user as needed through
    an API call. If no history table or database exists, then one
    is created. This created database should have a history table
    containing two columns: role and content indexed sequentially
    by the order in which the history was recorded. 

    Args:
        model : str = 
            The name of the model being used. 

        role : str = 
            The role of the message. Could be either user or system

        content : str = 
            The content of the message as a sting. 
            
        max_tokens : int = 
            The number of available tokens for response used
            in this message
    '''
    # Bring local into global scope
    global config

    # Initialize connector variable
    conn = None
    try:
        # Connect to the database (if it exists)
        # Create one if it doesn't exist
        conn = sqlite3.connect(config['api_db'])

        # Get the cursor for the db
        cursor = conn.cursor()

        # Create an SQL query for creating a table
        query = """ CREATE TABLE IF NOT EXISTS history 
                    (
                        id integer PRIMARY KEY,
                        model text NOT NULL, 
                        max_tokens integer NONT NULL,
                        role text NOT NULL,
                        content text NOT NULL
                    );"""
        
        # Execute the SQL query
        cursor.execute(query)

        logger.debug (f"Model: {model}, Max Tokens: {max_tokens}, Role: {role}, Content: {content}")

        # Add a record to the table that's been created (if any needed to 
        # be created)
        query = """ INSERT INTO history(model, max_tokens, role, content)
                    VALUES(?, ?, ?, ?)"""
        cursor.execute(query, (model, max_tokens, role, content))

        # Commit the transactions
        conn.commit()
    
    # We've violated some sqlite storage process
    except Exception as e:
        logger.error (f"Storage into sqlite DB failed: {e}")

    # Attempt to close the database connection if existing
    finally:
        if (conn):
            # Close and write the database
            conn.close()

#-----------------------------------------------------------------------
# HISTORYLOAD
#-----------------------------------------------------------------------
def historyLoad():
    '''
    Loads the data from the history table in the storage database.
    This history table is used to provide context if the user has
    been having an on-going conversation with the model
    '''
    # Load the global variable
    global history, config

    # Initialize the connector
    conn = None

    try:
        # Connect to the database (if it exists)
        # Create one if it doesn't exist
        conn = sqlite3.connect(config['api_db'])

        # Get the cursor for the db
        cursor = conn.cursor()

        # Execute query to fetch all rows from the 'history' table
        cursor.execute("SELECT role, content FROM history")
        
        # Fetch all rows from the executed query
        rows = cursor.fetchall()
        
        # Get column names from the cursor description
        column_names = [description[0] for description in cursor.description]
        
        # Convert rows to list of dictionaries
        history = [dict(zip(column_names, row)) for row in rows]
    
    except Exception as e:
        logger.error (f"Unable to retreive conversation history: {e}")

    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()

#-----------------------------------------------------------------------
# HISTORYCLEAR
#-----------------------------------------------------------------------
@app.get("/history/clear")
async def historyClear ():
    '''
    This function clears the database history table and any variables
    that are acting to store this history 

    Route:
        @app.get("/history/clear")

    Return:
        value : bool
            True if succesfully completed
    '''
    # Bring local into global scope
    global config, history

    # Connect to the database (if it exists)
    # Create one if it doesn't exist
    conn = sqlite3.connect(config['api_db'])

    # Get the cursor for the db
    cursor = conn.cursor()

    # Execute DELETE statement to erase all rows from the 'history' table
    cursor.execute("DELETE FROM history")
    
    # Commit the transaction
    conn.commit()

    # Close the database
    conn.close()

    # Clear out the history variable
    global history
    history = []

    # Indicate the operation is done
    return True

#-----------------------------------------------------------------------
# HISTORYLIST
#-----------------------------------------------------------------------
@app.get("/history/list")
async def historyList ():
    '''
    Returns a list of user and system responses as stored since 
    queries have been taking place. These provide context for the LLM
    to appropriately respond into the future. 

    Route:
        @app.get("/history/list")

    Return:
        history : list of dict = 
            A list of dict in the form of 
            [{'user': 'some message'}, {'system': 'some message'}]
    '''
    # Bring in global variables
    global history

    # Return this global list
    return history

#-----------------------------------------------------------------------
# TOKENSMAX
#-----------------------------------------------------------------------
@app.get("/tokens/max")
@app.get("/tokens/max/{tokens}")
async def tokensMax (tokens=None):  
    '''
    This function sets the maximum number of allowed tokens to be
    returned by the model. Note that this is not persistent. 
    So there is no change to the original configuration file

    Routes:
        @app.get("/tokens/max")

        @app.get("/tokens/max/{tokens}")

    Args:
        tokens : int = 
            The maximum number of allowed tokens to be used 
            by the model. This is an optiona argument. 
            If no value is given then return the number of
            tokens
    
    Returns:
        response : bool or int = 
            Returns true if successfully set, otherwise returns
            false. Alternaatively returns number of tokens
            if no tokens given. 
    '''
    global config, config_file
    
    # Sets the number of max tokens in the config file
    # and for subsequent queries to llm
    if (tokens):
        # Set the max_tokens for the current model.
        config['llm_maxtokens']=tokens
        
        # Store the updated config into file
        configStore(config_file, config)

        return True

    # Returns the number of max tokens set in the
    # configuration file
    else:
        return config['llm_maxtokens']

#-----------------------------------------------------------------------
# CONFIGLOAD
#-----------------------------------------------------------------------
def configLoad(config_file):
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
    # Load the configuration file to get running parameters
    with open(config_file, 'r') as json_file:
        config = json.load(json_file)
    
    # Return dictionary
    return config

#-----------------------------------------------------------------------
# CONFIGSTORE
#-----------------------------------------------------------------------
def configStore (config_file, config_data):
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
        json.dump(config_data, json_file, indent=4)

#-----------------------------------------------------------------------
# RUN
#-----------------------------------------------------------------------
def run(host, port):
    '''
    This function should be called to start the server side api microservice 
    for the backend. 

    Args:
        host : str = 
            The host ip address passed in as a string

        port : str = 
            The host port passed in as a string 

    Returns:
        process : Popen = 
            Returns an instance of the process in case we need to kill later.
    '''
    uvicorn.run(app, host=host, port=int(port), log_level="info")   

#-----------------------------------------------------------------------
# MAIN
#-----------------------------------------------------------------------
def main():
    '''
    This is the main function. It grabs the config data, historical data
    for the conversation and stores it in a set of globals. The web
    server is then run and operates until the user uses a keyboard interrupt
    to break the execution. 
    '''
    global config, config_file

    # Load the configuration fille to get running parameters
    config=configLoad(config_file)
    
    # Load the table of conversation histories from the 
    # SQLite database
    historyLoad()

    # Run the LLM model server as a microservice
    try:
        run(host=config["api_host"], port=config["api_port"])
    except KeyboardInterrupt as e:
        logger.info ('Terminating server')


if __name__ == "__main__":
    main()
        