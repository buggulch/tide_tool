# pip install flask, flask cors, pandas
from flask import Flask, request, jsonify
from backend import tide_analysis
from flask_cors import CORS

# creating Flask application by creating an instance of the Flask class
# __name__ is passed as an argument to the Flask constructor. This helps 
# Flask to determine the root path of the application, which is useful 
# for locating resources like templates and static files.
app = Flask(__name__)

cors = CORS(app, resources={r"/*": {"origins": "*"}})

# calls route method within the flask class
# @app.route is a decorator (@) that maps (binds) the url to the python function
# when a request is made to the url flask calls the submit_form function
# POST request sends data in the body not in the URL. Better for when you
# need to send large amounts of data in the request. Get requests only include
# request data in the url. The response if different from the request.
@app.route('/submit-form', methods=['POST'])

def submit_form():
    
    # data sent to server in json form via post request
    # In Flask, the request object is an instance of the Request class, which contains 
    # all the information about the incoming HTTP request. json is the attribute used to 
    # access the json data
    data = request.json
   
    # Pulling data from json dictionary
    # get is a built in python method that allows you to retrieve the value associated 
    # with a specific key
    # using get to define python variables for function
    location = data.get('location') # String
    tideHeight = float(data.get('tideHeight')) # Need in float form to use in backend code
    beginDate = data.get('beginDate') # String (date)
    endDate = data.get('endDate') # String (date)
    days = data.get('days') # List of strings
    tideType = data.get('tideType') # String

    # Call the function from tidev4.py. Using variables retrieved above
    result = tide_analysis(location, tideHeight, beginDate, endDate, days, tideType)


    #returning a result to the gui. Converts python variables to json string
    # result.to_dict(orient='records') converts the result pandas dataframe
    # to a dictionary that can be handled by jsonify
    # jsonify converts the result dictionary to json format
    # data is sent to the gui as a json object, not string. This is required for
    # implementing javascript that converts result dictionary to an html table
    return jsonify({"message": "Form data received", "result": result.to_dict(orient='records')})

# run the app if its __name__ = __main__
# the app wont run if it is called upon as a module in a different script
if __name__ == '__main__':
    app.run() # Calls the run method within the flask class