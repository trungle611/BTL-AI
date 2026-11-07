import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
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
  const [search, setSearch] = useState('');
  const [selection, setSelection] = useState('');
  const [scan, setScan] = useState(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [grams, setGrams] = useState(250);
  const [mealType, setMealType] = useState('lunch');
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
  const chosen = foods.find(f => f.id === selection);
  const calculated = chosen ? Object.fromEntries(['kcal','protein','carb','fat'].map(k => [k, chosen[`${k}_100g`] * Number(grams || 0) / 100])) : null;

  async function run(fn) {
    setBusy(true); setMessage('');
    try { await fn(); } catch (e) { setMessage(e.message); } finally { setBusy(false); }
  }
  const uploadFile = selectedFile => run(async () => {
    if (!selectedFile) throw new Error('Hãy chọn ảnh món ăn.');
    const form = new FormData(); form.append('file', selectedFile);
    const result = await call('/api/scan', { method: 'POST', body: form });
    setScan(result);
    setSelection(result.candidates[0]?.id || '');
    if (result.status === 'unknown') setMessage('Chưa nhận diện được món trong danh mục. Hãy tìm thủ công.');
  });
  const useDemo = async () => {
    const response = await fetch('/demo/pho_bo_synthetic.png');
    const blob = await response.blob();
    const demoFile = new File([blob], 'pho_bo_synthetic.png', {type:'image/png'});
    setFile(demoFile); setPreview('/demo/pho_bo_synthetic.png'); uploadFile(demoFile);
  };
  const save = () => run(async () => {
    if (!selection) throw new Error('Hãy chọn món.');
    await call('/api/food-logs', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({food_id:selection, grams:Number(grams), meal_type:mealType, confirmed:true}) });
    await refresh(); setMessage('Đã lưu bữa ăn.'); setTab('dashboard');
  });
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
    {tab==='scan' && <section className="grid"><div className="card"><h2>1. Nhận diện ảnh</h2><p>Ảnh một món, JPG/PNG/WEBP, tối đa 5 MB.</p><input type="file" accept="image/jpeg,image/png,image/webp" onChange={e=>{const selected=e.target.files[0];setFile(selected);setPreview(selected?URL.createObjectURL(selected):'');}}/>{preview && <img className="preview" src={preview} alt="Ảnh món ăn đang chọn"/>}<div className="actions"><button disabled={busy} onClick={()=>uploadFile(file)}>{busy?'Đang phân tích…':'Phân tích ảnh'}</button><button className="secondary" disabled={busy} onClick={useDemo}>Thử ảnh phở mẫu</button></div>{scan && <div className="result"><b>Trạng thái: {scan.status === 'needs_confirmation' ? 'Cần xác nhận' : 'Chưa rõ'}</b><p>{scan.warnings.join(' ')}</p>{scan.candidates.length>0 && <p>Gợi ý: {scan.candidates.map(x=>x.name).join(', ')}</p>}</div>}</div><div className="card"><h2>2. Xác nhận món và khẩu phần</h2><label>Tìm món thủ công<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Ví dụ phở bò"/></label><label>Món ăn<select value={selection} onChange={e=>setSelection(e.target.value)}><option value="">Chọn món</option>{foods.filter(f=>!search || f.name.toLowerCase().includes(search.toLowerCase())).map(f=><option key={f.id} value={f.id}>{f.name}</option>)}</select></label><div className="row"><label>Khẩu phần (g)<input type="number" min="1" max="2000" value={grams} onChange={e=>setGrams(e.target.value)}/></label><label>Bữa<select value={mealType} onChange={e=>setMealType(e.target.value)}><option value="breakfast">Sáng</option><option value="lunch">Trưa</option><option value="dinner">Tối</option><option value="snack">Phụ</option></select></label></div>{chosen && <div className="result"><p><strong>{fmt(calculated.kcal)} kcal</strong> · Đạm {fmt(calculated.protein)} g · Bột đường {fmt(calculated.carb)} g · Béo {fmt(calculated.fat)} g</p><p>Nguồn: {chosen.source_reference}</p>{!chosen.is_verified && <p className="warn">Dữ liệu thử nghiệm, chưa được kiểm chứng.</p>}</div>}<button disabled={busy || !chosen} onClick={save}>Xác nhận và lưu nhật ký</button></div></section>}
    {tab==='dashboard' && <section className="card"><h2>Nhật ký hôm nay</h2><div className="metric">{fmt(dashboard?.totals.kcal)} <span>kcal</span></div><p>Đạm {fmt(dashboard?.totals.protein)} g · Bột đường {fmt(dashboard?.totals.carb)} g · Béo {fmt(dashboard?.totals.fat)} g</p>{dashboard?.entries.length ? dashboard.entries.map(x=><div className="entry" key={x.id}><strong>{x.name}</strong><span>{fmt(x.grams)} g · {fmt(x.nutrition.kcal)} kcal</span><small>{x.source_reference}</small></div>) : <p>Chưa có bữa ăn nào được ghi.</p>}</section>}
    {tab==='plan' && <section className="grid"><div className="card"><h2>Lập thực đơn tuần</h2><p>Chỉ dùng món trong danh mục. Hệ thống kiểm tra ID, thành phần cần tránh và tổng năng lượng.</p><label>Mục tiêu tham khảo (kcal/ngày)<input type="number" min="900" max="5000" value={target} onChange={e=>setTarget(e.target.value)}/></label><label>Thành phần cần tránh (tag, cách nhau bằng dấu phẩy)<input value={avoid} onChange={e=>setAvoid(e.target.value)} placeholder="shrimp, pork"/></label><button disabled={busy} onClick={generate}>Tạo thực đơn</button><p className="muted">Mục tiêu tự nhập chỉ phục vụ bản thử nghiệm; đây không phải chỉ định y khoa.</p></div><div className="card"><h2>Kết quả</h2>{plan ? <><p>Chế độ: {plan.generation_mode === 'gemini' ? 'Gemini + hậu kiểm' : 'Dự phòng theo quy tắc'}</p>{plan.days.map(day=><div className="day" key={day.day}><strong>Ngày {day.day} · {fmt(day.total_kcal)} kcal</strong>{day.meals.map(m=><p key={m.meal_slot}>{m.meal_slot}: {m.name}, {fmt(m.grams)} g</p>)}</div>)}<p className="warn">Kiểm tra nguồn dữ liệu từng món trước khi dùng ngoài bản demo.</p></> : <p>Chưa có thực đơn.</p>}</div></section>}
    {tab==='profile' && <section className="card"><h2>Hồ sơ thử nghiệm</h2><p>Thông tin lưu trên máy chạy backend. Chưa có tài khoản riêng cho nhiều người dùng.</p><div className="row"><label>Tuổi (từ 18)<input type="number" value={profile.age ?? ''} onChange={e=>setProfile({...profile,age:e.target.value})}/></label><label>Chiều cao (cm)<input type="number" value={profile.height_cm ?? ''} onChange={e=>setProfile({...profile,height_cm:e.target.value})}/></label></div><div className="row"><label>Cân nặng (kg)<input type="number" value={profile.weight_kg ?? ''} onChange={e=>setProfile({...profile,weight_kg:e.target.value})}/></label><label>Mục tiêu<select value={profile.goal} onChange={e=>setProfile({...profile,goal:e.target.value})}><option value="maintain">Duy trì</option><option value="gain">Tăng cân</option><option value="lose">Giảm cân</option></select></label></div><label>Mục tiêu năng lượng tự đặt (kcal/ngày)<input type="number" value={profile.target_kcal} onChange={e=>setProfile({...profile,target_kcal:e.target.value})}/></label><label>Thành phần cần tránh (tag, cách nhau bằng dấu phẩy)<input value={avoid} onChange={e=>setAvoid(e.target.value)}/></label><button disabled={busy} onClick={saveProfile}>Lưu hồ sơ</button><p className="muted">Ứng dụng không tự tính mục tiêu y khoa từ tuổi, chiều cao và cân nặng.</p></section>}
    <footer>Chỉ mang tính tham khảo. Dữ liệu demo được đánh dấu riêng; không dùng cho quyết định sức khỏe.</footer>
  </main>;
}

createRoot(document.getElementById('root')).render(<App/>);
