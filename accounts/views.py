from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from accounts.forms import RegistrationForm, LoginForm, ShopifyForm
from accounts.models import PersonAccount, Live, ShopifyAccess, OTP
from django.contrib.auth.models import User

from django.http import QueryDict
from django.contrib import messages

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from django.http import StreamingHttpResponse
import threading
import requests
import json

from django.conf import settings


from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np
import cv2
from collections import Counter
import os
import pandas as pd
from PIL import ImageColor


def shopify(t,k,s,a,data):
    shopify_url = t
    api_key = k
    api_secret = s
    access_token = a

    # Make an API request to retrieve all products
    url = f"https://{shopify_url}/admin/api/2023-04/{data}.json"
    headers = {
        "X-Shopify-Access-Token": access_token
    }
    response = requests.get(url, headers=headers)

    return response

def getProducts(response):
    # Print the response
    if response.status_code == 200:
        products = response.json()["products"]
        for product in products:    
            for key in product:
                pass
                # print(f"key: {key} - {product[key]}")
                # print(product)
    else:
        print(f"Error: {response.status_code}")
    return products

def getOrders(response):
    # Print the response
    if response.status_code == 200:
        orders = response.json()["orders"]
        for order in orders:    
            for key in order:
                pass
                # print(f"key: {key} - {product[key]}")
                # print(product)
    else:
        print(f"Error: {response.status_code}")
    return orders

def createOrderAndUpdateInventory(request,id):
    live_data = Live.objects.get(id=id)
    shopify_access = ShopifyAccess.objects.get(user_id=live_data.createdBy.id)

    headers = {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': shopify_access.access_token
    }

    post_data = request.POST
    modified_post_data = post_data.copy()
    modified_post_data.pop('csrfmiddlewaretoken')

    line_items = []
    for i in range(len(modified_post_data.getlist('product'))):
        quantity = modified_post_data.getlist('quantity')[i]
        variant_id = modified_post_data.getlist('product')[i]
        if quantity and int(quantity) > 0:
            line_items.append({
                'variant_id': variant_id,
                'quantity': int(quantity)
            })

            # Update inventory
            inventory = {
                "variant": {
                    "id": variant_id,
                    "inventory_quantity_adjustment": -int(quantity)  # Adjust inventory based on order quantity
                }
            }
            response = requests.post(f"https://{shopify_access.shopify_url}/admin/api/2023-04/products/{variant_id}/variants/{variant_id}.json", headers=headers, data=json.dumps(inventory))

            if response.status_code == 200:
                print(f"Inventory updated for product ID {variant_id}")
            else:
                print(f"Failed to update inventory for product ID {variant_id}")

    # Create an order
    order = {
        'order': {
            'line_items': line_items,
            'customer': {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.username
            },
            'financial_status': 'pending'
        }
    }

    # Send the POST request to create the order
    response = requests.post(f'https://{shopify_access.shopify_url}/admin/api/2023-04/orders.json', headers=headers, data=json.dumps(order))

    # Check if the request was successful
    if response.status_code == 201:
        print('Order created successfully.')
    else:
        print('Error creating order: ', response.text)

    return redirect(f'/pamine/livepage/{id}')

def getAllCustomerDetails():
    url = f"https://ae32d3.myshopify.com/admin/api/2023-04/orders.json"
    headers = {
        "X-Shopify-Access-Token": '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'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        customer_data = response.json().get('customer', {})
        print(customer_data)
        return customer_data
    else:
        print(f"Failed to fetch customer details: {response.text}")
        return None

def getCustomerDetails(shopify_url, access_token, customer_id):
    url = f"https://{shopify_url}/admin/api/2023-04/customers/{customer_id}.json"
    headers = {
        "X-Shopify-Access-Token": access_token
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        customer_data = response.json().get('customer', {})
        return customer_data
    else:
        print(f"Failed to fetch customer details for customer ID {customer_id}: {response.text}")
        return None
    
def getAllOrderswithCustomers(shopify_url, access_token):
    url = f"https://{shopify_url}/admin/api/2023-04/orders.json?status=any&fields=id,email,line_items,customer,order_number,total_price,financial_status"
    headers = {
        "X-Shopify-Access-Token": access_token
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        orders = response.json().get('orders', [])
        for order in orders:
            customer_id = order.get('customer', {}).get('id')
            if customer_id:
                customer_data = getCustomerDetails(shopify_url, access_token, customer_id)
                order['customer_details'] = customer_data
        return orders
    else:
        print(f"Failed to fetch orders for {shopify_url}: {response.text}")
        return None
    
def getAllOrders(shopify_url, access_token):
    url = f"https://{shopify_url}/admin/api/2023-04/orders.json?status=any&fields=id,email,line_items,customer,order_number,total_price,financial_status"
    headers = {
        "X-Shopify-Access-Token": access_token
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        orders = response.json()['orders']
        return orders
    else:
        print(f"Failed to fetch orders for {shopify_url}: {response.text}")
        return None

def getAllOrdersByEmail(email):
    url = f"https://ae32d3.myshopify.com/admin/api/2023-04/orders.json?email={email}"
    headers = {
        "X-Shopify-Access-Token": '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'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        orders = response.json()['orders']
        return orders
    else:
        print(f"Failed to fetch orders for ae32d3.myshopify.com: {response.text}")
        return None

def getAllOrdersFromAllStores():
    unique_orders = {}
    shopify_access = ShopifyAccess.objects.all().distinct()
    print(shopify_access)
    for store in shopify_access:
        orders = getAllOrders(store.shopify_url, store.access_token)
        if orders:
            print(f"Orders for store {store.shopify_url}:")
            for order in orders:
                order_id = order['id']
                if order_id not in unique_orders:
                    unique_orders[order_id] = order
                    # print(order)
        else:
            print(f"No orders found for store {store.shopify_url}")
    return unique_orders
@login_required(login_url='/login/')
def endLive(request, id, live):
    order = Live.objects.get(id=id)
    if live == 'END':
        request.session.set_expiry(600)
        Live.objects.filter(pk=id).update(live=0)
        print(f'Live {id} is now {live}')
    return redirect('setuplive')

#LOGGED IN USER PAGES START

@login_required(login_url='/login/')
def home(request):
    user_details = PersonAccount.objects.get(pk=request.user.id)
    if(user_details.account_type == 'Seller'):
        live_data = Live.objects.filter(live=True,createdBy=user_details.user_id)
    else:
        live_data = Live.objects.filter(live=True)
    context = {'test':'test','user':user_details,'live':live_data}
    return render(request, 'accounts/home.html', context)

@login_required(login_url='/login/')
def livesetup(request):
    if request.method == 'POST':
        new_live = Live(
            title=request.POST['title'],
            description=request.POST['description'],
            createdBy=request.user.personaccount,  # assuming the logged in user has a related PersonAccount object
            live=True
        )
        # save the new instance to the database
        new_live.save()
        return redirect(f'/pamine/livepage/{new_live.id}')
    user_details = PersonAccount.objects.get(pk=request.user.id)
    context = {'test':'test', 'user':user_details}
    return render(request, 'accounts/livepage.html', context)

@login_required(login_url='/login/')
def livepage(request,id):
    liveData = Live.objects.get(id=id)
    try:
        shopifyAccess = ShopifyAccess.objects.get(user_id=liveData.createdBy.id)
        print(request.user.first_name)
        print(request.user.last_name)
        if(liveData.live == 0):
            return redirect(f'/pamine/')
        
        t = shopifyAccess.shopify_url
        k = shopifyAccess.api_key
        s = shopifyAccess.api_secret
        a = shopifyAccess.access_token
        p_conn = shopify(t,k,s,a,'products')
        products = getProducts(p_conn)
        o_conn = shopify(t,k,s,a,'orders')
        orders = getOrders(o_conn)

        # print(products)
        # print(orders)

        user_details = PersonAccount.objects.get(pk=request.user.id)
        
        context = {'test':'test', 'products':products,'live':liveData, 'id':id, 'user':user_details}
    except ObjectDoesNotExist:
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="5;url=/pamine/#sellers">
            <title>ERROR</title>
        </head>
        <body>
            <h5>There's an issue with the seller. [Shopify Not Found]</h5>
            <p>This is a redirect page. You will be redirected in 5 seconds.</p>
            <p>If you are not redirected, please <a href="/pamine/#sellers">click here</a>.</p>
        </body>
        </html>
        """
        return HttpResponse(html_content)
    return render(request, 'accounts/livepage2.html', context)


@login_required(login_url='/login/')
def shopifysetup(request):
    try:
        shopify_access = request.user.shopifyaccess
    except ShopifyAccess.DoesNotExist:
        shopify_access = None
    
    if request.method == 'POST':
        form = ShopifyForm(request.POST, instance=shopify_access, user=request.user)
        if form.is_valid():
            messages.success(request, 'Shopify Setup Successfully')
            shopify_access = form.save(commit=False)
            shopify_access.user = request.user
            shopify_access.save()
            return redirect('setupshopify')
    else:
        form = ShopifyForm(instance=shopify_access, user=request.user)
    
    user_details = PersonAccount.objects.get(pk=request.user.id)
    context = {'form': form, 'user':user_details}
    return render(request, 'accounts/seller-details.html',context)

@login_required(login_url='/login/')
def history(request):
    orders = getAllOrdersFromAllStores()
    user_details = PersonAccount.objects.get(pk=request.user.id)
    # print(orders)
    getAllCustomerDetails()
    context = {'test':'test','user':user_details,'orders':orders}
    return render(request, 'accounts/history.html', context)
#LOGGED IN USER PAGES END


# DRIVER LICENSE START

def RGB2HEX(color):
    return "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2]))

def get_image(image_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    print('get_image')
    return image

def get_postal_image(image):
    print('get_postal_image')
    image = cv2.imread(image)
    return image

def get_uploaded_image(image):
    print('get_uploaded_image')
    image_ = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image_

def get_colors(image, number_of_colors):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rows, cols, channels = image.shape
    X = image.reshape(rows * cols, channels)
    
    modified_image = cv2.resize(image, (rows, cols), interpolation = cv2.INTER_AREA)
    modified_image = modified_image.reshape(modified_image.shape[0]*modified_image.shape[1], 3)

    clf = KMeans(n_clusters = number_of_colors, random_state=0)
    labels = clf.fit_predict(modified_image)
    counter = Counter(labels)

    unique_labels, counts = np.unique(labels, return_counts=True)
    label_order = np.argsort(counts)[::-1]  # descending order
    unique_labels = unique_labels[label_order]
    counts = counts[label_order]

    center_colors = clf.cluster_centers_

    ordered_colors = [center_colors[i] for i in counter.keys()]
    hex_colors = [RGB2HEX(ordered_colors[i]) for i in counter.keys()]

    print(len(hex_colors))
    return hex_colors
    
def compareColor(image1,image2):
    isSame = False
    count = 0
    for s1 in image1:
        for s2 in image2:
            if(s1 == s2):
                count+1
                return True

    return isSame

def image_to_opencv(image):
    image_bytes = image.read()

    np_arr = np.frombuffer(image_bytes, np.uint8)
    img_cv = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    return img_cv
    
# DRIVER LICENSE END
# POSTAL ID START

def postalHolokoteDetector(image,user):
    cv2.imwrite(settings.STATIC_ROOT + f'\postal_images\{user}_uploaded_postal.jpg',image)

    coefficients = [9,0,1] 
    m = np.array(coefficients).reshape((1,3))

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    cv2.imwrite(settings.STATIC_ROOT + f'\postal_images\{user}_postal_hsv.jpg',hsv)

    lower_blue = np.array([90,50,50]) # [110,50,50]
    upper_blue = np.array([130,255,255]) # [130,255,255]

    lower_violet = np.array([90,50,50]) # [110,50,50]
    upper_violet= np.array([160,255,255]) # [130,255,255]

    maskblue = cv2.inRange(hsv, lower_blue, upper_blue)
    maskviolet = cv2.inRange(hsv, lower_violet, upper_violet)

    bitwiseblue = cv2.bitwise_and(image,image, mask=maskblue)
    bitwiseviolet = cv2.bitwise_and(image,image, mask=maskviolet)
    cv2.imwrite(settings.STATIC_ROOT + f'\postal_images\{user}_postal_holokote.jpg',bitwiseblue)
    return bitwiseblue

def resizeImage(image):
    h, w = image.shape[0:2]
    return cv2.resize(image, (596,352))

def ORB_matches(image1,image2,user):
    img1 = resizeImage(image1)
    img2 = resizeImage(image2)
    # ORB Detector
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


    matchORB = bf.match(des1, des2)

    matchORB = sorted(matchORB, key = lambda x:x.distance)
    print(f"ORB Number of match {len(matchORB)}")
    match_resultORB = cv2.drawMatches(img1, kp1, img2, kp2, matchORB, None, flags=2)
    cv2.imwrite(settings.STATIC_ROOT + f'\postal_images\{user}_postal_match_result.jpg',match_resultORB)

    return len(matchORB)
# POSTAL ID END

# OTP
def isOTPValid(email,otp):
    print('isOTPValid')
    print(email)
    print(otp)
    otp_instances = OTP.objects.filter(email=email, otp_code=otp, expires_at__gt=timezone.now()).order_by('-created_at').first()
    
    print(otp_instances)

    if otp_instances is None:
        return False
    else:
        return True
    
def isOTPExpired(email,otp):
    print('isOTPExpired')
    print(email)
    print(otp)
    otp_instances = OTP.objects.filter(email=email, otp_code=otp, expires_at__lte=timezone.now()).order_by('-created_at').first()
    
    print(otp_instances)

    if otp_instances is None:
        return False
    else:
        return True
    
def isEmailUsed(email):
    isEmailUsed = User.objects.filter(email=email).exists()

    return isEmailUsed
# OTP

def presignup(request):
    if request.method == 'POST':
        data = request.POST
        if(isEmailUsed(data['email'])):
            messages.error(request, 'The email has already been used.')
            return render(request, 'accounts/presignup.html', {'data': data})
        else:
            initial_data = {
                'username': data['email'],
            }
            otp_instance = OTP.create_otp(data['email'])
            
            subject = 'PaMine Registration OTP'
            sender = 'paminesender@gmail.com'
            html_message = render_to_string('accounts/otp_email.html', {'otp':otp_instance.otp_code,'expiration':otp_instance.expires_at})
            recipients = [data['email']]
            send_mail(subject, None, sender, recipients, html_message=html_message)

            request.session['initial_data'] = initial_data
            return redirect(signup)
    else:
        pass
    return render(request, 'accounts/presignup.html')

def signup(request):
    if request.method == 'POST':
        data = request.POST
        form = RegistrationForm(request.POST, request.FILES)
        if isOTPValid(data['username'],data['otp']):
            if not isOTPExpired(data['username'],data['otp']):
                if form.is_valid():
                    # Create user
                    user = form.save(commit=False)
                    print('user_id',user.id)
                    id_verification = False
                    if(form.cleaned_data['id_options'] == 'Driver License'):
                        print('DL')
                        number_of_colors = 200
                        image_file = form.cleaned_data['id_image']
                        img_uploaded_cv = image_to_opencv(image_file)

                        img_uploaded_colors = get_colors(get_uploaded_image(img_uploaded_cv), number_of_colors)
                        img_base_colors = get_colors(get_image(settings.STATIC_ROOT + '\driver-license-base.jpg'), number_of_colors)
                        
                        id_verification = compareColor(img_uploaded_colors,img_base_colors)
                    elif(form.cleaned_data['id_options'] == 'Postal ID'):
                        print('Postal')
                        number_of_colors = 200
                        image_file = form.cleaned_data['id_image']
                        img_cv = image_to_opencv(image_file)

                        img_uploaded_holokote = postalHolokoteDetector(img_cv,form.cleaned_data['username'])
                        img_base_holokote = get_postal_image(settings.STATIC_ROOT + '\postal-holokote.jpg')

                        num_of_matches = ORB_matches(img_uploaded_holokote,img_base_holokote,form.cleaned_data['username'])

                        if(num_of_matches > 100):
                            id_verification = True
                        
                    
                    if(id_verification):
                        user.email = form.cleaned_data['username']
                        user.set_password(form.cleaned_data['password1'])
                        user.save()

                        # Create or update person account
                        try:
                            person_account = PersonAccount.objects.get(user=user)
                        except PersonAccount.DoesNotExist:
                            person_account = PersonAccount(user=user)

                        
                        person_account.first_name = form.cleaned_data['first_name']
                        person_account.last_name = form.cleaned_data['last_name']
                        person_account.phone = form.cleaned_data['phone']
                        person_account.address = form.cleaned_data['address']
                        person_account.id_options = form.cleaned_data['id_options']
                        person_account.account_type = form.cleaned_data['account_type']
                        person_account.id_image = form.cleaned_data['id_image']
                        person_account.save()

                        # Login user
                        # login(request, user)
                        messages.success(request, 'Account registed successfully.')
                        return render(request, 'accounts/signup.html', {'form': form})
                    else:
                        messages.error(request, 'The ID verification failed. Please try again with a valid ID.')
                        return render(request, 'accounts/signup.html', {'form': form})
                else:
                    messages.error(request, 'The form is not valid. Please correct the errors below.')
                    return render(request, 'accounts/signup.html', {'form': form})
            else:
                messages.error(request, 'The code has expired.')
                return render(request, 'accounts/signup.html', {'form': form})
        else:
            messages.error(request, 'Incorrect code.')
            return render(request, 'accounts/signup.html', {'form': form})
    else:
        initial_data = request.session.pop('initial_data', {})
        print(initial_data)
        if 'username' not in initial_data:
            return redirect(presignup)
        else:
            request.session['initial_data'] = initial_data
            form = RegistrationForm(initial=initial_data)
    return render(request, 'accounts/signup.html', {'form': form})

def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('home')
                else:
                    form.add_error(None, 'Invalid username or password')
        else:
            form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_user(request):
    print('Logout')
    logout(request)
    return redirect('login')










User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        PersonAccount.objects.create(user=instance)
