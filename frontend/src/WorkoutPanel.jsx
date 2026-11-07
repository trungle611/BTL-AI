import React, {useState} from 'react';
import {Activity, Check, ChevronDown, ChevronUp, CirclePlay, Clock3, Dumbbell} from 'lucide-react';

const statusText = {not_started:'Chưa bắt đầu',started:'Đang tập',completed:'Hoàn thành'};

export default function WorkoutPanel({workouts, call, refresh, onError, compact = false}) {
  const [expanded, setExpanded] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const items = workouts?.items || [];
  const completed = items.filter(item => item.status === 'completed').length;
  const minutes = items.reduce((sum,item)=>sum + item.duration_minutes,0);

  async function act(item, action) {
    setBusyId(item.id);
    try {await call(`/api/workouts/${item.id}/${action}`,{method:'POST'});await refresh();}
    catch(error) {onError(error.message);} finally {setBusyId(null);}
  }

  return <section className="panel workout-panel" aria-labelledby="workout-title">
    <div className="panel-heading"><div><div className="section-kicker"><Activity size={15}/> KẾ HOẠCH TẬP LUYỆN</div><h2 id="workout-title">Bài tập hôm nay</h2></div><span className="count-pill">{completed}/{items.length} xong</span></div>
    <div className="workout-overview"><span><Clock3 size={16}/> Khoảng {minutes} phút</span><span><Dumbbell size={16}/> {items.length} bài tập</span></div>
    {items.length === 0 && <div className="empty-state"><Dumbbell size={24}/><strong>Chưa tải được kế hoạch tập</strong></div>}
    <div className="workout-list">{items.map((item,index)=><article className={`workout-item ${item.status === 'completed' ? 'is-complete' : ''}`} key={item.id}>
      <div className="workout-row"><div className="workout-number">{String(index+1).padStart(2,'0')}</div><div className="workout-copy"><strong>{item.name}</strong><span>{item.category} · {item.duration_minutes} phút{item.sets ? ` · ${item.sets} hiệp${item.reps ? ` × ${item.reps}` : ''}` : ''}</span></div><span className={`status-tag ${item.status}`}>{item.status === 'completed' && <Check size={13}/>} {statusText[item.status]}</span></div>
      <div className="workout-actions"><button className="link-button" onClick={()=>setExpanded(expanded===item.id?null:item.id)}>{expanded===item.id?'Ẩn chi tiết':'Xem chi tiết'} {expanded===item.id?<ChevronUp size={15}/>:<ChevronDown size={15}/>}</button>{item.status === 'not_started' && <button className="small-action" disabled={busyId===item.id} onClick={()=>act(item,'start')}><CirclePlay size={15}/> Bắt đầu tập</button>}{item.status === 'started' && <button className="small-action" disabled={busyId===item.id} onClick={()=>act(item,'complete')}><Check size={15}/> Đánh dấu hoàn thành</button>}</div>
      {expanded===item.id && <div className="workout-detail"><p>{item.detail}</p>{item.status === 'not_started' && <button className="primary-button" disabled={busyId===item.id} onClick={()=>act(item,'start')}><CirclePlay size={17}/> Bắt đầu tập</button>}{item.status === 'started' && <button className="primary-button" disabled={busyId===item.id} onClick={()=>act(item,'complete')}><Check size={17}/> Hoàn thành bài tập</button>}{item.status === 'completed' && <p className="done-copy"><Check size={16}/> Bạn đã hoàn thành bài này hôm nay.</p>}</div>}
    </article>)}</div>
    {!compact && <p className="data-note">Lịch tập cơ bản để tham khảo; dừng lại nếu thấy đau hoặc không thoải mái.</p>}
  </section>;
}
