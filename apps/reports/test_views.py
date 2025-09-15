from django.http import JsonResponse

def test_reports_endpoint(request):
    return JsonResponse({
        'message': 'Reports endpoint is working!',
        'status': 'success',
        'method': request.method
    })