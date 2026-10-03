import urllib.request, json

# Test Punjab soil data (should give wheat/maize not tomato)
req = urllib.request.Request('http://localhost:8000/api/soil-data?state=Punjab&district=Ludhiana')
with urllib.request.urlopen(req) as r:
    d = json.loads(r.read())
print('Punjab soil:', d['data'])

# Test Himachal Pradesh soil data (should give apple)
req2 = urllib.request.Request('http://localhost:8000/api/soil-data?state=Himachal%20Pradesh&district=Shimla')
with urllib.request.urlopen(req2) as r:
    d2 = json.loads(r.read())
print('Himachal soil:', d2['data'])

# Test West Bengal (should give rice)
req3 = urllib.request.Request('http://localhost:8000/api/soil-data?state=West%20Bengal&district=Purba%20Bardhaman')
with urllib.request.urlopen(req3) as r:
    d3 = json.loads(r.read())
print('West Bengal soil:', d3['data'])

def predict(soil):
    payload = json.dumps({
        'n': soil['n'], 'p': soil['p'], 'k': soil['k'],
        'temperature': soil['temperature'], 'humidity': soil['humidity'],
        'ph': soil['ph'], 'rainfall': soil['rainfall'],
        'farm_acres': 2.5, 'user_budget': 60000,
        'state': 'Test', 'district': 'Test', 'farming_method': 'regular'
    }).encode()
    r = urllib.request.Request('http://localhost:8000/api/predict', data=payload, headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())

print()
p1 = predict(d['data'])
print('Punjab ->', p1['recommended_crop_display'], '('+str(p1['confidence_pct'])+'%)')
p2 = predict(d2['data'])
print('Himachal ->', p2['recommended_crop_display'], '('+str(p2['confidence_pct'])+'%)')
p3 = predict(d3['data'])
print('West Bengal ->', p3['recommended_crop_display'], '('+str(p3['confidence_pct'])+'%)')
