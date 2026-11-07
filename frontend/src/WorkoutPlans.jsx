import React, {useState} from 'react';
import {Check, Dumbbell, Flame} from 'lucide-react';

const dayNames=['T2','T3','T4','T5','T6','T7','CN'];

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
    <div className="training-heading"><div><span className="section-kicker"><Dumbbell size={15}/> PHƯƠNG PHÁP TẬP</span><h2 id="plans-title">Chọn giáo án phù hợp</h2><p>PPL chia theo Push, Pull, Legs. Upper/Lower chia buổi thân trên và thân dưới. Chọn một giáo án để xem bài tập hôm nay.</p></div></div>
    {[["gain","Tăng cơ",Dumbbell],["lose","Giảm cân",Flame]].map(([goal,label,Icon])=><div className="plan-group" key={goal}><h3><Icon size={18}/>{label}</h3><div className="plan-grid">{plans.filter(plan=>plan.goal===goal).map(plan=><article className={`plan-card ${selectedId===plan.id?'selected':''}`} key={plan.id}><div className="plan-card-top"><span className="plan-method">{plan.method}</span>{selectedId===plan.id&&<span className="plan-selected"><Check size={14}/> Đang chọn</span>}</div><h4>{plan.name}</h4><p>{plan.description}</p><span className="plan-frequency">{plan.days_per_week} buổi / tuần</span><div className="week-strip">{plan.schedule.map((day,index)=><div key={index}><b>{dayNames[index]}</b><span>{day}</span></div>)}</div><button className={selectedId===plan.id?'selected-button':'primary-button'} disabled={!!busy||selectedId===plan.id} onClick={()=>choose(plan.id)}>{selectedId===plan.id?'Đã chọn giáo án':'Chọn giáo án này'}</button></article>)}</div></div>)}
    <p className="data-note">Giáo án mẫu để tham khảo. Điều chỉnh mức tạ, số lần và thời gian theo thể lực của bạn.</p>
  </section>;
}
