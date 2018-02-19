from django.utils import timezone
from .models import *
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .forms import *
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerSerializer
from django.conf import settings

#Imports for weasyprint
#from django.http import HttpResponse
#from django.template.loader import render_to_string
#import weasyprint

#Import for currency calculator
import djmoney_rates
from moneyed import Money
from djmoney_rates.utils import convert_money
import decimal


#Import for graphics
from graphos.sources.simple import SimpleDataSource
from graphos.renderers.gchart import LineChart
from graphos.sources.model import ModelDataSource


def home(request):
   return render(request, 'portfolio/home.html',
                 {'portfolio': home})


@login_required
def customer_list(request):
   customer = Customer.objects.filter(created_date__lte=timezone.now())
   return render(request, 'portfolio/customer_list.html',
                 {'customers': customer})


@login_required
def customer_edit(request, pk):
   customer = get_object_or_404(Customer, pk=pk)
   if request.method == "POST":
       # update
       form = CustomerForm(request.POST, instance=customer)
       if form.is_valid():
           customer = form.save(commit=False)
           customer.updated_date = timezone.now()
           customer.save()
           customer = Customer.objects.filter(created_date__lte=timezone.now())
           return render(request, 'portfolio/customer_list.html',
                         {'customers': customer})
   else:
       # edit
       form = CustomerForm(instance=customer)
   return render(request, 'portfolio/customer_edit.html', {'form': form})


@login_required
def customer_delete(request, pk):
   customer = get_object_or_404(Customer, pk=pk)
   customer.delete()
   return redirect('portfolio:customer_list')


@login_required
def stock_list(request):
   stocks = Stock.objects.filter(purchase_date__lte=timezone.now())
   return render(request, 'portfolio/stock_list.html', {'stocks': stocks})


@login_required
def stock_new(request):
   if request.method == "POST":
       form = StockForm(request.POST)
       if form.is_valid():
           stock = form.save(commit=False)
           stock.created_date = timezone.now()
           stock.save()
           stocks = Stock.objects.filter(purchase_date__lte=timezone.now())
           return render(request, 'portfolio/stock_list.html',
                         {'stocks': stocks})
   else:
       form = StockForm()
       # print("Else")
   return render(request, 'portfolio/stock_new.html', {'form': form})


@login_required
def stock_edit(request, pk):
   stock = get_object_or_404(Stock, pk=pk)
   if request.method == "POST":
       form = StockForm(request.POST, instance=stock)
       if form.is_valid():
           stock = form.save()
           # stock.customer = stock.id
           stock.updated_date = timezone.now()
           stock.save()
           stocks = Stock.objects.filter(purchase_date__lte=timezone.now())
           return render(request, 'portfolio/stock_list.html', {'stocks': stocks})
   else:
       # print("else")
       form = StockForm(instance=stock)
   return render(request, 'portfolio/stock_edit.html', {'form': form})


@login_required
def stock_delete(request, pk):
   stock = get_object_or_404(Stock, pk=pk)
   stock.delete()
   stocks = Stock.objects.filter(purchase_date__lte=timezone.now())
   return render(request, 'portfolio/stock_list.html', {'stocks': stocks})


@login_required
def investment_list(request):
   investments = Investment.objects.filter(acquired_date__lte=timezone.now())
   return render(request, 'portfolio/investment_list.html', {'investments': investments})



@login_required
def portfolio(request,pk):
   customer = get_object_or_404(Customer, pk=pk)
   customers = Customer.objects.filter(created_date__lte=timezone.now())
   investments =Investment.objects.filter(customer=pk)
   stocks = Stock.objects.filter(customer=pk)
   sum_acquired_value = Investment.objects.filter(customer=pk).aggregate(Sum('acquired_value'))


   return render(request, 'portfolio/portfolio.html', {'customers': customers, 'investments': investments,
                                                      'stocks': stocks,
                                                      'sum_acquired_value': sum_acquired_value,})

@login_required
def investment_edit(request, pk):
   investment = get_object_or_404(Investment, pk=pk)
   if request.method == "POST":
       # update
       form = InvestmentForm(request.POST, instance=investment)
       if form.is_valid():
           investment = form.save(commit=False)
           investment.updated_date = timezone.now()
           investment.save()
           investment = Investment.objects.filter(recent_date__lte=timezone.now())
           return render(request, 'portfolio/investment_list.html',
                         {'investments': investment})
   else:
       # edit
       form = InvestmentForm(instance=investment)
   return render(request, 'portfolio/investment_edit.html', {'form': form})


@login_required
def investment_delete(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    investment.delete()
    return redirect('portfolio:investment_list')

@login_required
def investment_add (request):
   if request.method == "POST":
       form = InvestmentForm(request.POST)
       if form.is_valid():
           investment = form.save(commit=False)
           investment.created_date = timezone.now()
           investment.save()
           investment = Investment.objects.filter(acquired_date__lte=timezone.now())
           return render(request, 'portfolio/investment_list.html',
                         {'investments': investment})
   else:
       form = InvestmentForm()
       # print("Else")
   return render(request, 'portfolio/investment_add.html', {'form': form})


@login_required
def portfolio(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customers = Customer.objects.filter(created_date__lte=timezone.now())
    investments = Investment.objects.filter(customer=pk)
    stocks = Stock.objects.filter(customer=pk)
    sum_acquired_value = Investment.objects.filter(customer=pk).aggregate(sum=Sum('acquired_value'))['sum']
    sum_recent_value = Investment.objects.filter(customer=pk).aggregate(sum=Sum('recent_value'))['sum']

    # Initialize the value of the stocks
    sum_current_stocks_value = 0
    sum_of_initial_stock_value = 0

    # Loop through each stock and add the value to the total
    for stock in stocks:
        sum_current_stocks_value += stock.current_stock_value()
        sum_of_initial_stock_value += stock.initial_stock_value()


    #Converting all values to decimals
    sum_current_stocks_value = decimal.Decimal(sum_current_stocks_value)
    sum_of_initial_stock_value = decimal.Decimal(sum_of_initial_stock_value)
    sum_acquired_value = decimal.Decimal(sum_acquired_value)
    sum_recent_value = decimal.Decimal(sum_recent_value)

    # Adding variables for total sum of inital and current value
    sum_initial_total = decimal.Decimal(sum_of_initial_stock_value) + decimal.Decimal(sum_acquired_value)
    sum_current_total = decimal.Decimal(sum_current_stocks_value) + decimal.Decimal(sum_recent_value)

    #Adding code to convert value into euros
    sum_initial_total_euros = convert_money(sum_initial_total, "USD", "EUR")
    sum_current_total_euros = convert_money(sum_current_total, "USD", "EUR")

    sum_initial_total_rubels = convert_money(sum_initial_total, "USD", "RUB")
    sum_current_total_rubels = convert_money(sum_current_total, "USD", "RUB")


    #Building the objects for teh graph
    data = [
        ['Time', 'Investment', 'Stock', 'Total'],
        ['Initial', sum_acquired_value, sum_of_initial_stock_value, sum_initial_total],
        ['Current', sum_recent_value, sum_current_stocks_value, sum_current_total]
    ]
    # DataSource object
    data_source = SimpleDataSource(data=data)
    #queryset = Customer.objects.filter(pk=pk)
    #data_source_new = ModelDataSource(queryset, fields=['year', 'sales'])
    # Chart object
    chart = LineChart(data_source)
    context = {'chart': chart}

    return render(request, 'portfolio/portfolio.html', {'customers': customers, 'investments': investments,
                                                        'stocks': stocks,
                                                        'sum_acquired_value': sum_acquired_value,
                                                        'sum_recent_value': sum_recent_value,
                                                        'sum_current_stocks_value': sum_current_stocks_value,
                                                        'sum_of_initial_stock_value': sum_of_initial_stock_value,
                                                        'sum_initial_total': sum_initial_total,
                                                        'sum_current_total': sum_current_total,
                                                        'sum_initial_total_euros': sum_initial_total_euros,
                                                        'sum_current_total_euros': sum_current_total_euros,
                                                        'sum_initial_total_rubels': sum_initial_total_rubels,
                                                        'sum_current_total_rubels': sum_current_total_rubels,
                                                        'chart': chart})




# List at the end of the views.py
# Lists all customers
class CustomerList(APIView):

    def get(self,request):
        customers_json = Customer.objects.all()
        serializer = CustomerSerializer(customers_json, many=True)
        return Response(serializer.data)

'''
@login_required
def admin_order_pdf(request, customer_id):
    customer = get_object_or_404(Customer, pk=pk)
    customers = Customer.objects.filter(created_date__lte=timezone.now())
    investments = Investment.objects.filter(customer=pk)
    stocks = Stock.objects.filter(customer=pk)
    sum_acquired_value = Investment.objects.filter(customer=pk).aggregate(Sum('acquired_value'))
    sum_recent_value = Investment.objects.filter(customer=pk).aggregate(Sum('recent_value'))

    # Initialize the value of the stocks
    sum_current_stocks_value = 0
    sum_of_initial_stock_value = 0

    # Loop through each stock and add the value to the total
    for stock in stocks:
        sum_current_stocks_value += stock.current_stock_value()
        sum_of_initial_stock_value += stock.initial_stock_value()

    html = render_to_string('portfolio/pdf.html', {'customers': customers, 'investments': investments,
                                                        'stocks': stocks,
                                                        'sum_acquired_value': sum_acquired_value,
                                                        'sum_recent_value': sum_recent_value,
                                                        'sum_current_stocks_value': sum_current_stocks_value,
                                                        'sum_of_initial_stock_value': sum_of_initial_stock_value})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename=\"order_{}.pdf"'.format(order.id)
    weasyprint.HTML(string=html).write_pdf(response)
    return response
'''