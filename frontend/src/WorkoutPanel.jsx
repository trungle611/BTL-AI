import React, {useState} from 'react';
import {Activity, Check, ChevronDown, ChevronUp, CirclePlay, Clock3, Dumbbell} from 'lucide-react';

const statusText={not_started:'Chưa bắt đầu',started:'Đang tập',completed:'Hoàn thành'};
const attendanceText={attended:'Có đi tập',missed:'Bỏ lỡ',completed:'Hoàn thành'};

export default function WorkoutPanel({workouts,call,refresh,onError}) {
  const [expanded,setExpanded]=useState(null);
  const [busyId,setBusyId]=useState(null);
  const items=workouts?.items||[];
  const completed=items.filter(item=>item.status==='completed').length;
  const minutes=items.reduce((sum,item)=>sum+item.duration_minutes,0);
  const attendance=workouts?.attendance;
  const canTrain=attendance==='attended';

  async function act(item,action) {
    setBusyId(item.id);
    try {await call(`/api/workouts/${item.id}/${action}`,{method:'POST'});await refresh();}
    catch(error){onError(error.message);} finally{setBusyId(null);}
  }
  async function checkIn(status) {
    setBusyId('attendance');
    try {await call('/api/workouts/attendance',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});await refresh();}
    catch(error){onError(error.message);} finally{setBusyId(null);}
  }

  return <section className="panel workout-panel" aria-labelledby="workout-title">
    <div className="panel-heading"><div><div className="section-kicker"><Activity size={15}/> BUỔI TẬP KẾ TIẾP</div><h2 id="workout-title">{workouts?.session_name} · Buổi {workouts?.session_number}</h2><p className="session-plan">{workouts?.selected_plan?.name} · {workouts?.selected_plan?.sessions_per_cycle} buổi / chu kỳ</p></div><span className="count-pill">{completed}/{items.length} bài xong</span></div>
    <p className="panel-lead">Tập theo thứ tự buổi, không theo thứ trong tuần. Bỏ lỡ hôm nay thì lần sau vẫn là buổi này. Hoàn thành tất cả bài để chuyển sang buổi kế tiếp.</p>
    <div className="attendance-box"><div><strong>Hôm nay bạn có đi tập không?</strong><span>{attendance?`Đã ghi nhận: ${attendanceText[attendance]}`:'Chưa ghi nhận hôm nay'}</span></div>{attendance!=='completed'&&<div className="attendance-actions"><button className="primary-button" disabled={busyId==='attendance'||attendance==='attended'} onClick={()=>checkIn('attended')}><Check size={16}/> Có đi tập</button><button className="missed-button" disabled={busyId==='attendance'||attendance==='missed'} onClick={()=>checkIn('missed')}>Bỏ lỡ hôm nay</button></div>}</div>
    <div className="attendance-history"><strong>7 ngày gần đây</strong><div className="history-grid">{(workouts?.attendance_history||[]).map(entry=><div className={`history-day ${entry.status||'unmarked'}`} key={entry.day}><span>{new Intl.DateTimeFormat('vi-VN',{weekday:'short',timeZone:'UTC'}).format(new Date(`${entry.day}T12:00:00Z`))}</span><b>{entry.day.slice(8)}</b><small>{attendanceText[entry.status]||'Chưa ghi'}</small></div>)}</div><p>“Chưa ghi” không được tính là bỏ lỡ.</p></div>
    <div className="workout-overview"><span><Clock3 size={16}/> Khoảng {minutes} phút</span><span><Dumbbell size={16}/> {items.length} bài tập</span></div>
    {attendance==='missed'&&<p className="missed-note">Buổi này được giữ lại cho lần đi tập tiếp theo. Bạn vẫn có thể sửa ghi nhận hôm nay.</p>}
    <div className="workout-list">{items.map((item,index)=><article className={`workout-item ${item.status==='completed'?'is-complete':''}`} key={item.id}>
      <div className="workout-row"><div className="workout-number">{String(index+1).padStart(2,'0')}</div><div className="workout-copy"><strong>{item.name}</strong><span>{item.category} · {item.duration_minutes} phút{item.sets?` · ${item.sets} hiệp${item.reps?` × ${item.reps}`:''}`:''}</span></div><span className={`status-tag ${item.status}`}>{item.status==='completed'&&<Check size={13}/>} {statusText[item.status]}</span></div>
      <div className="workout-actions"><button className="link-button" onClick={()=>setExpanded(expanded===item.id?null:item.id)}>{expanded===item.id?'Ẩn chi tiết':'Xem chi tiết'} {expanded===item.id?<ChevronUp size={15}/>:<ChevronDown size={15}/>}</button>{canTrain&&item.status==='not_started'&&<button className="small-action" disabled={busyId===item.id} onClick={()=>act(item,'start')}><CirclePlay size={15}/> Bắt đầu tập</button>}{canTrain&&item.status==='started'&&<button className="small-action" disabled={busyId===item.id} onClick={()=>act(item,'complete')}><Check size={15}/> Hoàn thành</button>}</div>
      {expanded===item.id&&<div className="workout-detail"><p>{item.detail}</p>{item.steps?.length>0&&<ol className="exercise-steps">{item.steps.map((step,index)=><li key={index}>{step}</li>)}</ol>}{item.rest_seconds>0&&<p className="rest-note">Nghỉ khoảng {item.rest_seconds} giây giữa các hiệp.</p>}{canTrain&&item.status==='not_started'&&<button className="primary-button" disabled={busyId===item.id} onClick={()=>act(item,'start')}><CirclePlay size={17}/> Bắt đầu tập</button>}{canTrain&&item.status==='started'&&<button className="primary-button" disabled={busyId===item.id} onClick={()=>act(item,'complete')}><Check size={17}/> Hoàn thành bài tập</button>}{item.status==='completed'&&<p className="done-copy"><Check size={16}/> Bạn đã hoàn thành bài này hôm nay.</p>}{!canTrain&&item.status!=='completed'&&<p>Ghi nhận có đi tập để bắt đầu bài này.</p>}</div>}
    </article>)}</div>
    <p className="data-note">Giáo án mẫu để tham khảo; dừng lại nếu đau hoặc không thoải mái.</p>
  </section>;
}
