import os
import json
import redis
import random
import requests


class Address:
    def __init__(self, address: str, google_geocoding_api_key: str, redis_connection_string: str):
        if address == 'random':
            self.address = address
            self.is_cache = None
            self.response = None
            return

        self.url_base = 'https://maps.googleapis.com/maps/api/geocode/json?address='
        self.api_key = google_geocoding_api_key
        self.address = address
        self.url = self.set_url()
        self.response = None
        self.location = None
        self.status = None
        self.is_cache = None
        self.reponse_from_cache = None
        self.r = redis.from_url(redis_connection_string)

    def set_url(self):
        url = self.url_base + self.address + '&key=' + self.api_key
        return url

    def get_from_cache(self):
        self.reponse_from_cache = self.r.get(self.url)
        self.is_cache = False
        if self.reponse_from_cache:
            self.is_cache = True
            self.response = json.loads(self.reponse_from_cache)
            return

    def save_to_cache(self):
        if self.status:
            # pass
            jsn = json.dumps(self.response)
            self.r.set(self.url, jsn)

    def request(self):
        response = requests.get(self.url)
        response = response.json()
        self.response = response

    def set_status(self):
        try:
            self.response['results'][0]['geometry']['location']
            self.status = True
        except:
            self.status = False

    def set_location(self):
        if self.address == 'random':
            self.location = Location('random')
            return

        if not self.status:
            self.location = Location(None)
        else:
            self.location = Location(self.response['results'][0]['geometry']['location'])

    def print(self):
        print(self.location)

    def parse(self):
        if self.address == 'random':
            self.status = False
            self.set_location()
            self.response = None
            return

        self.get_from_cache()
        if not self.reponse_from_cache:
            self.request()
            self.set_status()
            self.save_to_cache()
            self.set_location()
            return

        self.set_status()
        self.set_location()


class Location:
    def __init__(self, location='random'):
        if location is None:
            self.lat = None
            self.lon = None

        if location == 'random':
            self.lat = random.randint(0, 90)
            self.lon = random.randint(0, 180)

        elif isinstance(location, dict):
            self.lat = location['lat']

            if 'lon' in location:
                self.lon = location['lon']

            if 'lng' in location:
                self.lon = location['lng']

        elif isinstance(location, list) or isinstance(location, tuple):
            self.lat = location[0]
            self.lon = location[1]

    def __repr__(self):
        return f'Lat = {self.lat}, lon = {self.lon}'

    def __str__(self):
        return f'Lat = {self.lat}, lon = {self.lon}'

    def print(self):
        print(f'Lat = {self.lat}, lon = {self.lon}')

    def to_dict(self):
        dct = {'lat': self.lat, 'lon': self.lon}
        return dct

    def to_list(self):
        return [self.lat, self.lon]

    def to_tuple(self):
        return (self.lat, self.lon,)


class Geocoding:
    def __init__(self):
        self.cache = dict()
        self.google_geocoding_api_key = os.getenv("GOOGLE_GEOCODING_API_KEY")
        self.redis_connection_string = os.getenv("REDIS_CONNECTION_STRING")
        self.json = None
        self.response = None
        self.response_list = None
        self.response_json = None

    def to_list(self):
        lst = list()
        for address_obj in self.response:
            dct = {'cache': address_obj.is_cache,
                   'location': address_obj.location.to_dict(),
                   'response': address_obj.response}

            lst.append(dct)

        self.response_list = lst

    def to_json(self):
        self.to_list()
        self.json = json.dumps(self.response_list)

    def get(self, address: str='random'):
        address_obj = Address(address,
                              google_geocoding_api_key=self.google_geocoding_api_key,
                              redis_connection_string=self.redis_connection_string)
        address_obj.parse()
        return address_obj

    def gets(self, addressees: list=['random']):
        address_objs = list()
        for address in addressees:
            address_obj = self.get(address)
            address_objs.append(address_obj)

        self.response = address_objs


def main(args):
    addresses = args.get("addresses")
    # addresses = json.loads(addresses)
    g = Geocoding()
    g.gets(addresses)
    g.to_json()

    return {'body': g.json}
