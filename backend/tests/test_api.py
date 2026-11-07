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

