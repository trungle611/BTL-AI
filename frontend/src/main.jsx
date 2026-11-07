import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import ScanSection from './ScanSection.jsx';
import './style.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
async function call(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : `Lỗi ${response.status}`);
  return body;
}
const fmt = x => Number(x || 0).toLocaleString('vi-VN', { maximumFractionDigits: 1 });

function App() {
  const [tab, setTab] = useState('scan');
  const [foods, setFoods] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [plan, setPlan] = useState(null);
  const [target, setTarget] = useState(1800);
  const [avoid, setAvoid] = useState('');
  const [profile, setProfile] = useState({age:'',height_cm:'',weight_kg:'',goal:'maintain',target_kcal:1800,avoid_tags:[]});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const refresh = async () => {
    const [list, dash, currentProfile] = await Promise.all([call('/api/foods'), call('/api/dashboard'), call('/api/profile')]);
    setFoods(list); setDashboard(dash); setProfile(currentProfile); setTarget(currentProfile.target_kcal); setAvoid(currentProfile.avoid_tags.join(', '));
  };
  useEffect(() => { refresh().catch(e => setMessage(e.message)); }, []);

  async function run(fn) {
    setBusy(true); setMessage('');
    try { await fn(); } catch (e) { setMessage(e.message); } finally { setBusy(false); }
  }
  const generate = () => run(async () => {
    const monday = new Date(); monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
    const weekStart = `${monday.getFullYear()}-${String(monday.getMonth()+1).padStart(2,'0')}-${String(monday.getDate()).padStart(2,'0')}`;
    const result = await call('/api/meal-plans/generate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({week_start:weekStart,target_kcal:Number(target),avoid_tags:avoid.split(',').map(s=>s.trim()).filter(Boolean)})});
    setPlan(result);
  });
  const saveProfile = () => run(async () => {
    const body = {...profile, age:profile.age === '' ? null : Number(profile.age), height_cm:profile.height_cm === '' ? null : Number(profile.height_cm), weight_kg:profile.weight_kg === '' ? null : Number(profile.weight_kg), target_kcal:Number(profile.target_kcal), avoid_tags:avoid.split(',').map(s=>s.trim()).filter(Boolean)};
    const result = await call('/api/profile', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    setProfile(result); setTarget(result.target_kcal); setMessage('Đã lưu hồ sơ thử nghiệm.');
  });

  return <main>
    <header><div><p className="eyebrow">TRỢ LÝ DINH DƯỠNG MÓN VIỆT</p><h1>HBTNFIT</h1><p>Nhận diện món ăn, xác nhận khẩu phần và lập thực đơn có kiểm tra.</p></div><div className="badge">Bản thử nghiệm Track 1</div></header>
    <nav>{[['scan','Quét và ghi bữa'],['dashboard','Nhật ký'],['plan','Thực đơn 7 ngày'],['profile','Hồ sơ']].map(([id,label])=><button key={id} className={tab===id?'active':''} onClick={()=>setTab(id)}>{label}</button>)}</nav>
    {message && <div className="notice" role="status">{message}</div>}
    {tab==='scan' && <ScanSection call={call} foods={foods} refresh={refresh} setTab={setTab} setMessage={setMessage}/>}
    {tab==='dashboard' && <section className="card"><h2>Nhật ký hôm nay</h2><div className="metric">{fmt(dashboard?.totals.kcal)} <span>kcal</span></div><p>Đạm {fmt(dashboard?.totals.protein)} g · Bột đường {fmt(dashboard?.totals.carb)} g · Béo {fmt(dashboard?.totals.fat)} g</p>{dashboard?.entries.length ? dashboard.entries.map(x=><div className="entry" key={x.id}><strong>{x.name}</strong><span>{fmt(x.grams)} g · {fmt(x.nutrition.kcal)} kcal</span><small>{x.source_reference}</small></div>) : <p>Chưa có bữa ăn nào được ghi.</p>}</section>}
    {tab==='plan' && <section className="grid"><div className="card"><h2>Lập thực đơn tuần</h2><p>Chỉ dùng món trong danh mục. Hệ thống kiểm tra ID, thành phần cần tránh và tổng năng lượng.</p><label>Mục tiêu tham khảo (kcal/ngày)<input type="number" min="900" max="5000" value={target} onChange={e=>setTarget(e.target.value)}/></label><label>Thành phần cần tránh (tag, cách nhau bằng dấu phẩy)<input value={avoid} onChange={e=>setAvoid(e.target.value)} placeholder="shrimp, pork"/></label><button disabled={busy} onClick={generate}>Tạo thực đơn</button><p className="muted">Mục tiêu tự nhập chỉ phục vụ bản thử nghiệm; đây không phải chỉ định y khoa.</p></div><div className="card"><h2>Kết quả</h2>{plan ? <><p>Chế độ: {plan.generation_mode === 'gemini' ? 'Gemini + hậu kiểm' : 'Dự phòng theo quy tắc'}</p>{plan.days.map(day=><div className="day" key={day.day}><strong>Ngày {day.day} · {fmt(day.total_kcal)} kcal</strong>{day.meals.map(m=><p key={m.meal_slot}>{m.meal_slot}: {m.name}, {fmt(m.grams)} g</p>)}</div>)}<p className="warn">Kiểm tra nguồn dữ liệu từng món trước khi dùng ngoài bản demo.</p></> : <p>Chưa có thực đơn.</p>}</div></section>}
    {tab==='profile' && <section className="card"><h2>Hồ sơ thử nghiệm</h2><p>Thông tin lưu trên máy chạy backend. Chưa có tài khoản riêng cho nhiều người dùng.</p><div className="row"><label>Tuổi (từ 18)<input type="number" value={profile.age ?? ''} onChange={e=>setProfile({...profile,age:e.target.value})}/></label><label>Chiều cao (cm)<input type="number" value={profile.height_cm ?? ''} onChange={e=>setProfile({...profile,height_cm:e.target.value})}/></label></div><div className="row"><label>Cân nặng (kg)<input type="number" value={profile.weight_kg ?? ''} onChange={e=>setProfile({...profile,weight_kg:e.target.value})}/></label><label>Mục tiêu<select value={profile.goal} onChange={e=>setProfile({...profile,goal:e.target.value})}><option value="maintain">Duy trì</option><option value="gain">Tăng cân</option><option value="lose">Giảm cân</option></select></label></div><label>Mục tiêu năng lượng tự đặt (kcal/ngày)<input type="number" value={profile.target_kcal} onChange={e=>setProfile({...profile,target_kcal:e.target.value})}/></label><label>Thành phần cần tránh (tag, cách nhau bằng dấu phẩy)<input value={avoid} onChange={e=>setAvoid(e.target.value)}/></label><button disabled={busy} onClick={saveProfile}>Lưu hồ sơ</button><p className="muted">Ứng dụng không tự tính mục tiêu y khoa từ tuổi, chiều cao và cân nặng.</p></section>}
    <footer>Chỉ mang tính tham khảo. Dữ liệu demo được đánh dấu riêng; không dùng cho quyết định sức khỏe.</footer>
  </main>;
}

createRoot(document.getElementById('root')).render(<App/>);
