import urllib.request, json
import urllib.parse

def test_state(state, district):
    s = urllib.parse.quote(state)
    d = urllib.parse.quote(district)
    req = urllib.request.Request(f'http://localhost:8000/api/soil-data?state={s}&district={d}')
    with urllib.request.urlopen(req) as r:
        soil = json.loads(r.read())['data']
        
    payload = json.dumps({
        'n': soil['n'], 'p': soil['p'], 'k': soil['k'],
        'temperature': soil['temperature'], 'humidity': soil['humidity'],
        'ph': soil['ph'], 'rainfall': soil['rainfall'],
        'farm_acres': 2.5, 'user_budget': 60000,
        'state': state, 'district': district, 'farming_method': 'regular'
    }).encode()
    r = urllib.request.Request('http://localhost:8000/api/predict', data=payload, headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(r) as resp:
        p = json.loads(resp.read())
        print(f"{state} -> {p['recommended_crop_display']} ({p['confidence_pct']}%)")

states = ['Andhra Pradesh', 'Telangana', 'Karnataka', 'Tamil Nadu', 'Maharashtra', 'Gujarat', 'Rajasthan', 'Madhya Pradesh']
for s in states:
    test_state(s, 'Unknown')
