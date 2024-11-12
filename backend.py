# pip install pandas, noaa-coops, astral, datetime

from datetime import datetime
import pandas as pd
from noaa_coops import Station
from astral import LocationInfo
from astral.sun import sun

# Create function to convert date format '%Y-%m-%d' (html form) to %Y%m%d (noaa coops)
def convert_date(date_form):
    # Parse the date string to a datetime object
    # strptime = string parse time # This is a class method, not an instance method
    # '%Y-%m-%d' specifies the expected format of the input date string
    date = datetime.strptime(date_form, '%Y-%m-%d')
    # Convert the datetime object to the required format
    # strftime = string format time
    return date.strftime('%Y%m%d')

# Create function to filter tide data based on html form entry
def tide_analysis(location, tideHeight, beginDate, endDate, days, tideType, timeOfDay):
    
    # Use convert_date to convert the format of beginDate and endDate for noaa coops
    begin_date = convert_date(beginDate)
    end_date = convert_date(endDate)

    # Map day names to their corresponding integer values for ease of data filtration
    day_name_to_int = {
        'Monday': 0,
        'Tuesday': 1,
        'Wednesday': 2,
        'Thursday': 3,
        'Friday': 4,
        'Saturday': 5,
        'Sunday': 6
    }
    days_int = [day_name_to_int[day] for day in days]

    # Read location database
    location_db = pd.read_csv('location_db.csv')
    
    # Lookup location details from location_db
    # 1. Filter data to only show the row that matches the location
    # 2. Use .iloc[0] to create a series with index and data (i.e. state - california
    # key value pair)
    loc_details = location_db[location_db['location'] == location].iloc[0]
    
    # Assigning python variables based on series pairs
    city = loc_details['city']
    state = loc_details['state']
    timezone = loc_details['timezone']
    latitude = loc_details['latitude']
    longitude = loc_details['longitude']
    station_id = loc_details['station_id']
    
    # Fetch Tide Data using noaa_coops package

    # Create an instance of the Station class
    station = Station(station_id)
    # Use get_data method to obtain tide data
    tide_data = station.get_data(
        begin_date = begin_date,
        end_date = end_date,
        product = 'predictions',
        datum = 'MLLW',  # standard tide datum
        units = 'english', 
        time_zone = 'lst_ldt',  # local standard time accounting for daylight savings
        interval = 'hilo'  # returns high and low tides only
    )
    
    # Convert .json tide_data to Pandas DataFrame
    # An instance of Dataframe class is created
    df = pd.DataFrame(tide_data)

    # print(df)

    # Rename columns 1 and 2
    df.columns = ['Tide height (ft)', 'H or L']

    # Set the index to be a datetime format
    df.index = pd.to_datetime(df.index)

    # Filter based on tide type
    if tideType == "Low":
        filtered_tides = df[
            (df['H or L'] == 'L') &
            (df['Tide height (ft)'] <= tideHeight) &
            (df.index.weekday.isin(days_int))
        ]
    else:  # High tide
        filtered_tides = df[
            # Tide type filter
            (df['H or L'] == 'H') &
            # Tide height filter
            (df['Tide height (ft)'] >= tideHeight) &
            # Days of the week filter. Converts index (date) column to weekday in terms of integer
            # isin provides boolean TRUE output if the date is any of the days specified in days_int
            # weekday is a property; special attribute with customized access and modification
            # index is an attribute of the df data frame 
            (df.index.weekday.isin(days_int))
        ]

    # print(filtered_tides)
    
    # Fetch sun data using astral package and use it to filter out tides that occur during the dark

    # Create an instance of the LocationInfo class
    city = LocationInfo(city, state, timezone, latitude=latitude, longitude=longitude)
    
    # Create dictionary of sunrise and sunset times for the dates in the filtered_tides data
    # The outer dictionary keys are dates. The inner dictionary keys are sunrise, sunset, timezone
    # sun() is a function from astal.sun that extracts sunrise and sunset
    sunrise_sunset = {
        date: sun(city.observer, date=date, tzinfo=city.tzinfo) for date in filtered_tides.index.date
    }
    
    # print(sunrise_sunset)

    def filter_sunrise_sunset(row):
        date = row.name.date()
        sunrise = sunrise_sunset[date]['sunrise']
        sunset = sunrise_sunset[date]['sunset']

        if timeOfDay == "Daylight":
            sunrise_adjusted = sunrise - pd.Timedelta(hours=1)
            sunset_adjusted = sunset + pd.Timedelta(hours=1)
            is_between = sunrise_adjusted.time() < row.name.time() < sunset_adjusted.time()
        elif timeOfDay == "Night":
            sunrise_adjusted = sunrise + pd.Timedelta(hours=1)
            sunset_adjusted = sunset - pd.Timedelta(hours=1)
            is_between = not (sunrise_adjusted.time() < row.name.time() < sunset_adjusted.time())
        else:
            is_between = True

        if is_between:
            return pd.Series({
                'Tide Time': row.name.strftime('%Y-%m-%d %H:%M'),
                'Day of the week': row.name.day_name(),
                'Tide height (ft)': row['Tide height (ft)'],
                'Sunrise': sunrise.strftime('%Y-%m-%d %H:%M'),
                'Sunset': sunset.strftime('%Y-%m-%d %H:%M')
            })
        else:
            return pd.Series({
                'Tide Time': None,
                'Day of the week': None,
                'Tide height (ft)': None,
                'Sunrise': None,
                'Sunset': None
            })

    # def filter_sunrise_sunset(row):
    #     date = row.name.date()
    #     sunrise = sunrise_sunset[date]['sunrise']
    #     sunset = sunrise_sunset[date]['sunset']
    #     # Adjust sunrise and sunset times
    #     sunrise_adjusted = sunrise - pd.Timedelta(hours=1)  # 1 hour before sunrise
    #     sunset_adjusted = sunset + pd.Timedelta(hours=1)    # 1 hour after sunset

    #     # Check if tide time is between adjusted sunrise and sunset
    #     is_between = sunrise_adjusted.time() < row.name.time() < sunset_adjusted.time()
        
    #     day = row.name.day_name()

    #     # Return data if it's within the desired time range
    #     if is_between:
    #         return pd.Series({
    #             'Tide Time': row.name.strftime('%Y-%m-%d %H:%M'),
    #             'Day of the week': day,
    #             'Tide height (ft)': row['Tide height (ft)'],
    #             'Sunrise': sunrise.strftime('%Y-%m-%d %H:%M'),
    #             'Sunset': sunset.strftime('%Y-%m-%d %H:%M')
    #         })
    #     else:
    #         return pd.Series({
    #             'Tide Time': None,
    #             'Day of the week': None,
    #             'Tide height (ft)': None,
    #             'Sunrise': None,
    #             'Sunset': None
    #         })

    # Apply the function and create a new DataFrame
    results_df = filtered_tides.apply(filter_sunrise_sunset, axis=1).dropna()
    
    # print(results_df)
    # print(type(results_df))

    return results_df

# # Test inputs
# location = 'San Francisco, CA'
# tideType = 'High'
# tideHeight = 6.5
# beginDate = '2024-11-06'
# endDate = '2025-11-30'
# days = ['Saturday', 'Sunday']
# timeOfDay = 'Daylight'

# tide_analysis(location, tideHeight, beginDate, endDate, days, tideType, timeOfDay)
