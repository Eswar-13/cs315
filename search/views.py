from django.shortcuts import render
from django.db import connection
from .models import Station
from .services.path_finder import RouteService
from django.core.cache import cache

def generate_cache_key(source, dest, date_str, connected_allowed):
    return f"route_search:{source}:{dest}:{date_str}:{connected_allowed}"


def get_cached_route_data(source, dest, date_str, connected_allowed, timeout=3600):

    key = generate_cache_key(source, dest, date_str, connected_allowed)
    cached_data = cache.get(key)
    if cached_data is not None:
        return cached_data
    # Compute the data
    service = RouteService()
    data = service.find_routes(source, dest, date_str, connected_allowed)
    cache.set(key, data, timeout)
    return data


def route_search(request):
    results = []
    connecting_results = []
    source = dest = travel_date = None
    allow_connect = False

    if request.method == 'GET':
        source = request.GET.get('source')
        dest = request.GET.get('dest')
        travel_date = request.GET.get('date')
        allow_connect = request.GET.get('allow_connect') == '1'

        if source and dest and travel_date:
            route_data = get_cached_route_data(source, dest, travel_date, allow_connect)
            results = route_data['results']
            connecting_results = route_data['connecting_results']

    stations = Station.objects.all()
    return render(request, 'search/search.html', {
        'stations': stations,
        'results': results,
        'connecting_results': connecting_results,
        'source': source,
        'dest': dest,
        'date': travel_date,
        'allow_connect': allow_connect,
    })

def seconds_to_hms(seconds):
    if seconds is None:  # Handle None case
        return "00:00:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"


# def route_search(request):
#     results = []
#     connecting_results = []
#     source = dest = travel_date = None
#     allow_connect = False

#     if request.method == 'GET':
#         source = request.GET.get('source')
#         dest = request.GET.get('dest')
#         travel_date = request.GET.get('date')
#         allow_connect = request.GET.get('allow_connect') == '1'

#         if source and dest and travel_date:
#             # Direct trains
#             with connection.cursor() as cursor:
#                 query = """
#                 SELECT 
#                     t.number AS train_number,
#                     t.origin_date,
#                     src.departure_time,
#                     dest.arrival_time,
#                     t.seats_available,
#                     (dest.distance_from_src - src.distance_from_src) AS distance,
#                     CAST(
#                         (julianday(dest.arrival_time) - julianday(src.departure_time)) * 86400 
#                         AS INTEGER
#                     ) AS duration_seconds
#                 FROM 
#                     search_train t
#                     INNER JOIN search_schedule src ON t.id = src.train_id
#                     INNER JOIN search_schedule dest ON t.id = dest.train_id
#                 WHERE
#                     src.station_id = %s AND
#                     dest.station_id = %s AND
#                     date(src.departure_time) = date(%s) AND
#                     src.stop_order < dest.stop_order
#                 ORDER BY src.departure_time
#                 """
#                 cursor.execute(query, [source, dest, travel_date])
#                 columns = [col[0] for col in cursor.description]
#                 raw_results = cursor.fetchall()
#                 for row in raw_results:
#                     row_dict = dict(zip(columns, row))
#                     row_dict['duration'] = seconds_to_hms(row_dict['duration_seconds'])
#                     results.append(row_dict)

#             # Connecting trains (if allowed)
#             if allow_connect:
#                 with connection.cursor() as cursor:
#                     connect_query = """
#                     SELECT
#                         t1.number AS train1_number,
#                         t1.origin_date AS train1_date,
#                         src1.departure_time AS train1_departure,
#                         mid.arrival_time AS train1_arrival,
#                         t1.seats_available AS train1_seats,
#                         t2.number AS train2_number,
#                         t2.origin_date AS train2_date,
#                         mid2.departure_time AS train2_departure,
#                         dest.arrival_time AS train2_arrival,
#                         t2.seats_available AS train2_seats,
#                         mid.station_id AS mid_station_id,
#                         mid.distance_from_src - src1.distance_from_src AS train1_distance,
#                         dest.distance_from_src - mid2.distance_from_src AS train2_distance,
#                         CAST((julianday(mid.arrival_time) - julianday(src1.departure_time)) * 86400 AS INTEGER) AS train1_duration_seconds,
#                         CAST((julianday(dest.arrival_time) - julianday(mid2.departure_time)) * 86400 AS INTEGER) AS train2_duration_seconds,
#                         CAST((julianday(mid.arrival_time) - julianday(src1.departure_time)) * 86400 AS INTEGER) +
#                         CAST((julianday(dest.arrival_time) - julianday(mid2.departure_time)) * 86400 AS INTEGER) +
#                         CAST((julianday(mid2.departure_time) - julianday(mid.arrival_time)) * 86400 AS INTEGER) AS total_duration
#                     FROM
#                         search_train t1
#                         INNER JOIN search_schedule src1 ON t1.id = src1.train_id
#                         INNER JOIN search_schedule mid ON t1.id = mid.train_id
#                         INNER JOIN search_train t2 ON t2.origin_date = t1.origin_date
#                         INNER JOIN search_schedule mid2 ON t2.id = mid2.train_id
#                         INNER JOIN search_schedule dest ON t2.id = dest.train_id
#                     WHERE
#                         src1.station_id = %s AND
#                         dest.station_id = %s AND
#                         date(src1.departure_time) = date(%s) AND
#                         src1.stop_order < mid.stop_order AND
#                         mid2.stop_order < dest.stop_order AND
#                         mid.station_id = mid2.station_id AND
#                         mid.station_id != %s AND
#                         mid.station_id != %s AND
#                         mid.arrival_time < mid2.departure_time
#                     ORDER BY mid.arrival_time
#                     LIMIT 20
#                     """
#                     # Parameters: source, dest, travel_date, travel_date, source, dest
#                     cursor.execute(connect_query, [source, dest, travel_date, source, dest])
#                     columns = [col[0] for col in cursor.description]
#                     raw_results = cursor.fetchall()
#                     for row in raw_results:
#                         row_dict = dict(zip(columns, row))
#                         row_dict['total_duration_hms'] = seconds_to_hms(row_dict['total_duration'])
#                         row_dict['mid_station_name'] = Station.objects.get(name=row_dict['mid_station_id']).name
#                         row_dict['train1_duration'] = seconds_to_hms(row_dict['train1_duration_seconds'])
#                         row_dict['train2_duration'] = seconds_to_hms(row_dict['train2_duration_seconds'])
#                         connecting_results.append(row_dict)


#     stations = Station.objects.all()
#     return render(request, 'search/search.html', {
#         'stations': stations,
#         'results': results,
#         'connecting_results': connecting_results,
#         'source': source,
#         'dest': dest,
#         'date': travel_date,
#         'allow_connect': allow_connect,
#     })
