import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Bell, CalendarDays, ChevronDown, CircleUserRound, Dumbbell, House, Menu, UtensilsCrossed} from 'lucide-react';
import ScanSection from './ScanSection.jsx';
import TodayMeals from './TodayMeals.jsx';
import WorkoutPanel from './WorkoutPanel.jsx';
import WorkoutPlans from './WorkoutPlans.jsx';
import ProfilePanel from './ProfilePanel.jsx';
import './style.css';

const API=import.meta.env.VITE_API_URL||'http://localhost:8000';
function visitorId(){
  const key='hbtnfit_visitor_id';
  let value=localStorage.getItem(key);
  if(!value){value=crypto.randomUUID();localStorage.setItem(key,value);}
  return value;
}
async function call(path,options={}) {
  const headers=new Headers(options.headers||{});
  headers.set('X-Visitor-Id',visitorId());
  const response=await fetch(`${API}${path}`,{...options,headers});
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

function App() {
  const [section,setSection]=useState('home');
  const [foods,setFoods]=useState([]);
  const [dashboard,setDashboard]=useState(null);
  const [workouts,setWorkouts]=useState(null);
  const [plans,setPlans]=useState([]);
  const [profile,setProfile]=useState({age:null,height_cm:null,weight_kg:null,goal:'maintain',avoid_tags:[],target_kcal:1800});
  const [notice,setNotice]=useState('');
  const [showBell,setShowBell]=useState(false);
  const [navOpen,setNavOpen]=useState(false);

  async function refresh() {
    const [catalog,day,training]=await Promise.all([call('/api/foods'),call('/api/dashboard'),call('/api/workouts/today')]);
    setFoods(catalog);setDashboard(day);setWorkouts(training);
  }
  useEffect(()=>{
    Promise.all([refresh(),call('/api/profile').then(setProfile),call('/api/workouts/plans').then(setPlans)]).catch(error=>setNotice(error.message));
  },[]);
  function go(id){setSection(id);setNavOpen(false);setNotice('');}
  const dateLabel=new Intl.DateTimeFormat('vi-VN',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date());
  const title={home:'Tổng quan hôm nay',food:'Ăn uống',workout:'Tập luyện',profile:'Cá nhân'}[section];
  const subtitle={home:'Nhận diện món ăn và theo dõi thực đơn hôm nay.',food:'Nhận diện món ăn, xác nhận khẩu phần và theo dõi thực đơn.',workout:'Theo dõi ngày đi tập và tiếp tục đúng buổi kế tiếp của giáo án.',profile:'Cập nhật thông tin và mục tiêu cá nhân.'}[section];

  return <div className="app-shell">
    <header className="topbar"><div className="topbar-inner"><button className="menu-toggle" aria-label="Mở điều hướng" onClick={()=>setNavOpen(!navOpen)}><Menu size={22}/></button><button className="brand" onClick={()=>go('home')} aria-label="Về trang chủ HBTNFIT"><span className="brand-logo-frame"><img className="brand-logo" src="/Logo_HUET.svg" alt="Logo Đại học Công nghệ"/></span><span className="brand-words"><span className="brand-name">HBTNFIT</span><span className="brand-school">ĐẠI HỌC CÔNG NGHỆ</span></span></button><span className="topbar-caption">Sống khỏe theo cách của bạn</span><div className="top-actions"><div className="notification-wrap"><button className="header-icon" aria-label="Thông báo" aria-expanded={showBell} onClick={()=>setShowBell(!showBell)}><Bell size={19}/></button>{showBell&&<div className="notification-popover">Chưa có thông báo mới.</div>}</div><button className="account-button" onClick={()=>go('profile')}><span className="avatar">U</span><span>Tài khoản demo</span><ChevronDown size={15}/></button></div></div></header>
    <div className="body-layout"><aside className={`sidebar ${navOpen?'open':''}`}><div className="sidebar-group"><span className="sidebar-label">ĐIỀU HƯỚNG</span><nav aria-label="Điều hướng chính">{navigation.map(item=>{const Icon=item.icon;return <button key={item.id} className={`nav-item ${section===item.id?'active':''}`} onClick={()=>go(item.id)} title={item.label}><Icon size={19}/><span>{item.label}</span></button>;})}</nav></div><div className="sidebar-bottom"><div className="sidebar-note"><span className="status-dot"/> Bản dùng thử Track 1</div><small>HBTNFIT · 2026</small></div></aside>
      <main className="content"><div className="page-intro"><div><div className="date-line"><CalendarDays size={15}/>{dateLabel}</div><h1>{title}</h1><p>{subtitle}</p></div><span className="demo-badge">PHIÊN BẢN ĐẦU TIÊN</span></div>{notice&&<div className="global-notice" role="alert">{notice}<button aria-label="Đóng thông báo" onClick={()=>setNotice('')}>×</button></div>}
        {(section==='home'||section==='food')&&<div className="dashboard-grid"><div className="main-column"><ScanSection call={call} foods={foods} onAdded={refresh}/></div><div className="side-column"><TodayMeals dashboard={dashboard} profile={profile} onOpenProfile={()=>go('profile')} call={call} refresh={refresh} onError={setNotice}/></div></div>}
        {section==='workout'&&<div className="training-page">{workouts?.selected_plan&&<WorkoutPanel workouts={workouts} call={call} refresh={refresh} onError={setNotice}/>}<WorkoutPlans plans={plans} selectedId={workouts?.selected_plan?.id} call={call} refresh={refresh} onError={setNotice}/></div>}
        {section==='profile'&&<ProfilePanel profile={profile} setProfile={setProfile} call={call} onError={setNotice} refresh={refresh}/>}
        <footer className="app-footer">Thông tin dinh dưỡng và bài tập chỉ mang tính tham khảo. Dữ liệu món demo chưa được kiểm chứng.</footer>
      </main>
    </div>
  </div>;
}

createRoot(document.getElementById('root')).render(<App/>);
