import os
import tempfile
from io import BytesIO
from fastapi.testclient import TestClient
from PIL import Image

dbfile = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
dbfile.close()
os.environ['DATABASE_URL'] = f"sqlite:///{dbfile.name}"

from app.main import app
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

