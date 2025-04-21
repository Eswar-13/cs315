# booking/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from search.models import Train, Station
from .models import Booking, Passenger, Seating
from django.conf import settings
from django.contrib import messages

@login_required
def booking_start(request):
    # Get train and route info from query params
    train_no = request.GET.get('train_no')
    source_name = request.GET.get('source')
    dest_name = request.GET.get('dest')
    date = request.GET.get('date')
    seats_available = int(request.GET.get('seats_available', 0))

    if request.method == "POST":
        no_of_passengers = int(request.POST.get('no_of_passengers'))
        # Redirect to passenger details form, pass all info via GET
        url = (reverse('booking:passengers') +
               f"?train_no={train_no}&source={source_name}&dest={dest_name}&date={date}&no_of_passengers={no_of_passengers}")
        return redirect(url)

    # Render form to select number of passengers
    context = {
        'train_no': train_no,
        'source': source_name,
        'dest': dest_name,
        'date': date,
        'seats_available': seats_available,
        'max_passengers': min(seats_available, 6),
    }
    return render(request, 'booking/booking_start.html', context)

@login_required
def booking_passengers(request):
    # Get info from GET params
    train_no = request.GET.get('train_no')
    source_name = request.GET.get('source')
    dest_name = request.GET.get('dest')
    date = request.GET.get('date')
    no_of_passengers = int(request.GET.get('no_of_passengers', 1))

    if request.method == "POST":
        # Save booking and passengers
        train = get_object_or_404(Train, number=train_no, origin_date=date)
        source = get_object_or_404(Station, name=source_name)
        dest = get_object_or_404(Station, name=dest_name)
        booking = Booking.objects.create(
            train=train,
            user=request.user,
            source=source,
            destination=dest,
            no_of_passengers=no_of_passengers
        )
        # Create Passenger and Seating records
        for i in range(1, no_of_passengers + 1):
            name = request.POST.get(f'name_{i}')
            age = int(request.POST.get(f'age_{i}'))
            gender = request.POST.get(f'gender_{i}')
            passenger = Passenger.objects.create(
                user=request.user,
                name=name,
                age=age,
                gender=gender
            )
            seat_no = request.POST.get(f'seat_no_{i}', str(i))
            Seating.objects.create(
                booking=booking,
                passenger=passenger,
                seat_no=seat_no
            )
        messages.success(request, "Booking successful!")
        return redirect('booking:confirm')

    # Render form for passenger details
    context = {
        'no_of_passengers': no_of_passengers,
        'train_no': train_no,
        'source': source_name,
        'dest': dest_name,
        'date': date,
        'passenger_range': range(1, no_of_passengers + 1), 
    }
    return render(request, 'booking/booking_passengers.html', context)

@login_required
def booking_confirm(request):
    # Show a simple confirmation page
    return render(request, 'booking/booking_confirm.html')

@login_required
def booking_history(request):
    bookings = Booking.objects.filter(user=request.user).select_related(
        'train', 'source', 'destination'
    ).order_by('-train__origin_date')
    return render(request, 'booking/history.html', {'bookings': bookings})
