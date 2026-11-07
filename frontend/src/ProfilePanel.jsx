import React,{useEffect,useState} from 'react';
import {Check, Sparkles, Settings2} from 'lucide-react';

export default function ProfilePanel({profile,setProfile,call,onError,refresh}) {
  const [busy,setBusy]=useState('');
  const [saved,setSaved]=useState(false);
  const [avoid,setAvoid]=useState((profile.avoid_tags||[]).join(', '));
  useEffect(()=>setAvoid((profile.avoid_tags||[]).join(', ')),[profile.avoid_tags]);

  async function saveProfile() {
    const body={...profile,
      age:profile.age==null||profile.age===''?null:Number(profile.age),
      height_cm:profile.height_cm==null||profile.height_cm===''?null:Number(profile.height_cm),
      weight_kg:profile.weight_kg==null||profile.weight_kg===''?null:Number(profile.weight_kg),
      target_weight_kg:profile.target_weight_kg==null||profile.target_weight_kg===''?null:Number(profile.target_weight_kg),
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
    } catch(error){onError(error.message);} finally{setBusy('');}
  }

  return <div className="profile-page"><section className="panel profile-panel"><div className="panel-heading"><div><div className="section-kicker"><Settings2 size={15}/> THÔNG TIN CÁ NHÂN</div><h2>Hồ sơ của bạn</h2></div></div><p className="panel-lead">Nhập cân nặng hiện tại và mong muốn để nhận các phương án tham khảo. Mỗi trình duyệt có phiên test riêng; chưa có tài khoản đăng nhập.</p>
    <div className="profile-grid"><label>Tuổi<input type="number" min="18" max="120" value={profile.age??''} onChange={e=>setProfile({...profile,age:e.target.value})} placeholder="Ví dụ 22"/></label><label>Chiều cao (cm)<input type="number" min="100" max="250" value={profile.height_cm??''} onChange={e=>setProfile({...profile,height_cm:e.target.value})} placeholder="Ví dụ 170"/></label><label>Cân nặng hiện tại (kg)<input type="number" min="25" max="400" step="0.1" value={profile.weight_kg??''} onChange={e=>setProfile({...profile,weight_kg:e.target.value})} placeholder="Ví dụ 65"/></label><label>Cân nặng mong muốn (kg)<input type="number" min="25" max="400" step="0.1" value={profile.target_weight_kg??''} onChange={e=>setProfile({...profile,target_weight_kg:e.target.value})} placeholder="Ví dụ 70"/></label><label>Mục tiêu<select value={profile.goal||'maintain'} onChange={e=>setProfile({...profile,goal:e.target.value})}><option value="maintain">Duy trì</option><option value="gain">Tăng cân</option><option value="lose">Giảm cân</option></select></label><label>Mục tiêu năng lượng tự nhập (kcal/ngày)<input type="number" min="900" max="5000" value={profile.target_kcal??1800} onChange={e=>setProfile({...profile,target_kcal:e.target.value})}/></label><label>Thành phần cần tránh<input value={avoid} onChange={e=>setAvoid(e.target.value)} placeholder="shrimp, pork"/></label></div>
    <div className="profile-footer"><button className="primary-button" disabled={!!busy} onClick={save}>Lưu hồ sơ</button><button className="secondary-button" disabled={!!busy} onClick={analyze}><Sparkles size={16}/>{busy==='analyze'?'Đang phân tích…':'AI gợi ý ăn uống & tập luyện'}</button>{saved&&<span className="saved-message">Đã lưu hồ sơ.</span>}</div><p className="data-note">AI đưa ra lựa chọn tham khảo, không tự đặt mức calo hay thay thế tư vấn chuyên môn.</p>
  </section>
  {profile.analysis&&<section className="panel guidance-panel"><div className="section-kicker"><Sparkles size={15}/> GỢI Ý TỪ GEMINI</div><h2>Phương án cho mục tiêu của bạn</h2><p className="panel-lead">{profile.analysis.summary}</p><h3>Ăn uống</h3><div className="guidance-grid">{profile.analysis.food_options?.map(option=><article className={`guidance-card ${profile.food_choice===option.id?'selected':''}`} key={option.id}><h4>{option.title}</h4><p>{option.detail}</p><ul>{option.examples?.map((example,index)=><li key={index}>{example}</li>)}</ul><button className="secondary-button" disabled={!!busy||profile.food_choice===option.id} onClick={()=>choose('food_choice',option.id)}>{profile.food_choice===option.id?<><Check size={15}/> Đã chọn</>:'Chọn cách ăn này'}</button></article>)}</div><h3>Tập luyện</h3><div className="guidance-grid">{profile.analysis.workout_options?.map(option=><article className={`guidance-card ${profile.workout_choice===option.id?'selected':''}`} key={option.id}><h4>{option.name}</h4><p>{option.detail}</p><button className="secondary-button" disabled={!!busy||profile.workout_choice===option.id} onClick={()=>choose('workout_choice',option.id)}>{profile.workout_choice===option.id?<><Check size={15}/> Đã chọn</>:'Chọn giáo án này'}</button></article>)}</div><p className="data-note">Gợi ý được tạo bằng {profile.analysis.model}; hãy tự kiểm tra món ăn và điều chỉnh bài tập theo thể lực.</p></section>}
  </div>;
}
