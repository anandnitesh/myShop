from django.shortcuts import render
from .models import Product, Contact, Orders, OrderUpdate
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from PayTm import Checksum
# Create your views here.
from django.http import HttpResponse
MERCHANT_KEY = 'Your-Merchant-Key-Here'

def index(request):
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds':allProds}
    return render(request, 'shop/index.html', params)

def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False

def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]

        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds': allProds, "msg": ""}
    if len(allProds) == 0 or len(query)<4:
        params = {'msg': "Please make sure to enter relevant search query"}
    return render(request, 'shop/search.html', params)


def about(request):
    return render(request, 'shop/about.html')


def contact(request):
    thank = False
    if request.method=="POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        thank = True
    return render(request, 'shop/contact.html', {'thank': thank})


def tracker(request):
    if request.method=="POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps([updates, order[0].items_json], default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{}')
        except Exception as e:
            return HttpResponse('{}')

    return render(request, 'shop/tracker.html')


def productView(request, myid):

    # Fetch the product using the id
    product = Product.objects.filter(id=myid)
    return render(request, 'shop/prodView.html', {'product':product[0]})


def checkout(request):
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json, name=name, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone, amount=amount)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank = True
        id = order.order_id
        # return render(request, 'shop/checkout.html', {'thank':thank, 'id': id})
        # Request paytm to transfer the amount to your account after payment by user
        param_dict = {

                'MID': 'Your-Merchant-Id-Here',
                'ORDER_ID': str(order.order_id),
                'TXN_AMOUNT': str(amount),
                'CUST_ID': email,
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'WEBSTAGING',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',

        }
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
        return render(request, 'shop/paytm.html', {'param_dict': param_dict})

    return render(request, 'shop/checkout.html')


@csrf_exempt
def handlerequest(request):
    # paytm will send you post request here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]

    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print('order successful')
        else:
            print('order was not successful because' + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})
Code shop/templates/shop/index.html as described/written in the video
{% extends 'shop/basic.html' %}
{% block title%} MyAwesomeCart - Best Ecommerce Website{% endblock %}
{% block css %}
.col-md-3
{
display: inline-block;
margin-left:-4px;
}
.carousel-indicators .active {
background-color: blue;
}
.col-md-3 img{
width: 170px;
height: 200px;
}
body .carousel-indicator li{
background-color: blue;
}
body .carousel-indicators{
bottom: -40px;
}
.carousel-indicators li {


    background-color: #7270fc;
}
body .carousel-control-prev-icon,
body .carousel-control-next-icon{
background-color: blue;
}
.carousel-control-prev,
.carousel-control-next{
top: auto;
bottom: auto;
padding-top: 222px;
}
body .no-padding{
padding-left: 0,
padding-right: 0;
}
{% endblock %}
{% block body %}
{% load static %}
<div class="container">
    <!--Slideshow starts here -->
    {% for product, range, nSlides in allProds %}
    <h5 class="my-4">Flash Sale On {{product.0.category}} - Recommended Items</h5>
    <div class="row">
        <div id="demo{{forloop.counter}}" class="col carousel slide my-3" data-ride="carousel">
            <ul class="carousel-indicators">
                <li data-target="#demo{{forloop.counter}}" data-slide-to="0" class="active"></li>
                {% for i in range %}
                <li data-target="#demo{{forloop.parentloop.counter}}" data-slide-to="{{i}}"></li>
                {% endfor %}
            </ul>
            <div class="container carousel-inner no-padding">
                <div class="carousel-item active">
                    {% for i in product %}
                    <div class="col-xs-3 col-sm-3 col-md-3">
                        <div class="card align-items-center" style="width: 18rem;">
                            <img src='/media/{{i.image}}' class="card-img-top" alt="...">
                            <div class="card-body">
                                <h5 class="card-title" id="namepr{{i.id}}">{{i.product_name}}</h5>
                                <p class="card-text">{{i.desc|slice:"0:53"}}...</p>
                                <h6 class="card-title" >Price: <span id="pricepr{{i.id}}">{{i.price}}</span></h6>
                                <span id="divpr{{i.id}}" class="divpr">
                                    <button id="pr{{i.id}}" class="btn btn-primary cart">Add To Cart</button>
                                </span>
                                <a href="/shop/products/{{i.id}}"><button id="qv{{i.id}}" class="btn btn-primary cart">QuickView</button></a>
                            </div>
                        </div>
                    </div>
                    {% if forloop.counter|divisibleby:4 and forloop.counter > 0 and not forloop.last %}
                </div>
                <div class="carousel-item">
                    {% endif %}
                    {% endfor %}
                </div>
            </div>
        </div>
        <!-- left and right controls for the slide -->
        <a class="carousel-control-prev" href="#demo{{forloop.counter}}" data-slide="prev">
            <span class="carousel-control-prev-icon"></span>
        </a>
        <a class="carousel-control-next" href="#demo{{forloop.counter}}" data-slide="next">
            <span class="carousel-control-next-icon"></span>
        </a>
    </div>
    {% endfor %}
</div>
{% endblock %}
{% block js %}
<script>
// Find out the cart items from localStorage
if (localStorage.getItem('cart') == null) {
    var cart = {};
} else {
    cart = JSON.parse(localStorage.getItem('cart'));
    updateCart(cart);
}
// If the add to cart button is clicked, add/increment the item
//$('.cart').click(function() {
    $('.divpr').on('click', 'button.cart', function(){
    var idstr = this.id.toString();
    if (cart[idstr] != undefined) {
        qty = cart[idstr][0] + 1;
    } else {
        qty = 1;
        name = document.getElementById('name'+idstr).innerHTML;
        price = document.getElementById('price'+idstr).innerHTML;
        cart[idstr] = [qty, name, parseInt(price)];
    }
    updateCart(cart);
});
//Add Popover to cart
$('#popcart').popover();
updatePopover(cart);
function updatePopover(cart) {
    console.log('We are inside updatePopover');
    var popStr = "";
    popStr = popStr + "<h5> Cart for your items in my shopping cart </h5><div class='mx-2 my-2'>";
    var i = 1;
    for (var item in cart) {
        popStr = popStr + "<b>" + i + "</b>. ";
        popStr = popStr + document.getElementById('name' + item).innerHTML.slice(0, 19) + "... Qty: " + cart[item][0] + '<br>';
        i = i + 1;
    }
    popStr = popStr + "</div> <a href='/shop/checkout'><button class='btn btn-primary' id ='checkout'>Checkout</button></a> <button class='btn btn-primary' onclick='clearCart()' id ='clearCart'>Clear Cart</button>     "
    console.log(popStr);
    document.getElementById('popcart').setAttribute('data-content', popStr);
    $('#popcart').popover('show');
}
function clearCart() {
    cart = JSON.parse(localStorage.getItem('cart'));
    for (var item in cart) {
        document.getElementById('div' + item).innerHTML = '<button id="' + item + '" class="btn btn-primary cart">Add To Cart</button>'
    }
    localStorage.clear();
    cart = {};
    updateCart(cart);
}
function updateCart(cart) {
    var sum = 0;
    for (var item in cart) {
        sum = sum + cart[item][0];
        document.getElementById('div' + item).innerHTML = "<button id='minus" + item + "' class='btn btn-primary minus'>-</button> <span id='val" + item + "''>" + cart[item][0] + "</span> <button id='plus" + item + "' class='btn btn-primary plus'> + </button>";
    }
    localStorage.setItem('cart', JSON.stringify(cart));
    document.getElementById('cart').innerHTML = sum;
    console.log(cart);
    updatePopover(cart);
}
// If plus or minus button is clicked, change the cart as well as the display value
$('.divpr').on("click", "button.minus", function() {
    a = this.id.slice(7, );
    cart['pr' + a][0] = cart['pr' + a][0] - 1;
    cart['pr' + a][0] = Math.max(0, cart['pr' + a][0]);
    if (cart['pr' + a][0] == 0){
        document.getElementById('divpr' + a).innerHTML = '<button id="pr'+a+'" class="btn btn-primary cart">Add to Cart</button>';
        delete cart['pr'+a];
    }
    else{
        document.getElementById('valpr' + a).innerHTML = cart['pr' + a][0];
    }
    updateCart(cart);
});
$('.divpr').on("click", "button.plus", function() {
    a = this.id.slice(6, );
    cart['pr' + a][0] = cart['pr' + a][0] + 1;
    document.getElementById('valpr' + a).innerHTML = cart['pr' + a][0];
    updateCart(cart);
});
</script>
{% endblock %}
Code shop/templates/shop/basic.html as described/written in the video
<!doctype html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous">

    <title>{% block title%} {% endblock %}</title>
     <style>
       {% block css %} {% endblock %}
  </style>
  </head>
  <body>

    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <a class="navbar-brand" href="/shop">My Awesome Cart</a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>

  <div class="collapse navbar-collapse" id="navbarSupportedContent">
    <ul class="navbar-nav mr-auto">
      <li class="nav-item active">
        <a class="nav-link" href="/shop">Home <span class="sr-only">(current)</span></a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="/shop/about">About Us</a>
      </li>

      <li class="nav-item">
        <a class="nav-link" href="/shop/tracker">Tracker</a>
      </li>

      <li class="nav-item">
        <a class="nav-link" href="/blog">Blog</a>
      </li>

       <li class="nav-item">
        <a class="nav-link" href="/shop/contact">Contact Us</a>
      </li>


    </ul>
    <form method='get' action='/shop/search/' class="form-inline my-2 my-lg-0">
      <input class="form-control mr-sm-2" type="search" placeholder="Search" aria-label="Search" name="search" id="search">
      <button class="btn btn-outline-success my-2 my-sm-0" type="submit">Search</button>
    </form>
    <button type="button" class="btn btn-secondary mx-2" id="popcart" data-container="body" data-toggle="popover" data-placement="bottom" data-html="true" data-content="Vivamus
sagittis lacus vel augue laoreet rutrum faucibus.">


  Cart(<span id="cart">0</span>)
</button>
  </div>
</nav>
  {% block body %} {% endblock %}

    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.3.1.js"
  integrity="sha256-2Kok7MbOyxpgUVvAk/HJ2jigOSYS2auK4Pfzbm7uH60="
  crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.6/umd/popper.min.js" integrity="sha384-wHAiFfRlMFy6i5SRaxvfOCifBUQy1xHdJ/yoi7FRNXMRBu5WHdZYu1hA6ZOblgut" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/js/bootstrap.min.js" integrity="sha384-B0UglyR+jN6CkvvICOB2joaf5I4l3gm9GU6Hc1og6Ls7i6U/mkkaduKaBhlAXv9k" crossorigin="anonymous"></script>
    {% block js %} {% endblock %}
  </body>
</html>
Code shop/templates/shop/search.html as described/written in the video
{% extends 'shop/basic.html' %}

{% block title%} Search Results - My Awesome Cart{% endblock %}


{% block css %}
.col-md-3
{
display: inline-block;
margin-left:-4px;
}
.carousel-indicators .active {
background-color: blue;
}
.col-md-3 img{
width: 170px;
height: 200px;
}
body .carousel-indicator li{
background-color: blue;
}
body .carousel-indicators{
bottom: -40px;
}
.carousel-indicators li {

