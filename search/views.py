# views.py
from django.shortcuts import render
from django.db import connection
from .models import Station

def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def route_search(request):
    results = []
    
    if request.method == 'GET':
        
        source = request.GET.get('source')
        dest = request.GET.get('dest')
        travel_date = request.GET.get('date')
        
        if source and dest and travel_date:
            with connection.cursor() as cursor:
                query = """
                SELECT 
                    t.number AS train_number,
                    t.origin_date,
                    src.departure_time,
                    dest.arrival_time,
                    t.seats_available,
                    (dest.distance_from_src - src.distance_from_src) AS distance,
                    CAST(
                        (julianday(dest.arrival_time) - julianday(src.departure_time)) * 86400 
                        AS INTEGER
                    ) AS duration_seconds
                FROM 
                    search_train t
                    INNER JOIN search_schedule src ON t.id = src.train_id
                    INNER JOIN search_schedule dest ON t.id = dest.train_id
                WHERE
                    src.station_id = %s AND
                    dest.station_id = %s AND
                    t.origin_date = %s AND
                    src.stop_order < dest.stop_order
                ORDER BY src.departure_time
                """
                cursor.execute(query, [source, dest, travel_date])
                columns = [col[0] for col in cursor.description]
                raw_results = cursor.fetchall()
                
                # Convert seconds to HH:MM:SS
                results = []
                for row in raw_results:
                    row_dict = dict(zip(columns, row))
                    row_dict['duration'] = seconds_to_hms(row_dict['duration_seconds'])
                    results.append(row_dict)

    stations = Station.objects.all()
    return render(request, 'search/search.html', {
        'stations': stations,
        'results': results,
        'source': source,
        'dest': dest,
        'date': travel_date
    })
