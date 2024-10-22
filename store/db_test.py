# User on-boarding payload 
# {
#     "id": 123,
#     "name": "ram kumar",
#     "address": "#2 some street, some town, some state", 
#     "farms": [
#         {
#             "crops": ["rice", "cucumber"],
#             # Each element of this list is a point on the boundry of the farm.
#             # If there is only one element, assume it's some point in a 
#             # 1 hectare (~30m x 30m) farm. 
#             "gps": [(12.977179, 77.639163),],
#         }
#     ]
# }

# Payment payload 
# {
#     "details": "roti sabzi",
#     "category": "food",
#     "cost": 100.0,
#     "user_id": 123, 
# }