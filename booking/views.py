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
    train_no = request.GET.get('train_no')
    source_name = request.GET.get('source')
    dest_name = request.GET.get('dest')
    date = request.GET.get('date')

    train = get_object_or_404(Train, number=train_no, origin_date=date)
    seats_available = train.seats_available

    if request.method == "POST":
        no_of_passengers = int(request.POST.get('no_of_passengers'))
        if no_of_passengers > seats_available or no_of_passengers < 1:
            messages.error(request, "Invalid number of passengers")
            return redirect('booking:start')

        source = get_object_or_404(Station, name=source_name)
        dest = get_object_or_404(Station, name=dest_name)

        # Create Booking immediately (no passenger details yet)
        booking = Booking.objects.create(
            train=train,
            user=request.user,
            source=source,
            destination=dest,
            no_of_passengers=no_of_passengers
        )
        # Redirect to passenger details with booking_id (UUID)
        url = reverse('booking:passengers') + f"?booking_id={booking.booking_id}"
        return redirect(url)

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
    booking_id = request.GET.get('booking_id')
    booking = get_object_or_404(Booking, booking_id=booking_id)

    if request.method == "POST":
        train = booking.train
        no_of_passengers = booking.no_of_passengers

        # Check seat availability again
        if train.seats_available < no_of_passengers:
            messages.error(request, "Not enough seats available")
            return redirect('booking:start')

        starting_seat = train.seats_available - no_of_passengers + 1

        # Update train seats
        train.seats_available -= no_of_passengers
        train.save()

        # Create passengers and seating
        for i in range(no_of_passengers):
            name = request.POST.get(f'name_{i+1}')
            age = int(request.POST.get(f'age_{i+1}'))
            gender = request.POST.get(f'gender_{i+1}')

            passenger = Passenger.objects.create(
                user=request.user,
                name=name,
                age=age,
                gender=gender
            )

            Seating.objects.create(
                booking=booking,
                passenger=passenger,
                seat_no=starting_seat + i
            )

        messages.success(request, "Booking successful!")
        return redirect('booking:confirm')

    context = {
        'no_of_passengers': booking.no_of_passengers,
        'train_no': booking.train.number,
        'source': booking.source.name,
        'dest': booking.destination.name,
        'date': booking.train.origin_date,
        'passenger_range': range(1, booking.no_of_passengers + 1),
        'booking_id': booking.booking_id,
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