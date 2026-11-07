import React,{useEffect,useState} from 'react';
import {Check, Sparkles, Settings2} from 'lucide-react';

export default function ProfilePanel({profile,setProfile,call,onError,refresh,onOpenFood}) {
  const [busy,setBusy]=useState('');
  const [saved,setSaved]=useState(false);
  const [avoid,setAvoid]=useState((profile.avoid_tags||[]).join(', '));
  const updateProfile=(key,value)=>setProfile(current=>({...current,[key]:value}));
  useEffect(()=>setAvoid((profile.avoid_tags||[]).join(', ')),[profile.avoid_tags]);

  async function saveProfile() {
    const body={...profile,
      age:profile.age==null||profile.age===''?null:Number(profile.age),
      height_cm:profile.height_cm==null||profile.height_cm===''?null:Number(profile.height_cm),
      weight_kg:profile.weight_kg==null||profile.weight_kg===''?null:Number(profile.weight_kg),
      target_weight_kg:profile.target_weight_kg==null||profile.target_weight_kg===''?null:Number(profile.target_weight_kg),
      target_date:profile.target_date||null,
      target_kcal:Number(profile.target_kcal),
      avoid_tags:avoid.split(',').map(value=>value.trim()).filter(Boolean)};
    const result=await call('/api/profile',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    setProfile(result);setSaved(true);
    return result;
  }
  async function save() {
    setBusy('save');setSaved(false);
    try {await saveProfile();} catch(error){onError(error.message);} finally{setBusy('');}
  }
  async function analyze() {
    setBusy('analyze');setSaved(false);
    try {
      const stored=await saveProfile();
      if(!stored.weight_kg||!stored.target_weight_kg){onError('Hãy nhập cân nặng hiện tại và mong muốn.');return;}
      setProfile(await call('/api/profile/analyze',{method:'POST'}));
    } catch(error){onError(error.message);} finally{setBusy('');}
  }
  async function choose(field,id) {
    setBusy(id);
    try {
      const result=await call('/api/profile/choice',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({[field]:id})});
      setProfile(result);
      if(field==='workout_choice')await refresh();
      if(field==='food_choice')onOpenFood();
    } catch(error){onError(error.message);} finally{setBusy('');}
  }

  return <div className="profile-page"><section className="panel profile-panel"><div className="panel-heading"><div><div className="section-kicker"><Settings2 size={15}/> THÔNG TIN CÁ NHÂN</div><h2>Hồ sơ của bạn</h2></div></div><p className="panel-lead">Nhập cân nặng hiện tại và mong muốn để nhận các phương án tham khảo. Mỗi trình duyệt có phiên test riêng; chưa có tài khoản đăng nhập.</p>
    <div className="profile-grid"><label>Tuổi<input type="number" min="18" max="120" value={profile.age??''} onChange={e=>updateProfile('age',e.target.value)} placeholder="Ví dụ 22"/></label><label>Chiều cao (cm)<input type="number" min="100" max="250" value={profile.height_cm??''} onChange={e=>updateProfile('height_cm',e.target.value)} placeholder="Ví dụ 170"/></label><label>Cân nặng hiện tại (kg)<input type="number" min="25" max="400" step="0.1" value={profile.weight_kg??''} onChange={e=>updateProfile('weight_kg',e.target.value)} placeholder="Ví dụ 65"/></label><label>Cân nặng mong muốn (kg)<input type="number" min="25" max="400" step="0.1" value={profile.target_weight_kg??''} onChange={e=>updateProfile('target_weight_kg',e.target.value)} placeholder="Ví dụ 70"/></label><label>Muốn đạt mục tiêu trước ngày<input type="date" value={profile.target_date??''} onInput={e=>updateProfile('target_date',e.target.value)} onChange={e=>updateProfile('target_date',e.target.value)}/></label><label>Mục tiêu<select value={profile.goal||'maintain'} onChange={e=>updateProfile('goal',e.target.value)}><option value="maintain">Duy trì</option><option value="gain">Tăng cân</option><option value="lose">Giảm cân</option></select></label><label>Thông số sinh học để ước tính năng lượng<select value={profile.sex??''} onChange={e=>updateProfile('sex',e.target.value||null)}><option value="">Chọn nếu muốn tính mục tiêu</option><option value="female">Nữ</option><option value="male">Nam</option></select></label><label>Mức vận động hiện tại<select value={profile.activity_level??''} onChange={e=>updateProfile('activity_level',e.target.value||null)}><option value="">Chọn mức vận động</option><option value="sedentary">Ít vận động</option><option value="light">Nhẹ · 1–3 buổi/tuần</option><option value="moderate">Vừa · 3–5 buổi/tuần</option><option value="high">Nhiều · 6–7 buổi/tuần</option></select></label><label>Mức protein muốn theo dõi<select value={profile.protein_mode||'balanced'} onChange={e=>updateProfile('protein_mode',e.target.value)}><option value="balanced">Cân bằng · khoảng 1,2 g/kg</option><option value="strength">Tập kháng lực đều · khoảng 1,6 g/kg</option></select></label><label>Thành phần cần tránh<input value={avoid} onChange={e=>setAvoid(e.target.value)} placeholder="Ví dụ: tôm, thịt heo"/></label></div>
    {profile.daily_targets&&<div className="goal-estimate"><div><strong>{profile.daily_targets.kcal.toLocaleString('vi-VN')} kcal</strong><span>Mỗi ngày</span></div><div><strong>{profile.daily_targets.protein_g} g</strong><span>Protein</span></div><div><strong>{profile.daily_targets.carb_g??'–'} g</strong><span>Carb</span></div><div><strong>{profile.daily_targets.fat_g??'–'} g</strong><span>Chất béo</span></div><div><strong>{profile.daily_targets.days_remaining} ngày</strong><span>Đến thời hạn đã chọn</span></div></div>}
    {profile.daily_targets&&<p className="data-note">Protein: {profile.weight_kg} kg × {profile.daily_targets.protein_factor} g/kg ≈ {profile.daily_targets.protein_g} g/ngày. Mức này theo cách tập bạn chọn, không tăng theo số kg muốn đạt.</p>}
    {profile.daily_targets?.timeline_warning&&<p className="goal-warning">Thời hạn này có thể quá gấp. Mức ăn gợi ý đã được giới hạn; không đảm bảo đạt đúng cân nặng vào ngày chọn.</p>}
    {profile.daily_targets?.macro_distribution_warning&&<p className="goal-warning">Mức kcal và protein đã chọn khiến tỷ lệ carb thấp hơn khoảng tham khảo. Hãy xem lại mục tiêu hoặc trao đổi với chuyên gia dinh dưỡng.</p>}
    <div className="profile-footer"><button className="primary-button" disabled={!!busy} onClick={save}>Lưu và tính mục tiêu</button><button className="secondary-button" disabled={!!busy} onClick={analyze}><Sparkles size={16}/>{busy==='analyze'?'Đang phân tích…':'AI gợi ý ăn uống & tập luyện'}</button>{saved&&<span className="saved-message">Đã lưu hồ sơ.</span>}</div><p className="data-note">Điền đủ tuổi, chiều cao, hai mức cân nặng, thời hạn, thông số sinh học và mức vận động để tính. Kcal và protein là ước tính tham khảo, không thay thế tư vấn chuyên môn.</p>
  </section>
  {profile.analysis&&<section className="panel guidance-panel"><div className="section-kicker"><Sparkles size={15}/> GỢI Ý TỪ GEMINI</div><h2>Phương án cho mục tiêu của bạn</h2><p className="panel-lead">{profile.analysis.summary}</p><h3>Ăn uống</h3><div className="guidance-grid">{profile.analysis.food_options?.map(option=><article className={`guidance-card ${profile.food_choice===option.id?'selected':''}`} key={option.id}><h4>{option.title}</h4><p>{option.detail}</p><ul>{option.examples?.map((example,index)=><li key={index}>{example}</li>)}</ul><button className="secondary-button" disabled={!!busy||profile.food_choice===option.id} onClick={()=>choose('food_choice',option.id)}>{profile.food_choice===option.id?<><Check size={15}/> Đã chọn</>:'Chọn cách ăn này'}</button></article>)}</div><h3>Tập luyện</h3><div className="guidance-grid">{profile.analysis.workout_options?.map(option=><article className={`guidance-card ${profile.workout_choice===option.id?'selected':''}`} key={option.id}><h4>{option.name}</h4><p>{option.detail}</p><button className="secondary-button" disabled={!!busy||profile.workout_choice===option.id} onClick={()=>choose('workout_choice',option.id)}>{profile.workout_choice===option.id?<><Check size={15}/> Đã chọn</>:'Chọn giáo án này'}</button></article>)}</div><p className="data-note">Gợi ý được tạo bằng {profile.analysis.model}; hãy tự kiểm tra món ăn và điều chỉnh bài tập theo thể lực.</p></section>}
  </div>;
}
