import os
from openai import OpenAI
import gradio as gr  # Image Understanding and Web UI
import requests
import googlemaps
from gradio.components import HTML

# get location
def get_location_data(location, api_key):
    """
    for QWeather API sent GET to ask for weather data.

    :param location: name or geocode（For example:"beijing" or "116.405285,39.904989"）
    :param api_key: my QWeather API key
    :return: responded JSON data
    """
    # Generate request URL
    url = f"https://geoapi.qweather.com/v2/city/lookup?location={location}&key={api_key}"

    # Sent GET request
    response = requests.get(url)

    # Check respond state code
    if response.status_code == 200:
        # return JSON data
        return response.json()
    else:
        # error process
        print(f"Request failed，State Code:{response.status_code}")
        print(response.text)
        return None
# get weather
def get_weather_forecast(location_id, api_key):
    """
    For QWeather API sent request for the future 3 days weather forcast.

    paradigms:
    - location: Position ID or Lat and Lng
    - api_key: My QWeather API key
    - duration: forcast time size:'3d' or '7d'

    return:
    - respond JSON data
    """

    # Generate request link
    url = f"https://devapi.qweather.com/v7/weather/3d?location={location_id}&key={api_key}"

    # Sent GET request
    response = requests.get(url)

    # Check request if success or not
    if response.status_code == 200:
        # return responed JSON data
        return response.json()
    else:
        # If request failed, print error message
        print(f"request failed, state code:{response.status_code}，error message:{response.text}")
        return None

G_api_key = os.getenv('GOOGLE_MAPS_API_KEY')

gmaps = googlemaps.Client(key= G_api_key)

# Geocoding an address
def get_geocoding(input_address):
    geocode_result = gmaps.geocode(input_address)
    lat = geocode_result[0]['geometry']['location']['lat']
    lng = geocode_result[0]['geometry']['location']['lng']

    return (lat,lng)

# get recommand restaurant for address
def get_recommandation(input_address): # for restaurant
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    lat,lng = get_geocoding(input_address)

    api_key = os.getenv('GOOGLE_MAPS_API_KEY')

    params = {
        "location": f"{lat},{lng}",
        "radius": "1500",
        "type": "restaurant",  # restaurant or shopping_mall
        "keyword": "eating",  # eating
        "key": api_key  # my gmaps key
    }

    # Sent GET request
    response = requests.get(url, params=params)

    # check respond state code
    if response.status_code == 200:
        # analyze JSON data
        json_data = response.json()
        names_array = [result["name"] for result in json_data["results"]]
        names_str = "\n".join(names_array)  # use \n to splite the names
        return names_str
        # list to save names
        # names_array = []
        #
        # # get stores name and save in list
        # for result in json_data["results"]:
        #     names_array.append(result["name"])
        # return names_array
        # get store name
        # for result in json_data["results"]:
        #     return (result["name"])

    else:
        print("Failed to fetch data. Status code:", response.status_code)
        return None

# get recommand shopping mall for address
def get_shopping_mall(input_address):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    lat, lng = get_geocoding(input_address)

    api_key = os.getenv('GOOGLE_MAPS_API_KEY')

    params = {
        "location": f"{lat},{lng}",
        "radius": "1500",
        "type": "shopping_mall",  # restaurant or shopping_mall
        "keyword": "",  # eating
        "key": api_key  # my gmaps key
    }

    # sent GET request
    response = requests.get(url, params=params)

    # check respond state code
    if response.status_code == 200:
        # analyze JSON data
        json_data = response.json()
        names_array = [result["name"] for result in json_data["results"]]
        names_str = "\n".join(names_array)  # use \n to splite names
        return names_str

    else:
        print("Failed to fetch data. Status code:", response.status_code)
        return None

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def process_network(input_question):
    response = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": f"{input_question}",
        }],
        model="gpt-4o",
    )
    return response.choices[0].message.content

def Exp_what_2_play(destination, departure_date, back_date):
    url = f"https://www.expedia.com/things-to-do/search?location={destination}&sort=RECOMMENDED&swp=on&startDate={departure_date}&endDate={back_date}"
    return url

def chat_with_gpt(chat_destination, chat_history, chat_departure, chat_departure_date, chat_back_date, chat_style, chat_budget, chat_people,
                  chat_other):
    # Formatting Prompt Message
    prompt = (
        "chat_departure:{}，chat_destination:{} ，chat_departure_date:{} ， chat_back_date:{}. chat_style:{} ，chat_budget:{}，chat_people:{}，other requirements:{}"
        .format(chat_departure, chat_destination, chat_departure_date, chat_back_date, chat_style, chat_budget, chat_people, chat_other)
    )

    # append into history
    chat_history.append((chat_destination, ''))

    # use gpt 4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f'''
            You are now a professional travel planner and your responsibility is to help me plan my travel itinerary and generate a detailed travel schedule based on travel origin, destination, starting date, ending date, trip style (compact, moderate, casual), budget, and number of people. Please present the results in a tabular format. The table header of the travel planner please include date, location, itinerary plan, mode of transportation, meal arrangement, accommodation arrangement, cost estimation, and links. All headers are mandatory, so please deepen your thought process and strictly adhere to the following rules:
            1. The date should show in form: MM/DD/YYYY, for example: 04/27/2025，clearly mark each day's itinerary.
            2. The location needs to present the city of the day, please make the location strictly and reasonably according to the date, considering the geographical proximity of the location to ensure a smooth trip.
            3. The trip plan needs to include location, time, and activities, where location needs to be sorted according to geographic proximity. The number of locations can be flexibly adjusted according to the style of the trip, e.g. less locations for casual and more for compact. Time needs to be developed according to morning, noon, and evening, and give the time spent at each location (e.g., 10 a.m.-12 p.m.). Activities need to accurately describe the corresponding activities occurring at the location (e.g., visiting museums, touring parks, eating, etc.), and the type of activity needs to be rationalized based on the length of stay at the location.
            4. The mode of transportation needs to be reasonably chosen according to the geographical distance of the location, each location in the trip plan, such as walking, subway, taxi, train, plane, and other different modes of transportation, and described in as much detail as possible.
            5. Dining arrangements need to include recommended restaurants, type (e.g., local specialty, fast food, etc.), and budget range for each meal, near you.
            6. Accommodation arrangements need to include the recommended hotel or type of accommodation (e.g. hotel, B&B, etc.), address, and estimated cost for each night, near you.
            7. The cost estimate needs to include the estimated total cost per day with a breakdown of each cost (e.g. transportation, meals, entrance fees, etc.).
            8. Please give special consideration to entourage size information to ensure that the itinerary and accommodation arrangements meet the needs of all entourage members.
            9.The overall cost of the tour should not exceed the budget.
            10.My input departure date如:04/27/2025 is in the form MM/DD/YYYY, represent 04 month 27 day 2025 year；same as the back date。
            11.You should calculate how many day it take to travel from my input departure date and back date ( including departure date and back date).
            Now please follow the above rules strictly and generate a reasonable and detailed travel planner based on my travel origin, destination, departure date, back date, itinerary style (compact, moderate, casual), budget, and number of people accompanying you.
            Remember you have to generate the travel planner in tabular form based on the information I provided such as travel destination, departure date, back date, etc. The final answer must be in tabular form, there is no need for a Remarks column, each itinerary plan for morning,afternoon and evening should start with a new line/row,
            the last column with title "Links" and the contents should include:
            If the transportation contain flight, since you know the chat_departure, call it "F" , chat_destination, call it "T", chat_departure_date, call it "FD", chat_back_date, call it "TD", chat_people, call it "P",
            then write down this link: "https://www.expedia.com/Flights-Search?flight-type=on&mode=search&trip=roundtrip&leg1=from:F,to:T,departure:FD,fromType:M,toType:M&leg2=from:T,to:F,departure:TD,fromType:M,toType:M&options=cabinclass:economy&fromDate=FD&toDate=TD&passengers=adults:P,infantinlap:N";
            If the transportation contain Metro or train, then call the beginning place "BEG" and call the destination "DES", write down this link: "https://www.google.com/maps/dir/BEG/DES";
            If the accommodation is in the destination city, call the accommodation place "A", for every day of the accommodation, write down this link: "https://www.google.com/maps/search/A";
            If there is a dining place for that day, call it "B", then write down this link: "https://www.google.com/maps/search/B";
            For each place in the Itinerary plan, call the place "C", write down the link:"https://www.google.com/maps/search/C" in each coordinate line for morning, afternoon and evening;
            answered in English.
            '''},
            {"role": "user", "content": prompt}
        ]
    )

    # get answer
    answer = response.choices[0].message.content

    # update history
    information = (
        "departure:{}，destination:{} ，departure date:{} ，back date:{} , style:{} ，budget:{}，people:{}"
        .format(chat_departure, chat_destination, chat_departure_date, chat_back_date, chat_style, chat_budget, chat_people)
    )
    chat_history[-1] = (information, answer)

    return  chat_history # answer,

css=""" 
#col-left {
    margin: 0 auto;
    max-width: 430px;
}
#col-mid {
    margin: 0 auto;
    max-width: 430px;
}
#col-right {
    margin: 0 auto;
    max-width: 430px;
}
#col-showcase {
    margin: 0 auto;
    max-width: 1100px;
}
#button {
    color: blue;
}

"""
# gr.set_static_paths(paths=["static"])
# image_path = "static/logo.png"

# manage gradio window
with (gr.Blocks(css=css) as demo):
    html_code = """
     <!DOCTYPE html>
        <html lang="en-US">        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 10px;
                }
                .container {
                    max-width: 1500px;
                    margin: auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    padding: 10px;
                }
                .logo img {
                    display: block;
                    margin: 0 auto;
                    border-radius: 7px;
                }
                .content h2 {
                    text-align: center;
                    color: #999999;
                    font-size: 24px;
                    margin-top: 20px;
                }
                .content p {
                    text-align: center;
                    color: #cccccc;
                    font-size: 16px;
                    line-height: 1.5;
                    margin-top: 30px;
                }
            </style>
        </head>
    <body>
            <div class="container">
                <div class="logo">
                    <img src="https://img.picui.cn/free/2024/11/13/67347d3094fae.png" alt="Logo" width="30%">
                </div>
                <div class="content">
                    <h2>😀 Welcome to “6221Traval AI”，Your dedicated travel companion! We are committed to providing you with personalized travel planning, companionship and sharing services to make your journey fun and memorable.\n</h2>     
                </div>
            </div>
    </body>
"""
    gr.HTML(html_code) #manage the page

    with gr.Tab("Travel Planner"):
        # with gr.Group():
        with gr.Row():
            chat_departure = gr.Textbox(label="Enter the tour departure point", placeholder="Please enter your departure point")
            gr.Examples(["Beijing", "Washington", "New York", "Tokyo", "Paris", "London"],chat_departure, label='departure example', examples_per_page=6)
            chat_destination = gr.Textbox(label="Enter your travel destination", placeholder="Please enter the place you want to go")
            gr.Examples(["Beijing", "Washington", "New York", "Tokyo", "Paris", "London"],chat_destination, label='destination example', examples_per_page=6)

        with gr.Accordion("Personalized options (number of days, itinerary style, budget, number of participants)", open=False):
            with gr.Group():
                with gr.Row():
                    chat_departure_date = gr.Textbox(label="Enter departure date(in MM/DD/YYYY)", placeholder="Please enter your departure date")
                    # chat days = gr.Slider(minimum=1, maximum=20, step=1, value=3, label='Number of travel days')
                    chat_back_date = gr.Textbox(label="Enter back date(in MM/DD/YYYY)", placeholder="Please enter your back date")
                    chat_style = gr.Radio(choices=['Compact', 'Moderate', 'Leisure'], value='Moderate', label='Trip Style',elem_id="button")
                    chat_budget = gr.Textbox(label="Enter budget (with units)", placeholder="Please enter your budget")
                with gr.Row():
                    chat_people = gr.Textbox(label="Enter the number of participants", placeholder="Please enter your number of participants")
                    chat_other = gr.Textbox(label="Special preferences, requirements (may write none)", placeholder="Please write your special preferences, requirements")
                # chatting window
        llm_submit_tab = gr.Button("Submit", visible=True, elem_id="button")
        chatbot = gr.Chatbot([], elem_id="chat-box", label="Chatting-window", height=600)
        # click logic
        llm_submit_tab.click(fn=chat_with_gpt,
                             inputs=[chat_destination, chatbot, chat_departure, chat_departure_date, chat_back_date, chat_style, chat_budget,
                                     chat_people, chat_other], outputs=[chatbot]) #outputs=[chat_destination,chatbot]

    with gr.Tab("Travel Q&A agency"):
        Weather_APP_KEY = '797ab5e76cdf458b82b1283e100b9a5b'

        def weather_process(location):
            api_key = Weather_APP_KEY  # Hefeng_API_KEY
            location_data = get_location_data(location, api_key)
            # print(location_data)
            if not location_data:
                return "Unable to get city information, please check your input."
            location_id = location_data.get('location', [{}])[0].get('id')
            # print(location_id)
            if not location_id:
                return "Unable to get ID from city info."
            weather_data = get_weather_forecast(location_id, api_key)
            if not weather_data or weather_data.get('code') != '200':
                return "Cannot get weather forecast, please check your input and API key."
            # Building HTML tables to display weather data
            html_content = "<table>"
            html_content += "<tr>"
            html_content += "<th>DATE</th>"
            html_content += "<th>TEMPDay</th>"
            html_content += "<th>TEMPNight</th>"
            html_content += "<th>tempMax</th>"
            html_content += "<th>tempMin</th>"
            html_content += "<th>windDirDay</th>"
            html_content += "<th>windScaleDay</th>"
            html_content += "<th>windSpeedDay</th>"
            html_content += "<th>windDirNight</th>"
            html_content += "<th>windScaleNight</th>"
            html_content += "<th>windSpeedNight</th>"
            html_content += "<th>precip</th>"
            html_content += "<th>uvIndex</th>"
            html_content += "<th>humidity</th>"
            html_content += "</tr>"

            for day in weather_data.get('daily', []):
                html_content += f"<tr>"
                html_content += f"<td>{day['fxDate']}</td>"
                html_content += f"<td>{day['textDay']} ({day['iconDay']})</td>"
                html_content += f"<td>{day['textNight']} ({day['iconNight']})</td>"
                html_content += f"<td>{day['tempMax']}°C</td>"
                html_content += f"<td>{day['tempMin']}°C</td>"
                html_content += f"<td>{day.get('windDirDay', '未知')}</td>"
                html_content += f"<td>{day.get('windScaleDay', '未知')}</td>"
                html_content += f"<td>{day.get('windSpeedDay', '未知')} km/h</td>"
                html_content += f"<td>{day.get('windDirNight', '未知')}</td>"
                html_content += f"<td>{day.get('windScaleNight', '未知')}</td>"
                html_content += f"<td>{day.get('windSpeedNight', '未知')} km/h</td>"
                html_content += f"<td>{day.get('precip', '未知')} mm</td>"
                html_content += f"<td>{day.get('uvIndex', '未知')}</td>"
                html_content += f"<td>{day.get('humidity', '未知')}%</td>"
                html_content += "</tr>"
            html_content += "</table>"

            return HTML(html_content)

        with gr.Tab("Weather Search"):

            weather_input = gr.Textbox(label="Please enter the city name to check the weather", placeholder="For example: Washington DC")
            weather_output = gr.HTML(value="", label="Weather Check Results")
            query_button = gr.Button("Check Weather", elem_id="button")
            query_button.click(weather_process, [weather_input], [weather_output])

        with gr.Tab("Neighborhood Search "):
            with gr.Row():
                with gr.Column():
                    query_near = gr.Textbox(label="Search nearby restaurant",
                                            placeholder="Example: 1600 Amphitheatre Parkway, Mountain View, CA")
                    result = gr.Textbox(label="result", lines=2)
                    submit_btn = gr.Button("Search nearby restaurant", elem_id="button")

                    submit_btn.click(get_recommandation, inputs=[query_near], outputs=[result])

                with gr.Column():
                    query_near = gr.Textbox(label="Search nearby shopping mall",
                                            placeholder="Example: 1600 Amphitheatre Parkway, Mountain View, CA")
                    result = gr.Textbox(label="result", lines=2)
                    submit_btn = gr.Button("Search nearby restaurant", elem_id="button")

                    submit_btn.click(get_shopping_mall, inputs=[query_near], outputs=[result])

        with gr.Tab("Recommended Activities"):
            with gr.Row():
                chat_destination = gr.Textbox(label="Enter your travel destination",
                                              placeholder="Please enter the place you want to go")
                gr.Examples(["Beijing", "Washington", "New York", "Tokyo", "Paris", "London"], chat_destination,
                            label='destination example', examples_per_page=6)
                chat_departure_date = gr.Textbox(label="Enter departure date(in MM/DD/YYYY)",
                                             placeholder="Please enter your departure date")
                chat_back_date = gr.Textbox(label="Enter back date(in MM/DD/YYYY)",
                                        placeholder="Please enter your back date")

            result_network = gr.Textbox(label="Searching result", lines=2)

            submit_btn_network = gr.Button("Recommended Activities(link to Expedia)", elem_id="button")
            submit_btn_network.click(fn = Exp_what_2_play, inputs=[chat_destination, chat_departure_date, chat_back_date], outputs=[result_network])

        with gr.Tab("Other Questions"):
            query_network = gr.Textbox(label="Other Questions", placeholder="Example:the famous places in Washington")
            result_network = gr.Textbox(label="Searching result", lines=2)

            submit_btn_network = gr.Button("Other Question", elem_id="button")
            submit_btn_network.click(process_network, inputs=[query_network], outputs=[result_network])

if __name__ == "__main__":
    demo.queue().launch( share=True)
