import React, {useState} from 'react';
import {CalendarDays, Pencil, Trash2, Check, X, UtensilsCrossed} from 'lucide-react';

const labels = {breakfast:'Bữa sáng',lunch:'Bữa trưa',dinner:'Bữa tối',snack:'Bữa phụ'};
const slots = ['breakfast','lunch','dinner','snack'];
const fmt = value => Number(value || 0).toLocaleString('vi-VN',{maximumFractionDigits:1});

export default function TodayMeals({dashboard, profile, onOpenProfile, call, refresh, onError, compact = false}) {
  const [editing, setEditing] = useState(null);
  const [grams, setGrams] = useState('');
  const [mealType, setMealType] = useState('lunch');
  const [busy, setBusy] = useState(false);
  const entries = dashboard?.entries || [];
  const totals = dashboard?.totals || {};
  const target = profile?.daily_targets;
  const kcalProgress = target ? Math.min(100, Math.round((totals.kcal || 0) / target.kcal * 100)) : 0;
  const proteinProgress = target ? Math.min(100, Math.round((totals.protein || 0) / target.protein_g * 100)) : 0;

  function beginEdit(entry) {setEditing(entry.id);setGrams(String(entry.grams));setMealType(entry.meal_type);}
  async function saveEdit(id) {
    const value = Number(grams);
    if (!Number.isFinite(value) || value <= 0 || value > 2000) {onError('Khẩu phần phải từ 1 đến 2000 g.');return;}
    setBusy(true);
    try {
      await call(`/api/food-logs/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({grams:value,meal_type:mealType})});
      setEditing(null);await refresh();
    } catch(error) {onError(error.message);} finally {setBusy(false);}
  }
  async function remove(id) {
    setBusy(true);
    try {await call(`/api/food-logs/${id}`,{method:'DELETE'});await refresh();}
    catch(error) {onError(error.message);} finally {setBusy(false);}
  }

  return <section className="panel today-panel" aria-labelledby="today-meals-title">
    <div className="panel-heading"><div><div className="section-kicker"><CalendarDays size={15}/> DINH DƯỠNG HÔM NAY</div><h2 id="today-meals-title">Thực đơn hôm nay</h2></div><span className="count-pill">{entries.length} món</span></div>
    {target ? <div className="daily-goal"><div className="daily-goal-top"><strong>Mục tiêu theo cân nặng của bạn</strong><button className="link-button" onClick={onOpenProfile}>Sửa mục tiêu</button></div><div className="goal-progress"><div><span>Kcal</span><b>{fmt(totals.kcal)} / {fmt(target.kcal)}</b></div><progress value={kcalProgress} max="100" aria-label="Tiến độ kcal hôm nay"/></div><div className="goal-progress"><div><span>Protein</span><b>{fmt(totals.protein)} / {fmt(target.protein_g)} g</b></div><progress value={proteinProgress} max="100" aria-label="Tiến độ protein hôm nay"/></div><small>{profile.target_date && `Thời hạn mong muốn: ${new Date(`${profile.target_date}T12:00:00`).toLocaleDateString('vi-VN')}. `}Số liệu món chỉ được cộng sau khi xác nhận.</small></div> : <div className="daily-goal daily-goal-empty"><span>Chưa có mục tiêu kcal và protein mỗi ngày.</span><button className="link-button" onClick={onOpenProfile}>Thiết lập trong Cá nhân →</button></div>}
    <div className="nutrition-summary">
      <div className="calorie-total"><strong>{fmt(totals.kcal)}</strong><span>kcal đã thêm</span></div>
      <div className="macro-grid"><div><b>{fmt(totals.protein)}g</b><span>Protein</span></div><div><b>{fmt(totals.carb)}g</b><span>Carb</span></div><div><b>{fmt(totals.fat)}g</b><span>Chất béo</span></div></div>
    </div>
    {entries.length === 0 && <div className="empty-state"><UtensilsCrossed size={24}/><strong>Chưa có món nào</strong><p>Món chỉ được cộng vào đây sau khi bạn xác nhận thêm.</p></div>}
    {slots.map(slot => {
      const meals = entries.filter(entry => entry.meal_type === slot);
      if (!meals.length) return null;
      return <div className="meal-group" key={slot}><h3>{labels[slot]}</h3>{meals.map(entry => <div className="meal-entry" key={entry.id}>
        {editing === entry.id ? <div className="meal-edit"><strong>{entry.name}</strong><div className="edit-row"><label>Khẩu phần (g)<input type="number" min="1" max="2000" value={grams} onChange={e=>setGrams(e.target.value)}/></label><label>Bữa ăn<select value={mealType} onChange={e=>setMealType(e.target.value)}>{slots.map(value=><option value={value} key={value}>{labels[value]}</option>)}</select></label></div><div className="entry-actions"><button className="icon-button" aria-label="Lưu chỉnh sửa" disabled={busy} onClick={()=>saveEdit(entry.id)}><Check size={17}/></button><button className="icon-button" aria-label="Hủy chỉnh sửa" onClick={()=>setEditing(null)}><X size={17}/></button></div></div> : <><div className="meal-icon"><UtensilsCrossed size={17}/></div><div className="meal-copy"><strong>{entry.name}</strong><span>{fmt(entry.grams)} g · {fmt(entry.nutrition.kcal)} kcal</span></div><div className="entry-actions"><button className="icon-button" aria-label={`Sửa ${entry.name}`} onClick={()=>beginEdit(entry)}><Pencil size={16}/></button><button className="icon-button danger" aria-label={`Xóa ${entry.name}`} disabled={busy} onClick={()=>remove(entry.id)}><Trash2 size={16}/></button></div></>}
      </div>)}</div>;
    })}
    {!compact && entries.some(entry => entry.source_reference?.startsWith('Người dùng tự nhập')) && <p className="data-note">Món tự nhập có thể thiếu dinh dưỡng (hiển thị 0 khi chưa có số liệu); tổng hôm nay chưa phản ánh đầy đủ.</p>}
    {!compact && entries.some(entry => !entry.is_verified && !entry.source_reference?.startsWith('Người dùng tự nhập')) && <p className="data-note">Số liệu demo chưa được kiểm chứng; chỉ dùng để thử giao diện.</p>}
  </section>;
}
