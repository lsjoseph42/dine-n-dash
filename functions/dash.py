import re
import json
import googlemaps
from datetime import datetime
import os 

API_KEY = os.environ.get("SBHACKS_GOOGLE")
gmaps = googlemaps.Client(key=API_KEY)

def extract_stop_mileage(directions_json):
    """
    directions_json: parsed JSON from Google Directions API
    Returns: dict {destination_stop: miles}
    """
    result = {}

    legs = directions_json[0]["legs"]

    # Add the starting address from the first leg
    if legs:
        result[legs[0]["start_address"]] = 0.0

    for leg in legs:
        stop = leg["end_address"]
        miles = leg["distance"]["value"] / 1609.34  # meters → miles
        result[stop] = round(miles, 2)
    
    return result

def extract_waypoints(url):
    # Extract addresses from the URL after "maps/dir/"
    match = re.search(r'maps/dir/(.+?)/@', url)
    if match:
        addresses_str = match.group(1)
        # Replace '+' with spaces and split by '/'
        waypoints = [addr.replace('+', ' ') for addr in addresses_str.split('/')]
    else:
        waypoints = []

    starting_dest = waypoints.pop(0)
    final_dest = waypoints.pop(-1)

    directions_result = gmaps.directions(starting_dest,
                                    final_dest,
                                    waypoints=waypoints,
                                    mode="driving")
    
    return extract_stop_mileage(directions_result)

def calculate_route(directions_result, start, mpg=39.5, gas_price=4, no_in_party=1): 
    # {'1 Grand Ave, San Luis Obispo, CA 93407, USA': 0.0, 'Santa Barbara, CA 93106, USA': 99.34, 'Irvine, CA 92697, USA': 147.44, '9500 Gilman Dr, La Jolla, CA 920
    total_dist_one_way = sum(directions_result.values())
    dist_from_start = sum(list(directions_result.values())[(list(directions_result.keys()).index(start) + 1):])

    print(f"One way distance: {total_dist_one_way}")
    print(f"Distance from pickup location: {dist_from_start}")

    proportional_price = (((2 * dist_from_start) / mpg) * gas_price) / no_in_party
    print(f"User pays: {proportional_price}")
    return proportional_price


url = "https://www.google.com/maps/dir/California+Polytechnic+State+University,+1+Grand+Ave,+San+Luis+Obispo,+CA+93407/University+of+California,+Santa+Barbara,+Santa+Barbara,+CA+93106/University+of+California,+Irvine,+Irvine,+CA+92697/UCSD,+Gilman+Drive,+San+Diego,+CA/@34.0860338,-120.2804358,8z/data=!3m1!4b1!4m26!4m25!1m5!1m1!1s0x80ecf1b4054c3551:0x98b3b48a29d99103!2m2!1d-120.6624942!2d35.3050053!1m5!1m1!1s0x80e93f67f3314b37:0x4e956b7e5cb6cec2!2m2!1d-119.848947!2d34.4139629!1m5!1m1!1s0x80dcde0e2592bf91:0x79fbc5d0b6dab7ec!2m2!1d-117.8411678!2d33.6429785!1m5!1m1!1s0x80dc06c4414caf4f:0xefb6aafc89913ea7!2m2!1d-117.2343605!2d32.881168!3e0?entry=ttu&g_ep=EgoyMDI2MDEwNy4wIKXMDSoASAFQAw%3D%3D"
calculate_route(extract_waypoints(url), start = '1 Grand Ave, San Luis Obispo, CA 93407, USA')