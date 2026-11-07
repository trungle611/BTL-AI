import os
import tempfile
from datetime import timedelta
from io import BytesIO
from fastapi.testclient import TestClient
from PIL import Image

dbfile = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
dbfile.close()
os.environ['DATABASE_URL'] = f"sqlite:///{dbfile.name}"

from app.main import app
from app.main import local_today
from app.db import Base, engine, SessionLocal
from app.models import Food


def setup_module():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add(Food(id='T1', name='Món kiểm thử', kcal_100g=250, protein_100g=10,
                    carb_100g=20, fat_100g=5, source_type='test_fixture',
                    source_reference='Synthetic test fixture', reference_mass_g=100,
                    data_version='test-v1', is_verified=False, avoid_tags=[]))
        db.commit()


def test_confirm_and_dashboard():
    with TestClient(app) as client:
        assert client.post('/api/food-logs', json={'food_id':'T1','grams':200,'meal_type':'lunch','confirmed':False}).status_code == 422
        response = client.post('/api/food-logs', json={'food_id':'T1','grams':200,'meal_type':'lunch','confirmed':True})
        assert response.status_code == 201
        assert response.json()['nutrition']['kcal'] == 500
        dashboard = client.get('/api/dashboard').json()
        assert dashboard['totals']['kcal'] == 500
        assert dashboard['entries'][0]['source_reference'] == 'Synthetic test fixture'


def test_dated_daily_targets_are_scoped_and_reject_past_date():
    deadline = (local_today() + timedelta(days=90)).isoformat()
    first = {'X-Visitor-Id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'}
    second = {'X-Visitor-Id': 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'}
    with TestClient(app) as client:
        saved = client.put('/api/profile', headers=first, json={
            'age': 25, 'height_cm': 170, 'weight_kg': 70, 'target_weight_kg': 67,
            'target_date': deadline, 'sex': 'female', 'activity_level': 'moderate',
            'goal': 'lose'})
        assert saved.status_code == 200
        targets = saved.json()['daily_targets']
        assert targets['target_date'] == deadline
        assert targets['days_remaining'] == 90
        assert targets['kcal'] >= 1200
        assert targets['protein_g'] == 85
        assert targets['protein_factor'] == 1.2
        assert client.get('/api/profile', headers=first).json()['daily_targets'] == targets
        assert client.get('/api/profile', headers=second).json()['daily_targets'] is None
        rushed = client.put('/api/profile', headers=first, json={
            'age': 25, 'height_cm': 170, 'weight_kg': 70, 'target_weight_kg': 60,
            'target_date': (local_today() + timedelta(days=7)).isoformat(),
            'sex': 'female', 'activity_level': 'moderate', 'goal': 'lose'})
        assert rushed.json()['daily_targets']['timeline_warning'] is True
        assert rushed.json()['daily_targets']['kcal'] >= 1200
        strength = client.put('/api/profile', headers=first, json={
            'age': 25, 'height_cm': 170, 'weight_kg': 70, 'target_weight_kg': 67,
            'target_date': deadline, 'sex': 'female', 'activity_level': 'moderate',
            'protein_mode': 'strength', 'goal': 'lose'})
        assert strength.json()['daily_targets']['protein_g'] == 110
        assert strength.json()['daily_targets']['protein_factor'] == 1.6
        rejected = client.put('/api/profile', headers=first, json={
            'target_date': local_today().isoformat()})
        assert rejected.status_code == 422


def test_scan_rejects_bad_upload():
    with TestClient(app) as client:
        response = client.post('/api/scan', files={'file':('bad.txt', b'hello', 'text/plain')})
        assert response.status_code == 415


def test_scan_groups_dishes_and_requires_selection(monkeypatch):
    monkeypatch.setattr('app.ai.scan_image', lambda *_: {'dishes': [
        {'candidate_labels':['Món kiểm thử'], 'visible_ingredients':[], 'uncertainty_reason':''},
        {'candidate_labels':['món không có'], 'visible_ingredients':[], 'uncertainty_reason':'Không rõ'}],
        'warning':''})
    image = BytesIO()
    Image.new('RGB', (32, 32), 'white').save(image, format='PNG')
    with TestClient(app) as client:
        response = client.post('/api/scan', files={'file':('meal.png', image.getvalue(), 'image/png')})
        assert response.status_code == 200
        dishes = response.json()['dishes']
        assert len(dishes) == 2
        assert dishes[0]['candidates'][0]['id'] == 'T1'
        assert dishes[1]['candidates'] == []


def test_batch_logs_are_all_or_nothing():
    valid = {'food_id':'T1','grams':100,'meal_type':'lunch','confirmed':True}
    invalid = {**valid, 'food_id':'UNKNOWN'}
    with TestClient(app) as client:
        before = len(client.get('/api/dashboard').json()['entries'])
        assert client.post('/api/food-logs/batch', json={'items':[valid,invalid]}).status_code == 404
        assert len(client.get('/api/dashboard').json()['entries']) == before
        response = client.post('/api/food-logs/batch', json={'items':[valid,valid]})
        assert response.status_code == 201
        assert len(response.json()['entries']) == 2


def test_log_can_be_edited_and_deleted():
    with TestClient(app) as client:
        created = client.post('/api/food-logs', json={'food_id':'T1','grams':100,'meal_type':'lunch','confirmed':True}).json()
        changed = client.patch(f"/api/food-logs/{created['id']}", json={'grams':200,'meal_type':'dinner'})
        assert changed.status_code == 200
        assert changed.json()['nutrition']['kcal'] == 500
        assert changed.json()['meal_type'] == 'dinner'
        assert client.delete(f"/api/food-logs/{created['id']}").status_code == 204
        assert client.patch(f"/api/food-logs/{created['id']}", json={'grams':100,'meal_type':'lunch'}).status_code == 404


def test_workout_progress_is_separate_from_food_logs():
    with TestClient(app) as client:
        before = client.get('/api/dashboard').json()['totals']
        today = client.get('/api/workouts/today').json()
        assert len(today['items']) == 3
        assert client.post('/api/workouts/squat/start').json()['items'][1]['status'] == 'started'
        assert client.post('/api/workouts/squat/complete').json()['items'][1]['status'] == 'completed'
        assert client.get('/api/workouts/today').json()['items'][1]['status'] == 'completed'
        assert client.get('/api/dashboard').json()['totals'] == before


def test_repeated_confirmation_does_not_duplicate_meals():
    payload = {'confirmation_id':'demo-confirmation-001', 'items':[
        {'food_id':'T1','grams':150,'meal_type':'lunch','confirmed':True}]}
    with TestClient(app) as client:
        before = len(client.get('/api/dashboard').json()['entries'])
        first = client.post('/api/food-logs/batch', json=payload)
        second = client.post('/api/food-logs/batch', json=payload)
        assert first.status_code == second.status_code == 201
        assert first.json()['entries'][0]['id'] == second.json()['entries'][0]['id']
        assert len(client.get('/api/dashboard').json()['entries']) == before + 1
        changed = {**payload, 'items':[{**payload['items'][0], 'grams':200}]}
        assert client.post('/api/food-logs/batch', json=changed).status_code == 409


def test_custom_food_can_be_confirmed_and_replayed():
    payload = {'confirmation_id':'custom-confirmation-001', 'items':[
        {'custom_food':{'name':'Món mới kiểm thử','kcal_100g':120,'protein_100g':5,
                        'carb_100g':15,'fat_100g':3},
         'grams':200,'meal_type':'dinner','confirmed':True}]}
    with TestClient(app) as client:
        before = client.get('/api/dashboard').json()['totals']['kcal']
        first = client.post('/api/food-logs/batch', json=payload)
        assert first.status_code == 201
        assert first.json()['entries'][0]['nutrition']['kcal'] == 240
        assert first.json()['entries'][0]['is_verified'] is False
        second = client.post('/api/food-logs/batch', json=payload)
        assert second.json()['entries'][0]['id'] == first.json()['entries'][0]['id']
        assert client.get('/api/dashboard').json()['totals']['kcal'] == before + 240
        assert client.get('/api/foods', params={'q':'Món mới kiểm thử'}).json()[0]['source_type'] == 'user_entered'


def test_workout_plan_selection_and_progress(monkeypatch):
    from datetime import date
    current_day = [date(2026, 11, 9)]
    monkeypatch.setattr('app.main.local_today', lambda: current_day[0])
    with TestClient(app) as client:
        plans = client.get('/api/workouts/plans').json()
        assert {(plan['goal'], plan['method']) for plan in plans} == {
            ('gain','PPL'),('gain','UL'),('lose','PPL'),('lose','UL')}
        assert client.post('/api/workouts/select', json={'plan_id':'missing'}).status_code == 404
        selected = client.post('/api/workouts/select', json={'plan_id':'gain_ppl'})
        assert selected.status_code == 200
        today = selected.json()
        assert today['selected_plan']['id'] == 'gain_ppl'
        assert today['session_name'] == 'Push'
        assert today['items']
        assert client.post(f"/api/workouts/{today['items'][0]['id']}/start").status_code == 409
        missed = client.post('/api/workouts/attendance', json={'status':'missed'}).json()
        assert missed['attendance'] == 'missed'
        assert client.post(f"/api/workouts/{today['items'][0]['id']}/start").status_code == 409
        current_day[0] = date(2026, 11, 10)
        next_day = client.get('/api/workouts/today').json()
        assert next_day['session_name'] == 'Push'
        assert next_day['attendance'] is None
        assert next_day['attendance_history'][-2]['status'] == 'missed'
        assert client.post('/api/workouts/attendance', json={'status':'attended'}).status_code == 200
        first_id = today['items'][0]['id']
        assert client.post(f'/api/workouts/{first_id}/start').json()['items'][0]['status'] == 'started'
        assert client.post(f'/api/workouts/{first_id}/complete').json()['items'][0]['status'] == 'completed'
        for item in today['items'][1:]:
            assert client.post(f"/api/workouts/{item['id']}/complete").status_code == 200
        finished = client.get('/api/workouts/today').json()
        assert finished['attendance'] == 'completed'
        assert client.post('/api/workouts/attendance', json={'status':'missed'}).status_code == 409
        current_day[0] = date(2026, 11, 11)
        following = client.get('/api/workouts/today').json()
        assert following['session_name'] == 'Pull'
        assert following['session_number'] == 2


def test_profile_weight_guidance_and_choice(monkeypatch):
    monkeypatch.setattr('app.ai.generate_profile_guidance', lambda *_: {
        'summary':'Mục tiêu tăng cân: ăn đa dạng và tập đều.',
        'food_options':[{'title':'Bữa cân bằng','detail':'Ăn đủ các nhóm thực phẩm','examples':['Cơm, trứng, rau']},
                        {'title':'Bữa chia nhỏ','detail':'Chia bữa theo lịch','examples':['Sữa chua, trái cây']}],
        'ppl_note':'Phù hợp nếu có thời gian nhiều buổi.',
        'ul_note':'Phù hợp nếu có ít buổi hơn.'})
    with TestClient(app) as client:
        saved = client.put('/api/profile', json={'age':22,'height_cm':170,'weight_kg':60,
            'target_weight_kg':65,'goal':'gain','target_kcal':2000,'avoid_tags':[]})
        assert saved.status_code == 200
        assert saved.json()['target_weight_kg'] == 65
        analyzed = client.post('/api/profile/analyze')
        assert analyzed.status_code == 200
        assert len(analyzed.json()['analysis']['food_options']) == 2
        assert {item['id'] for item in analyzed.json()['analysis']['workout_options']} == {'gain_ppl','gain_ul'}
        assert client.post('/api/profile/choice', json={'food_choice':'wrong'}).status_code == 422
        chosen = client.post('/api/profile/choice', json={'food_choice':'food_1','workout_choice':'gain_ul'})
        assert chosen.status_code == 200
        assert chosen.json()['food_choice'] == 'food_1'
        assert client.get('/api/workouts/today').json()['selected_plan']['id'] == 'gain_ul'
        changed = client.put('/api/profile', json={'age':22,'height_cm':170,'weight_kg':60,
            'target_weight_kg':66,'goal':'gain','target_kcal':2000,'avoid_tags':[]})
        assert changed.json()['analysis'] is None


def test_browser_demo_sessions_do_not_share_data():
    first = {'X-Visitor-Id':'11111111-1111-4111-8111-111111111111'}
    second = {'X-Visitor-Id':'22222222-2222-4222-8222-222222222222'}
    with TestClient(app) as client:
        assert client.put('/api/profile', headers=first, json={'weight_kg':62,'target_weight_kg':66}).status_code == 200
        assert client.get('/api/profile', headers=second).json()['weight_kg'] is None
        food = {'custom_food':{'name':'Món riêng của phiên đầu','kcal_100g':100},
                'grams':100,'meal_type':'lunch','confirmed':True}
        own_log = client.post('/api/food-logs/batch', headers=first, json={'items':[food]})
        assert own_log.status_code == 201
        own_entry = own_log.json()['entries'][0]
        assert client.get('/api/dashboard', headers=first).json()['totals']['kcal'] == 100
        assert client.get('/api/dashboard', headers=second).json()['totals']['kcal'] == 0
        assert client.get('/api/foods', headers=second, params={'q':'Món riêng'}).json() == []
        assert client.get(f"/api/foods/{own_entry['food_id']}", headers=second).status_code == 404
        assert client.delete(f"/api/food-logs/{own_entry['id']}", headers=second).status_code == 404
        assert client.post('/api/workouts/select', headers=first, json={'plan_id':'gain_ppl'}).status_code == 200
        assert client.get('/api/workouts/today', headers=second).json()['selected_plan'] is None


def test_public_demo_requires_visitor_id(monkeypatch):
    monkeypatch.setenv('REQUIRE_VISITOR_ID', '1')
    with TestClient(app) as client:
        assert client.get('/api/profile').status_code == 400
        assert client.get('/api/profile', headers={'X-Visitor-Id':'not-a-uuid'}).status_code == 400
        assert client.get('/api/profile', headers={'X-Visitor-Id':'33333333-3333-4333-8333-333333333333'}).status_code == 200


def test_profile_and_plan_fallback(monkeypatch):
    def ai_unavailable(*args, **kwargs):
        raise RuntimeError('AI unavailable in unit test')
    monkeypatch.setattr('app.ai.generate_plan', ai_unavailable)
    with SessionLocal() as db:
        for id, kcal in [('T2', 150), ('T3', 200)]:
            db.add(Food(id=id, name=id, kcal_100g=kcal, protein_100g=10,
                        carb_100g=20, fat_100g=5, source_type='test_fixture',
                        source_reference='Synthetic test fixture', reference_mass_g=100,
                        data_version='test-v1', is_verified=False, avoid_tags=[]))
        db.commit()
    with TestClient(app) as client:
        saved = client.put('/api/profile', json={'age':22,'goal':'maintain','target_kcal':1800,'avoid_tags':[]})
        assert saved.status_code == 200
        assert client.get('/api/profile').json()['age'] == 22
        response = client.post('/api/meal-plans/generate', json={'week_start':'2026-11-09','target_kcal':1800,'avoid_tags':[]})
        assert response.status_code == 201
        data = response.json()
        assert data['generation_mode'] == 'rule_fallback'
        assert len(data['days']) == 7
        assert all(1440 <= day['total_kcal'] <= 2160 for day in data['days'])

