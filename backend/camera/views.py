from django.shortcuts import render

# View for the camera stream page
def index(request):
    """
    Renders the template for the live stream page.
    """
    return render(request, 'camera/index.html')