import os, requests

# AUTH_SVC_URL = os.environ.get("AUTH_SVC_URL")
AUTH_SVC_URL = "http://localhost:5000"
def token(request):
    if not "Authorization" in request.headers:
        return None, ("missing credentials", 401)

    token = request.headers["Authorization"]

    if not token:
        return None, ("missing credentials", 401)

    url = AUTH_SVC_URL.rstrip("/") + "/validate"
    response = requests.post(
        url,
        headers={"Authorization": token},
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
