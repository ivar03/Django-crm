from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .models import *
from .forms import OrderForm, CreateUserForm, CustomerForm
from .filters import OrderFilter
from .decorators import unauthenticated_user, allowed_users, admin_only

# Create your views here.
@unauthenticated_user
def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = CreateUserForm()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                user = form.save()
                username = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for' + username)
                return redirect('login')
        context={'form': form}
        return render(request, 'accounts/register.html', context)

@unauthenticated_user
def loginPage(request):
    if request.method == 'POST':
        username =request.POST.get('username')
        password =request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else: messages.info(request, 'Username or Passwordis incorrect')
    context={}
    return render(request, 'accounts/login.html', context)

def logoutUser(request):
    logout(request)
    return redirect('login')

@allowed_users(allowed_roles=['customer'])
@login_required(login_url='login')
def userPage(request):
    orders = request.user.customer.order_set.all()
    total_orders = orders.count()
    delivered = orders.filter(status = 'Delivered').count()
    pending = orders.filter(status = 'Pending').count()
    context={'orders': orders, 'total_orders': total_orders, 'delivered': delivered, 'pending': pending}
    return render(request,'accounts/user.html', context)

@allowed_users(allowed_roles=['customer'])
@login_required(login_url='login')
def accountSettings(request):
    customer = request.user.customer
    form = CustomerForm(instance=customer) 
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
    context={'form': form}
    return render(request, 'accounts/user_settings.html', context)

@admin_only
@login_required(login_url='login')
def home(request):
    orders = Order.objects.all()
    customers = Customer.objects.all()
    total_customers = customers.count()
    total_orders = orders.count()
    delivered = orders.filter(status = 'Delivered').count()
    pending = orders.filter(status = 'Pending').count()

    context = {'orders': orders, 'customers': customers, 'total_orders': total_orders, 'delivered': delivered, 'pending': pending}

    return render(request, 'accounts/dashboard.html', context)

@allowed_users(allowed_roles=['admin'])
@login_required(login_url='login')
def products(request):
    products = Product.objects.all()
    return render(request, 'accounts/products.html', {'products': products})

@allowed_users(allowed_roles=['admin'])
@login_required(login_url='login')
def customer(request, pk):
    customer = Customer.objects.get(id=pk)
    orders = customer.order_set.all()
    myFilter = OrderFilter(request.GET, queryset=orders)
    orders = myFilter.qs
    context =  {'customer':customer, 'orders': orders, 'myFilter': myFilter}
    return render(request, 'accounts/customer.html', context)

@allowed_users(allowed_roles=['admin'])
@login_required(login_url='login')
def createOrder(request,pk):
    OrderFormSet = inlineformset_factory(Customer, Order, fields=('product','status'), extra=5)
    customer = Customer.objects.get(id=pk)
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
    #form = OrderForm(initial={'customer':customer})
    if request.method == 'POST':
        formset = OrderFormSet(request.POST, instance=customer)
        #form = OrderForm(request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('/')
        
    context={'formset': formset, 'customer': customer}
    return render(request, 'accounts/order_form.html', context)

@allowed_users(allowed_roles=['admin'])
@login_required(login_url='login')
def updateOrder(request,pk):
    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('/')
        
    context={'form': form}
    return render(request, 'accounts/order_form.html', context)

@allowed_users(allowed_roles=['admin'])
@login_required(login_url='login')
def deleteOrder(request,pk):
    order = Order.objects.get(id=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('/')
    context = {'item':order}
    return render(request, 'accounts/delete.html', context)