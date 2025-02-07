from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Welcome to the Birdhouse Monitor!</h1><p>Go to <a href='/camera/'>/camera/</a> to view the camera.</p>")