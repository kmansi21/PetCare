from django.shortcuts import render , redirect
from django.conf import settings
from django.views.decorators.cache import never_cache
from bson.objectid import ObjectId
from datetime import datetime
from django.core.files.storage import FileSystemStorage
import uuid
@never_cache

def home(request):
    return render(request,"index.html")

def register(request):
    return render(request, "login.html")

def adduser(request):
    msg = ""
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone = request.POST.get("phone")
        role = request.POST.get("role")
        address = request.POST.get("address")
        coll = settings.DB["users"]
        
        existing_user = coll.find_one({"email": email,"role":role})
        if existing_user:
            return render(request, "login.html", {
                "error": f"User with this email already exists as {role}"
            })
            
        dic = {
            "name": name,
            "email": email,
            "password": password,
            "phone": phone,
            "role": role,
            "address": address
        }

        try:
            coll = settings.DB["users"]
            coll.insert_one(dic)
            msg = f"Registration successful as {role}. Please login."
        except:
            msg = "Registration failed"

    return render(request, "login.html", {"status": msg})

def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        ps = request.POST.get("password")
        role=request.POST.get("role")

        coll = settings.DB["users"]
        user = coll.find_one({"email": email, "password": ps , "role":role})

        if user:
            request.session['authenticated'] = True
            request.session['email'] = user["email"]
            request.session['user'] = user["name"]
            request.session['role'] = user["role"]

            if user["role"] == "adopter":
                return redirect('/adopterDashboard/')
            else:
                return redirect('/providerDashboard/')
        else:
            return render(request, "login.html", {
                "error": "Invalid email or password"
            })

    return render(request, "login.html")

# ================================================================== ADOPTER DASHBOARD =================================================== #

def adopterDashboard(request):
    if not request.session.get('authenticated'):
        return redirect('/login/')
    username = request.session.get('user')
    return render(request, "adopter dashboard.html",{"name":username})

# ================================================================== ADOPTER PET LIST =================================================== #

def adoptpet(request):
    if not request.session.get('authenticated'):
        return redirect('/login/')

    username = request.session.get('user')
    pets_coll = settings.DB["pets"]

    # Only show pets that are Available
    pets_cursor = pets_coll.find({"status": "Available"})

    pets = []
    for pet in pets_cursor:
        pets.append({
            "id": str(pet.get("_id")),
            "name": pet.get("name"),
            "type": pet.get("type"),
            "category": pet.get("category"),
            "location": pet.get("location"),
            "age": pet.get("age"),
            "description": pet.get("description"),
            "photo": pet.get("photo"),
            "contact": pet.get("contact"),    
            "status": pet.get("status") 
        })

    return render(request, "adopt.html", {
        "name": username,
        "pets": pets
    })
    
# ==================================================================  ADOPT FROM =================================================== #
def adopt_form(request, pet_id):
    adoption_collection = settings.DB["adopt_form"]
    pets_collection = settings.DB["pets"]

    pet = pets_collection.find_one({"_id": ObjectId(pet_id)})

    if not pet:
        return redirect("/adopt/")

    # Convert ObjectId to string for template
    pet["id"] = str(pet["_id"])

    if request.method == "POST":

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        reason = request.POST.get("reason")
        adopter_email = request.session.get("email")

        adoption_collection.insert_one({
            "pet_id": pet["_id"],
            "pet_name": pet["name"],
            "pet_photo": pet["photo"],
            "adopter_name": name,
            "phone": phone,
            "address": address,
            "adopter_email": adopter_email,
            "reason": reason,
            "status": "Adopted",
            "date": datetime.now()
        })

        pets_collection.update_one(
            {"_id": pet["_id"]},
            {"$set": {"status": "Adopted"}}
        )

        return redirect("/adopterDashboard/")

    return render(request, "adopt pet form.html", {"pet": pet})

# ================================================================== ADOPTER CARE TIPS =================================================== #


def caretips(request):
    if not request.session.get('authenticated'):
        return redirect('/login/')
    username = request.session.get('user')
    return render(request, "care-tips.html",{"name":username})

# ================================================================== ADOPTER PROFILE =================================================== #
def profile_adopter(request):
    email = request.session.get('email')
    role = request.session.get('role')

    users_coll = settings.DB["users"]
    adoption_coll = settings.DB["adopt_form"]

    user = users_coll.find_one({"email": email, "role": role})

 
    adopted_cursor = adoption_coll.find({
        "adopter_email": email
    })

    adopted_pets = []
    for adoption in adopted_cursor:
        adopted_pets.append({
            "name": adoption.get("pet_name"),
            "photo": adoption.get("pet_photo"),
            "date": adoption.get("date")
        })

    return render(request, "profile-adopter.html", {
        "user": user,
        "adopted_pets": adopted_pets
    })





# ================================================================== PROVIDER DASHBOARD =================================================== #

def providerDashboard(request):
    if not request.session.get('authenticated'):
        return redirect('/login/')
    username = request.session.get('user')
    return render(request, "provider dashboard.html",{"name":username})
# ================================================================== PROVIDER  PROFILE =================================================== #

def profile_provider(request):
    email = request.session.get('email')
    role = request.session.get('role')

    user = settings.DB["users"].find_one({"email": email, "role": role})

    return render(request, "profile-provider.html", {"user": user})

# ================================================================== PROVIDER  ADD PET =================================================== #

def addpet(request):
    if not request.session.get('authenticated'):
        return redirect('/login/')  

    if request.method == "POST":
        name = request.POST.get("name")
        animal_type = request.POST.get("type")
        category = request.POST.get("category")
        location = request.POST.get("location")
        contact = request.POST.get("contact")
        age = request.POST.get("age")
        description = request.POST.get("description")
        photo = request.FILES.get("photo")

        provider_email = request.session.get("email")
        
        pet_data = {
            "name": name,
            "type": animal_type,
            "category": category,
            "location": location,
            "age": age,
            "description": description,
            "provider_email": provider_email,
            "contact": contact,
            "status": "Available"
        }

        if photo:
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            unique_name = str(uuid.uuid4()) + "_" + photo.name
            filename = fs.save(unique_name, photo)
            pet_data["photo"] = settings.MEDIA_URL + filename
        coll = settings.DB["pets"]
        coll.insert_one(pet_data)

        return redirect('/add-pet/?success=1')


    success = request.GET.get('success')
    return render(request, "add pet.html", {"success": success})    

# ================================================================== PROVIDER PET LIST =================================================== #

def mypets(request):
    if not request.session.get('authenticated'):
        return redirect('/login/')
    
    provider_email = request.session.get('email')
    pets_coll = settings.DB["pets"]
    adoption_coll = settings.DB["adopt_form"]

    pets_cursor = pets_coll.find({"provider_email": provider_email})
    
    pets = []
    for pet in pets_cursor:
        cleaned_pet = {
            "id": str(pet.get("_id")),
            "name": pet.get("name"),
            "type": pet.get("type"),
            "category": pet.get("category"),
            "location": pet.get("location"),
            "age": pet.get("age"),
            "description": pet.get("description"),
            "status": pet.get("status", "Available"),
            "photo": pet.get("photo"),
            "contact": pet.get("contact"),
            "adopter_name": None,
            "adopter_phone": None,
            "adopter_address": None,
        }


        if pet.get("status") == "Adopted":
            adoption = adoption_coll.find_one({"pet_id": pet["_id"]})
            if adoption:
                cleaned_pet["adopter_name"] = adoption.get("adopter_name")
                cleaned_pet["adopter_phone"] = adoption.get("phone")
                cleaned_pet["adopter_address"] = adoption.get("address")

        pets.append(cleaned_pet)

    return render(request, "my-pets.html", {"pets": pets})














def logout(request):
    request.session.flush()   
    return redirect('/')
