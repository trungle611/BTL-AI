import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Bell, CalendarDays, ChevronDown, CircleUserRound, Dumbbell, House, Menu, Settings2, UtensilsCrossed} from 'lucide-react';
import ScanSection from './ScanSection.jsx';
import TodayMeals from './TodayMeals.jsx';
import WorkoutPanel from './WorkoutPanel.jsx';
import './style.css';

const API=import.meta.env.VITE_API_URL||'http://localhost:8000';
async function call(path,options={}) {
  const response=await fetch(`${API}${path}`,options);
  const body=await response.json().catch(()=>({}));
  if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:`Lỗi ${response.status}`);
  return body;
}

const navigation=[
  {id:'home',label:'Trang chủ',icon:House},
  {id:'workout',label:'Tập luyện',icon:Dumbbell},
  {id:'food',label:'Ăn uống',icon:UtensilsCrossed},
  {id:'profile',label:'Cá nhân',icon:CircleUserRound},
];

function ProfilePanel({profile,setProfile,call,onError}) {
  const [busy,setBusy]=useState(false);
  const [saved,setSaved]=useState(false);
  const [avoid,setAvoid]=useState((profile.avoid_tags||[]).join(', '));
  useEffect(()=>setAvoid((profile.avoid_tags||[]).join(', ')),[profile.avoid_tags]);
  async function save() {
    setBusy(true);setSaved(false);
    try {
      const body={...profile,age:profile.age===''?null:Number(profile.age),height_cm:profile.height_cm===''?null:Number(profile.height_cm),weight_kg:profile.weight_kg===''?null:Number(profile.weight_kg),target_kcal:Number(profile.target_kcal),avoid_tags:avoid.split(',').map(s=>s.trim()).filter(Boolean)};
      const result=await call('/api/profile',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      setProfile(result);setSaved(true);
    } catch(error){onError(error.message);} finally{setBusy(false);}
  }
  return <section className="panel profile-panel"><div className="panel-heading"><div><div className="section-kicker"><Settings2 size={15}/> THÔNG TIN CÁ NHÂN</div><h2>Hồ sơ của bạn</h2></div></div><p className="panel-lead">Dùng hồ sơ để lưu mục tiêu và thành phần muốn tránh. Bản demo hiện chỉ có một hồ sơ trên máy này.</p><div className="profile-grid"><label>Tuổi<input type="number" min="18" max="120" value={profile.age??''} onChange={e=>setProfile({...profile,age:e.target.value})} placeholder="Ví dụ 22"/></label><label>Chiều cao (cm)<input type="number" min="100" max="250" value={profile.height_cm??''} onChange={e=>setProfile({...profile,height_cm:e.target.value})} placeholder="Ví dụ 170"/></label><label>Cân nặng (kg)<input type="number" min="25" max="400" value={profile.weight_kg??''} onChange={e=>setProfile({...profile,weight_kg:e.target.value})} placeholder="Ví dụ 65"/></label><label>Mục tiêu<select value={profile.goal||'maintain'} onChange={e=>setProfile({...profile,goal:e.target.value})}><option value="maintain">Duy trì</option><option value="gain">Tăng cân</option><option value="lose">Giảm cân</option></select></label><label>Mục tiêu năng lượng tham khảo (kcal/ngày)<input type="number" min="900" max="5000" value={profile.target_kcal??1800} onChange={e=>setProfile({...profile,target_kcal:e.target.value})}/></label><label>Thành phần cần tránh<input value={avoid} onChange={e=>setAvoid(e.target.value)} placeholder="shrimp, pork"/></label></div><div className="profile-footer"><button className="primary-button" disabled={busy} onClick={save}>Lưu hồ sơ</button>{saved&&<span className="saved-message">Đã lưu thay đổi.</span>}</div><p className="data-note">Mục tiêu tự nhập chỉ để tham khảo, không thay thế tư vấn y khoa.</p></section>;
}

function App() {
  const [section,setSection]=useState('home');
  const [foods,setFoods]=useState([]);
  const [dashboard,setDashboard]=useState(null);
  const [workouts,setWorkouts]=useState(null);
  const [profile,setProfile]=useState({age:null,height_cm:null,weight_kg:null,goal:'maintain',avoid_tags:[],target_kcal:1800});
  const [notice,setNotice]=useState('');
  const [showBell,setShowBell]=useState(false);
  const [navOpen,setNavOpen]=useState(false);

  async function refresh() {
    const [catalog,day,training]=await Promise.all([call('/api/foods'),call('/api/dashboard'),call('/api/workouts/today')]);
    setFoods(catalog);setDashboard(day);setWorkouts(training);
  }
  useEffect(()=>{
    Promise.all([refresh(),call('/api/profile').then(setProfile)]).catch(error=>setNotice(error.message));
  },[]);
  function go(id){setSection(id);setNavOpen(false);setNotice('');}
  const dateLabel=new Intl.DateTimeFormat('vi-VN',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date());
  const title={home:'Tổng quan hôm nay',food:'Ăn uống',workout:'Tập luyện',profile:'Cá nhân'}[section];
  const subtitle={home:'Theo dõi bữa ăn và kế hoạch tập luyện của bạn trong một nơi.',food:'Nhận diện món ăn, xác nhận khẩu phần và theo dõi thực đơn.',workout:'Xem kế hoạch hôm nay và đánh dấu tiến độ từng bài tập.',profile:'Cập nhật thông tin và mục tiêu cá nhân.'}[section];

  return <div className="app-shell">
    <header className="topbar"><div className="topbar-inner"><button className="menu-toggle" aria-label="Mở điều hướng" onClick={()=>setNavOpen(!navOpen)}><Menu size={22}/></button><button className="brand" onClick={()=>go('home')} aria-label="Về trang chủ HBTNFIT"><span className="brand-mark">H<span>+</span></span><span className="brand-name">HBTNFIT</span></button><span className="topbar-caption">Sống khỏe theo cách của bạn</span><div className="top-actions"><div className="notification-wrap"><button className="header-icon" aria-label="Thông báo" aria-expanded={showBell} onClick={()=>setShowBell(!showBell)}><Bell size={19}/></button>{showBell&&<div className="notification-popover">Chưa có thông báo mới.</div>}</div><button className="account-button" onClick={()=>go('profile')}><span className="avatar">U</span><span>Tài khoản demo</span><ChevronDown size={15}/></button></div></div></header>
    <div className="body-layout"><aside className={`sidebar ${navOpen?'open':''}`}><div className="sidebar-group"><span className="sidebar-label">ĐIỀU HƯỚNG</span><nav aria-label="Điều hướng chính">{navigation.map(item=>{const Icon=item.icon;return <button key={item.id} className={`nav-item ${section===item.id?'active':''}`} onClick={()=>go(item.id)} title={item.label}><Icon size={19}/><span>{item.label}</span></button>;})}</nav></div><div className="sidebar-bottom"><div className="sidebar-note"><span className="status-dot"/> Bản dùng thử Track 1</div><small>HBTNFIT · 2026</small></div></aside>
      <main className="content"><div className="page-intro"><div><div className="date-line"><CalendarDays size={15}/>{dateLabel}</div><h1>{title}</h1><p>{subtitle}</p></div><span className="demo-badge">PHIÊN BẢN ĐẦU TIÊN</span></div>{notice&&<div className="global-notice" role="alert">{notice}<button aria-label="Đóng thông báo" onClick={()=>setNotice('')}>×</button></div>}
        {(section==='home'||section==='food')&&<div className="dashboard-grid"><div className="main-column"><ScanSection call={call} foods={foods} onAdded={refresh}/></div><div className="side-column"><TodayMeals dashboard={dashboard} call={call} refresh={refresh} onError={setNotice}/><WorkoutPanel workouts={workouts} call={call} refresh={refresh} onError={setNotice} compact/></div></div>}
        {section==='workout'&&<div className="single-column"><WorkoutPanel workouts={workouts} call={call} refresh={refresh} onError={setNotice}/></div>}
        {section==='profile'&&<div className="single-column"><ProfilePanel profile={profile} setProfile={setProfile} call={call} onError={setNotice}/></div>}
        <footer className="app-footer">Thông tin dinh dưỡng và bài tập chỉ mang tính tham khảo. Dữ liệu món demo chưa được kiểm chứng.</footer>
      </main>
    </div>
  </div>;
}

createRoot(document.getElementById('root')).render(<App/>);
