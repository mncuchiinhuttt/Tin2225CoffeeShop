from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from .models import MenuItem
from django.contrib.humanize.templatetags.humanize import intcomma

def home(request):
    return render(request, 'users/home.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def menu_list(request):
    menu_items = MenuItem.objects.all()
    return render(request, 'users/menu_list.html', {'menu_items': menu_items})

def menu_detail(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    formatted_price = intcomma(item.price).replace(",", ".")
    return render(request, 'users/menu_detail.html', {'item': item, 'formatted_price': formatted_price})