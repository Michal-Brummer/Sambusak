import requests

# Server address
url = "http://127.0.0.1:5000/register"

# Test data for registration
data = {
    "username": "TestUser",
    "password": "TestPassword123"
}

# Sending POST request
try:
    response = requests.post(url, json=data)
    
    # Printing the server response
    print("Response status code:", response.status_code)
    print("Response JSON:", response.json())

    # Additional validation
    if response.status_code == 200:
        print("Registration test passed!")
    elif response.status_code == 400:
        print("Registration test failed: User already exists or invalid input.")
    else:
        print("Unexpected response from server.")
except Exception as e:
    print("An error occurred during the registration test:", e)
