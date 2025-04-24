# services/route_service.py
from django.apps import apps
from collections import deque, defaultdict
from datetime import datetime, timedelta

class RouteService:
    _instance = None
    graph = None
    initialized = False

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self):
        """Explicit initialization method to load graph"""
        if not self.initialized:
            self.graph = defaultdict(list)
            self._load_graph()
            self.initialized = True

    def _load_graph(self):
        """Build complete graph structure from Schedule model"""
        Schedule = apps.get_model('search', 'Schedule')
        schedules = Schedule.objects.select_related('train', 'station').order_by('train', 'stop_order')

        current_train = None
        prev_stop = None

        for schedule in schedules:
            # Skip invalid entries
            if not schedule.station :
                continue

            if schedule.train != current_train:
                current_train = schedule.train
                prev_stop = None

            if prev_stop:
                # Create edge with full connection details
                edge = {
                    'from_station': prev_stop.station.name,
                    'to_station': schedule.station.name,
                    'train': current_train,
                    'departure': prev_stop.departure_time,
                    'arrival': schedule.arrival_time,
                    'distance': float(schedule.distance_from_src - prev_stop.distance_from_src),
                    'seats_available': current_train.seats_available
                }
                # print(f"Adding edge: {edge}")  # Debug statement
                self.graph[edge['from_station']].append(edge)

            prev_stop = schedule

    def find_routes(self, source, dest, date_str, connected_allowed):
        """Main route finding interface with connection support"""
        if not self.initialized:
            self.initialize()

        try:
            travel_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'results': [], 'connecting_results': [], 'allow_connect': False}

        # Get direct routes
        direct_data = self._find_direct_routes(source, dest, travel_date)
        results = direct_data['results']
        connecting_results = []

        # Get connecting routes if requested
        if connected_allowed:
            connecting_results = self._find_routes_with_connections(source, dest, travel_date)

        return {
            'results': results,
            'connecting_results': connecting_results,
            'allow_connect': connected_allowed
        }

    def _find_direct_routes(self, source, dest, travel_date):
        """BFS for direct routes (single train)"""
        queue = deque()
        results = []

        # Initialize with valid starting edges
        for edge in self.graph.get(source, []):
            if edge['departure'].date() == travel_date:
                queue.append((edge['to_station'], [edge], edge['train']))

        # Track visited stations per train to prevent loops
        visited = defaultdict(set)

        while queue:
            current_station, path, current_train = queue.popleft()

            if current_station == dest:
                results.append(path)
                continue

            for edge in self.graph.get(current_station, []):
                # Maintain train continuity
                if edge['train'] != current_train:
                    continue
                
                # Prevent revisiting stations with same train
                if edge['to_station'] in visited[current_train]:
                    continue

                visited[current_train].add(edge['to_station'])
                queue.append((edge['to_station'], path + [edge], current_train))

        return {
            'results': [self._format_direct_path(p) for p in results],
            'connecting_results': [],
            'allow_connect': False
        }

    def _format_direct_path(self, path):
        """Format path to match SQL output structure"""
        first = path[0]
        last = path[-1]
        duration = (last['arrival'] - first['departure']).total_seconds()
        
        return {
            'train_number': first['train'].number,
            'origin_date': first['train'].origin_date,
            'departure_time': first['departure'].time(),
            'arrival_time': last['arrival'].time(),
            'seats_available': first['seats_available'],
            'distance': sum(e['distance'] for e in path),
            'duration_seconds': int(duration),
            'duration': self._seconds_to_hms(duration)
        }

    @staticmethod
    def _seconds_to_hms(seconds):
        """Convert seconds to HH:MM:SS format"""
        return f"{int(seconds//3600):02}:{int((seconds%3600)//60):02}:{int(seconds%60):02}"
    
    def _find_routes_with_connections(self, source, dest, travel_date):
        """Bidirectional BFS implementation for 1-transfer routes"""

        # Build reverse graph for backward search
        reverse_graph = defaultdict(list)
        for from_station, edges in self.graph.items():
            for edge in edges:
                reverse_graph[edge['to_station']].append({
                    'from_station': edge['to_station'],
                    'to_station': from_station,
                    'train': edge['train'],
                    'departure': edge['arrival'],  # Reverse time perspective
                    'arrival': edge['departure'],
                    'distance': edge['distance'],
                    'seats_available': edge['seats_available']
                })

        # Forward BFS from source
        forward = defaultdict(lambda: {'arrival': None, 'path': None})
        queue = deque()
        for edge in self.graph.get(source, []):
            if edge['departure'].date() == travel_date:
                forward[edge['to_station']] = {
                    'arrival': edge['arrival'],
                    'path': [edge]
                }
                queue.append((edge['to_station'], edge['arrival'], [edge]))

        while queue:
            current_station, arrival_time, path = queue.popleft()
            for edge in self.graph.get(current_station, []):
                if edge['departure'] < arrival_time + timedelta(minutes=30):
                    continue
                if edge['departure'].date() != travel_date:
                    continue
                if edge['to_station'] not in forward or edge['arrival'] < forward[edge['to_station']]['arrival']:
                    new_path = path + [edge]
                    forward[edge['to_station']] = {
                        'arrival': edge['arrival'],
                        'path': new_path
                    }
                    queue.append((edge['to_station'], edge['arrival'], new_path))

        # Backward BFS from dest
        backward = defaultdict(lambda: {'departure': None, 'path': None})
        queue = deque()
        for edge in reverse_graph.get(dest, []):
                backward[edge['to_station']] = {
                    'departure': edge['arrival'],  # Original departure time
                    'path': [edge]
                }
                queue.append((edge['to_station'], edge['arrival'], [edge]))

        while queue:
            current_station, departure_time, path = queue.popleft()
            for edge in reverse_graph.get(current_station, []):
                if edge['departure'] > departure_time - timedelta(minutes=30):
                    continue
                if edge['departure'].date() != travel_date:
                    continue
                if edge['to_station'] not in backward or edge['arrival'] > backward[edge['to_station']]['departure']:
                    new_path = path + [edge]
                    backward[edge['to_station']] = {
                        'departure': edge['arrival'],
                        'path': new_path
                    }
                    queue.append((edge['to_station'], edge['arrival'], new_path))

        # Find valid mid stations
        # print(forward,backward)
        connecting_results = []
        print(forward.keys())
        print(backward.keys())
        for mid in set(forward.keys()) & set(backward.keys()):
            # print(mid)
            fwd = forward[mid]
            bwd = backward[mid]
            
            if fwd['arrival']  > bwd['departure']:
                continue
            
            # print("route")
            # Reconstruct paths
            first_leg = fwd['path']
            second_leg = [{
                'from_station': edge['to_station'],
                'to_station': edge['from_station'],
                'train': edge['train'],
                'departure': edge['arrival'],
                'arrival': edge['departure'],
                'distance': edge['distance'],
                'seats_available': edge['seats_available']
            } for edge in reversed(bwd['path'])]

            # Format to match SQL output
            connection = self._format_connection(first_leg, second_leg, mid)
            print(connection)
            print(' ')
            connecting_results.append(connection)

        return connecting_results

    def _format_connection(self, first_leg, second_leg, mid_station):
        """Format connecting route to match SQL structure"""
        train1 = first_leg[-1]['train']
        train2 = second_leg[0]['train']
        
        # Calculate durations
        train1_duration = (first_leg[-1]['arrival'] - first_leg[0]['departure']).total_seconds()
        train2_duration = (second_leg[-1]['arrival'] - second_leg[0]['departure']).total_seconds()
        transfer_duration = (second_leg[0]['departure'] - first_leg[-1]['arrival']).total_seconds()
        
        return {
            'train1_number': train1.number,
            'train1_date': first_leg[0]['departure'].date(),
            'train1_departure': first_leg[0]['departure'].time(),
            'train1_arrival': first_leg[-1]['arrival'].time(),
            'train1_seats': train1.seats_available,
            'train2_number': train2.number,
            'train2_date': second_leg[0]['departure'].date(),
            'train2_departure': second_leg[0]['departure'].time(),
            'train2_arrival': second_leg[-1]['arrival'].time(),
            'train2_seats': train2.seats_available,
            'mid_station_id': mid_station,
            'train1_distance': sum(e['distance'] for e in first_leg),
            'train2_distance': sum(e['distance'] for e in second_leg),
            'train1_duration_seconds': int(train1_duration),
            'train2_duration_seconds': int(train2_duration),
            'total_duration': int(train1_duration + train2_duration + transfer_duration),
            'total_duration_hms': self._seconds_to_hms(train1_duration + train2_duration + transfer_duration),
            'train1_duration': self._seconds_to_hms(train1_duration),
            'train2_duration': self._seconds_to_hms(train2_duration),
            'mid_station_name': mid_station
        }
