"""
    Containers to store acquired data.
"""

class Parameter(object):
    """
        Container for parameter
        Data:
            parameters
            date
            time
            from_date
            to_date
            concentration
            unit
            Concentration_24Hr
            remark
    """
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('parameters')

        """ Transform date """
        date = kwargs.get('date')
        time = kwargs.get('time')
        datetime_string = f'{date}, {time}'
        self.date = string_to_datetime(datetime_string) or None

        from_date_string = kwargs.get('fromDate')
        self.from_date = string_to_datetime(from_date_string) or None

        to_date_string = kwargs.get('toDate')
        self.to_date = string_to_datetime(to_date_string) or None

        self.concentration = kwargs.get('concentration', -1)
        self.unit = kwargs.get('unit', '')
        avg_conc = kwargs.get('Concentration_24Hr', -1)
        self.avg_concentration = avg_conc if type(avg_conc) == int else -1
        self.remark = kwargs.get('remark', '')

    def get_dict(self):
        return {
            'name': self.name,
            'date': self.date,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'concentration': self.concentration,
            'unit': self.unit,
            'avg_concentration': self.avg_concentration,
            'remark': self.remark
        }

    @property
    def value(self):
        return f'{self.concentration} {self.unit}'

    def __repr__(self, *args, **kwargs):
        return f"<Parameter {self.name} {self.concentration}{self.unit}>"

class Station(object):
    """
        Container for stations
        Data:
            station_name,
            station_id,
            address,
            time_stamp,
            parameters,
            status,
            latitude,
            longitude

        Accepts PollutionAPI.get_station_data response.
    """
    def __init__(self, *args, **kwargs):
        self.station_name = kwargs.get('station_name', 'N/A')
        self.station_id = kwargs.get('station_id', 'site_-1')
        self.address = kwargs.get('address', 'N/A')

        time_stamp_string = kwargs.get('time_stamp', datetime.datetime.utcnow())
        self.time_stamp = string_to_datetime(time_stamp_string)

        parameters_list = kwargs.get('parameters', [])
        self.parameters = [Parameter(**parameter_dict) for parameter_dict in parameters_list ]

        self.status = kwargs.get('status', 'N/A')

        self.latitude = kwargs.get('latitude', '')
        self.longitude = kwargs.get('longitude', '')

    def get_dict(self):
        return {
            'station_name': self.station_name,
            'station_id': self.station_id,
            'address': self.address,
            'time_stamp': self.time_stamp,
            'status': self.status,
            'latitude': self.latitude,
            'longitude': self.longitude
        }

    def __repr__(self, *args, **kwargs):
        return f"<Station {self.station_name} {self.station_id}>"