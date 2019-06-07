"""
    CAAQMS API

    Access the CAAQMS API via Python.
"""
import base64
import time
import datetime
import dateutil.parser
import dateutil.tz as tz
import requests

from containers import Station

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Supress InsecureRequestWarning

GET_STATION_PARAMETER_TIMESTAMP_FORMAT = '%d %b %Y, %H:%M' # 05 Mar 2019, 23:15
GET_STATION_INFO_TIMESTAMP_FORMAT = '%d %b %Y %H:%M' # 05 Mar 2019 23:15

string_to_datetime = (lambda time_string: dateutil.parser.parse(time_string).replace(tzinfo=tz.gettz('Asia/Kolkata')) )
datetime_to_string = (lambda timestamp, format: timestamp.strftime(format))

class PollutionAPI(object):
    """
        Scrape and store API Response from CPCB All India CAAQMS Portal.
        URL: https://app.cpcbccr.com
        URI: /caaqms/caaqms_landing_map_all

        Response
        ----
            Content-Type: json

            JSON Structure

            /caaqms/caaqms_landing_map_all
            {
                "map": {
                    "timestamp": <str:"05-03-2019 22:25:49" data timestamp (app format)>,
                    "station_list": [<station>]
                }
            }
            <station>
            {
                "ip_address": [<str:list of ip addresses],
                "station_id": <str:station_id(?)>,
                "aqi_info": {
                    "aqi_status": <str:"NA"(?)>
                },
                "station_type": <str:"CAAQMS"(?)>,
                "data_format": <str:"CSV"(?)>,
                "time_stamp": <str: ISO Format Time">,
                "vendor": <str:""(?)>,
                "Ambient": {
                    "AAQMS": {
                        "validation_status": <str:"Success"(?)>,
                        "parameter_map": [<parameter_map>]
                    }
                },
                "parameter_latest_update_date": <str:"2018-06-28 04:45:00" paramter update timestamp (app format)>,
                "status": <str:"Live" status of sensor>,
                "station_name": <str: "DTU, Delhi - CPCB">,
                "latitude": <str:latitude>,
                "longitude": <str:longitude>
            }
            <parameter_map>
            {
                "parameter_name": <str: "WS" parameter name from <parameters> >,
                "last_updated": <str: "2019-03-05 22:00:00" app format timetamp string>,
                "data_quality": <str: "U"(?)>,
                "remark": <str: "0" (?)>,
                "value": <str: "0.72">
            }
            <parameters>
            WS
            RF
            PM25
            SR
            RH
            Temp
            MP_Xylene
            Oxylene
            Ethyle
            Toulene (Toluene)
            Benzene
            PM10
            SO2
            Ozone
            CO
            NH3
            NOX
            WD
            NO2
            NO

            /caaqms/caaqms_viewdata_v2
            {
                'siteInfo': {
                    'photo': <str: image link (usually not there)>,
                    'siteName': <str: name of site>,
                    'address': <str: address of site>,
                    'lastUpdateddatetime': <str: timestamp of last update>,
                    'siteId': <str: station id>,
                    "city": <str: "Kaithal">,
                    "state":  <str: "Haryana">,
                    "stationType": <str: "CAAQMS">,
                    "stationStatus": <str: "Live">,
                    "parameters": <str: 21, no of parameters>,
                    "dataAvailPerc": <str: "84.13 % (?)>"
                }
                'tableData': {
                    'headers': [{<headers for columns in next key}],
                    'bodyContent': [list of <parameter> >]
                }
            }
            <parameter>
            {
                "parameters": <str: "PM2.5" pollutant>,
                "date": <str: "06 Mar 2019">,
                "time": <str: "00:15">,
                "fromDate": <str: "06 Mar 2019 00:15">,
                "toDate": <str: "06 Mar 2019 00:30">,
                "concentration": <decimal: 39.01>,
                "unit": <str: "ug/m3">,
                "Concentration_24Hr": <decimal: 55.39, avg conc over 24 Hr>,
                "remark": <str: "" (?)>
            },

    """
    UA = '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'''
    
    URL = 'https://app.cpcbccr.com'

    DEFAULT_HEADERS = {
        'User-Agent': UA
    }

    ALL_STATIONS_RESOURCE = {
        'URI': '/caaqms/caaqms_landing_map_all',
        'POST_DATA': 'eyJyZWdpb24iOiJsYW5kaW5nX2Rhc2hib2FyZCJ9'
    }

    STATION_VIEW_DATA_RESOURCE = {
        'URI': '/caaqms/caaqms_viewdata_v2',
        'POST_DATA': (lambda site_id: base64.b64encode(f'''{{"site_id":"{site_id}","user_id":"user_211","user_name":"KSPCB","user_role":"Admin","org":["KSPCB"]}}'''.encode()).decode())
    }

    STATION_DELTA_DATA_RESOURCE = {
        'URI': '/caaqms/caaqms_load_delta_v2',
        'POST_DATA': (lambda site_id, delta, time_stamp: base64.b64encode(f'''{{"delta":"{delta}","time_stamp":"{time_stamp}","site_id":"{site_id}"}}'''.encode()).decode())
    }


    def __init__(self, *args, **kwargs):
        self.stations = {}

    def _get(self, URI, *args, **kwargs):
        headers = kwargs.pop('headers', None)
        if headers is None:
            headers = self.DEFAULT_HEADERS
        else:
            headers.update(self.DEFAULT_HEADERS)

        return requests.get(self.URL+URI, headers=headers, verify=False, *args, **kwargs)

    def _post(self, URI, *args, **kwargs):
        headers = kwargs.pop('headers', None)
        if headers is None:
            headers = self.DEFAULT_HEADERS
        else:
            headers.update(self.DEFAULT_HEADERS)
        
        return requests.post(self.URL+URI, headers=headers, verify=False, *args, **kwargs)

    def get_all_stations(self, *args, **kwargs):
        """
            get data for all stations

            return dict station: `/caaqms/caaqms_landing_map_all` JSON Response
        """
        payload = self.ALL_STATIONS_RESOURCE['POST_DATA']
        request = self._post(
            self.ALL_STATIONS_RESOURCE['URI'], 
            data=payload
        )
        
        json_data = request.json()
        stations = json_data['map']['station_list']

        self.stations = stations

        return stations

    def get_station_data(self, site_id, *args, **kwargs):
        """
        get station_data for a `site_id`

        return dict site_data: {
            'site_data': <site information>,
            'parameters': <parameters>
        }
        """
        payload = self.STATION_VIEW_DATA_RESOURCE['POST_DATA'](site_id)
        request = self._post(
            self.STATION_VIEW_DATA_RESOURCE['URI'], 
            data=payload
        )

        json_data = request.json()
        site_info_key = 'siteInfo'
        table_data_key = 'tableData'
        body_content_key = 'bodyContent'

        site_data = {
            'site_data': json_data[site_info_key],
            'parameters': json_data[table_data_key][body_content_key]
        }

        return site_data

    # def get_station_delta(self, site_id, delta, time_stamp, *args, **kwargs):
    #     """
    #         get historical data based on delta.
    #     """
    #     payload = self.STATION_VIEW_DATA_RESOURCE['POST_DATA'](site_id, delta, time_stamp)
    #     request = self._post(self.STATION_VIEW_DATA_RESOURCE['URI'], data=payload)

    #     json_data = request.json()

    #     site_info_key = 'siteInfo'
    #     table_data_key = 'tableData'
    #     body_content_key = 'bodyContent'

    #     site_data = {
    #         'site_data': json_data[site_info_key],
    #         'parameters': json_data[table_data_key][body_content_key]
    #     }

    #     return site_data

def get_station(json_data, *args, **kwargs):
    """
        Transform get_station_data responses.
    """
    station_data = {
        'station_id': json_data['site_data']['siteId'],
        'address': json_data['site_data']['address'],
        'time_stamp': json_data['site_data']['lastUpdateddatetime'],
        'status': json_data['site_data']['stationStatus'],
        'station_name': json_data['site_data']['siteName'],
        'parameters': json_data['parameters']
    }

    station = Station(**station_data)
    return station

if __name__ == '__main__':
    api = PollutionAPI()
    stations = api.get_all_stations()
    station_list = []

    start = time.time()

    for station in stations:
        print(f"Collecting data for {station['station_id']}")
        start = time.time()
        data = api.get_station_data(station['station_id'])

        station_instance = get_station(data)
        print(station_instance.__dict__)
        station_list.append(station_instance)
        print(station_instance)
        print(station_instance.parameters[0].__dict__)
        printer(**station_instance.get_dict())

        end = time.time() - start
        print(f"Time taken: {end}")
        break

    end = time.time() - start
    print(f"Total Time Taken: {end}")


    for pollutant in station_list[0].parameters:
        print(f'''---- {pollutant.parameter} ----''')
        print(f'''     {pollutant.date}           ''')
        print(f'''Concentration: {pollutant.value}''')
        print('''-----------------------------------''')
