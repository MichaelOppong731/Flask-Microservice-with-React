import os, requests

# AUTH_SVC_URL = os.environ.get("AUTH_SVC_URL", "http://auth-service:5000")
AUTH_SVC_URL = "http://localhost:5000"
def login(request):
    auth = request.authorization
    if not auth:
        return None, ("missing credentials", 401)

    basicAuth = (auth.username, auth.password)

    # Ensure no double slashes in the URL
    url = AUTH_SVC_URL.rstrip("/") + "/login"

    response = requests.post(url, auth=basicAuth)

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)