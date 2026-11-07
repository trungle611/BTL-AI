import React, {useState} from 'react';
import {Check, Dumbbell, Flame} from 'lucide-react';

export default function WorkoutPlans({plans,selectedId,call,refresh,onError}) {
  const [busy,setBusy]=useState('');
  async function choose(id) {
    setBusy(id);
    try {
      await call('/api/workouts/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan_id:id})});
      await refresh();
    } catch(error) {onError(error.message);} finally {setBusy('');}
  }
  return <section className="training-plans" aria-labelledby="plans-title">
    <div className="training-heading"><div><span className="section-kicker"><Dumbbell size={15}/> PHƯƠNG PHÁP TẬP</span><h2 id="plans-title">{selectedId?'Đổi giáo án':'Chọn giáo án phù hợp'}</h2><p>PPL chia theo Push, Pull, Legs. Upper/Lower chia thân trên và thân dưới. Các buổi chạy theo tiến độ của bạn, không gắn vào thứ cố định.</p></div></div>
    {[["gain","Tăng cơ",Dumbbell],["lose","Giảm cân",Flame]].map(([goal,label,Icon])=><div className="plan-group" key={goal}>
      <h3><Icon size={18}/>{label}</h3>
      <div className="plan-grid">{plans.filter(plan=>plan.goal===goal).map(plan=><article className={`plan-card ${selectedId===plan.id?'selected':''}`} key={plan.id}>
        <div className="plan-card-top"><span className="plan-method">{plan.method}</span>{selectedId===plan.id&&<span className="plan-selected"><Check size={14}/> Đang chọn</span>}</div>
        <h4>{plan.name}</h4><p>{plan.description}</p><span className="plan-frequency">{plan.sessions_per_cycle} buổi / chu kỳ</span>
        <div className="week-strip" style={{gridTemplateColumns:`repeat(${plan.schedule.length},minmax(0,1fr))`}}>{plan.schedule.map((day,index)=><div key={index}><b>Buổi {index+1}</b><span>{day}</span></div>)}</div>
        <details className="plan-exercises"><summary>Xem bài tập từng buổi</summary><div className="plan-exercise-cycle">{plan.session_exercises?.map((session,index)=><div className="plan-session" key={index}>
          <strong>Buổi {index+1} · {plan.schedule[index]}</strong><ul>{session.map((item,itemIndex)=><li key={itemIndex}><span>{item.name}</span><small>{item.focus}{item.sets?` · ${item.sets} hiệp × ${item.reps}`:''}</small></li>)}</ul>
        </div>)}</div></details>
        <button className={selectedId===plan.id?'selected-button':'primary-button'} disabled={!!busy||selectedId===plan.id} onClick={()=>choose(plan.id)}>{selectedId===plan.id?'Đã chọn giáo án':'Chọn giáo án này'}</button>
      </article>)}</div>
    </div>)}
    <p className="data-note">Giáo án mẫu để tham khảo. Điều chỉnh mức tạ, số lần và thời gian theo thể lực của bạn.</p>
  </section>;
}
