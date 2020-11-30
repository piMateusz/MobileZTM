# def load_json_from_file(path):
#     with open(path) as json_file:
#         print(f"got response from {path}")
#         data = json.load(json_file)
#         print(f"data loaded from {path}")
#         return data


# def dump_json(file, data):
#     with open(file, "w") as write_file:
#         json.dump(data, write_file)
#
#
# def clear_stops_json(url, file_path, date):
#     """ This method loads stops json from api and reduces its size.
#         It should be run only once per day to detect and apply changes """
#
#     # loading json file from url
#     data = load_json_from_url(url)
#     # removing all keys instead of these connected to date param
#     for key in [k for k in data if k != date]:
#         del data[key]
#
#     for stop in data[date]["stops"]:
#         # removing all keys instead of needed ("stopId", "stopLat", "stopLon")
#         for key in [k for k in stop if k not in ["stopId", "stopLat", "stopLon"]]:
#             del stop[key]
#     # deserialization
#     dump_json(file_path, data)
#
#
# def clear_timetable_json(file_path, date):
#     """ This method loads timetables json from api and reduces its size.
#         It should be run only once per day to detect and apply changes """
#
#     # loading routes from json file
#     routes = load_json_from_file(JSON_ROUTES_PATH)
#     for route in routes[TODAY_DATE]["routes"]:
#         temp_file_path = file_path
#         route_number = route["routeId"]
#         timetable_url = TIMETABLE_URL_1 + date + TIMETABLE_URL_2 + str(route_number)
#
#         # loading json file from timetable_url
#         data = load_json_from_url(timetable_url)
#         for stop in data[date]["stopTimes"]:
#             # TODO
#             #  routeId may be also needed (to display transport number to the user)
#             # removing all keys instead of needed ("stopId", "arrivalTime")
#             for key in [k for k in stop if k not in ["stopId", "arrivalTime"]]:
#                 del stop[key]
#         # deserialization
#         temp_file_path = temp_file_path[:-5]
#         temp_file_path += f"{str(route_number)}.json"
#         dump_json(os.path.join(JSON_TIMETABLE_DIR_PATH, temp_file_path), data)
#
#
# def clear_routes_json(url, file_path, date):
#     """ This method loads routes json from api and reduces its size.
#         It should be run only once per day to detect and apply changes """
#
#     # loading json file from url
#     data = load_json_from_url(url)
#     # removing all keys instead of these connected to date param
#     for key in [k for k in data if k != date]:
#         del data[key]
#
#     for route in data[date]["routes"]:
#         # removing all keys instead of needed ("routeId")
#         for key in [k for k in route if k != "routeId"]:
#             del route[key]
#     # deserialization
#     dump_json(file_path, data)

# def load_and_clear_data_from_api():
#     clear_stops_json(STOPS_LIST_URL, JSON_STOPS_PATH, TODAY_DATE)