import React, { useState } from 'react';

const fmt = value => Number(value || 0).toLocaleString('vi-VN', {maximumFractionDigits: 1});
const emptyItem = (manual = false) => ({foodId: '', grams: 250, manual, search: '', skipped: false});

export default function ScanSection({call, foods, refresh, setTab, setMessage}) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [scan, setScan] = useState(null);
  const [items, setItems] = useState([]);
  const [mealType, setMealType] = useState('lunch');
  const [busy, setBusy] = useState(false);

  function update(index, changes) {
    setItems(current => current.map((item, position) => position === index ? {...item, ...changes} : item));
  }

  async function upload(selected) {
    if (!selected) { setMessage('Hãy chọn ảnh món ăn.'); return; }
    setBusy(true); setMessage(''); setScan(null); setItems([]);
    try {
      const form = new FormData(); form.append('file', selected);
      const result = await call('/api/scan', {method:'POST', body:form});
      setScan(result);
      setItems(result.dishes.map(dish => emptyItem(dish.candidates.length === 0)));
      if (result.status === 'unknown') setMessage('Gemini chưa khớp món trong danh mục. Hãy nhập tên để tìm thủ công.');
    } catch (error) {
      setMessage(`${error.message}. Bạn vẫn có thể tìm món thủ công.`);
      setScan({dishes:[{suggested_labels:[],candidates:[],visible_ingredients:[],uncertainty_reason:'Dịch vụ nhận diện không khả dụng'}],warnings:[]});
      setItems([emptyItem(true)]);
    } finally { setBusy(false); }
  }

  async function useDemo(filename) {
    const path = `/demo/${filename}`;
    const response = await fetch(path);
    const demo = new File([await response.blob()], filename, {type:'image/png'});
    setFile(demo); setPreview(path);
    await upload(demo);
  }

  async function save() {
    const active = items.filter(item => !item.skipped);
    if (!active.length) { setMessage('Hãy xác nhận ít nhất một món.'); return; }
    if (active.some(item => !item.foodId || !Number.isFinite(Number(item.grams)) || Number(item.grams) <= 0 || Number(item.grams) > 2000)) {
      setMessage('Hãy chọn món và nhập khẩu phần từ 1 đến 2000 g cho từng món.'); return;
    }
    setBusy(true); setMessage('');
    try {
      await call('/api/food-logs/batch', {method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({items:active.map(item => ({food_id:item.foodId,grams:Number(item.grams),meal_type:mealType,confirmed:true}))})});
      await refresh(); setMessage(`Đã lưu ${active.length} món đã xác nhận.`); setTab('dashboard');
    } catch (error) { setMessage(error.message); }
    finally { setBusy(false); }
  }

  const activeItems = items.filter(item => !item.skipped);
  const canSave = activeItems.length > 0 && activeItems.every(item =>
    item.foodId && Number.isFinite(Number(item.grams)) && Number(item.grams) > 0 && Number(item.grams) <= 2000);

  return <section className="grid">
    <div className="card">
      <h2>1. Tải ảnh món ăn</h2>
      <p>Gemini nhận diện từng món nhìn thấy trong ảnh. Ảnh JPG/PNG/WEBP, tối đa 5 MB.</p>
      <input type="file" accept="image/jpeg,image/png,image/webp" onChange={event => {
        const selected = event.target.files[0]; setFile(selected); setPreview(selected ? URL.createObjectURL(selected) : '');
        setScan(null); setItems([]); if (selected) void upload(selected);
      }}/>
      {preview && <img className="preview" src={preview} alt="Ảnh món ăn đang chọn"/>}
      <div className="actions">
        <button disabled={busy || !file} onClick={() => upload(file)}>{busy ? 'Đang xử lý…' : 'Thử nhận diện lại'}</button>
        <button className="secondary" disabled={busy} onClick={() => useDemo('pho_bo_synthetic.png')}>Thử ảnh một món</button>
        <button className="secondary" disabled={busy} onClick={() => useDemo('pho_bo_com_tam_synthetic.png')}>Thử ảnh hai món</button>
      </div>
      {scan?.warnings?.length > 0 && <p className="warn">{scan.warnings.join(' ')}</p>}
      {scan && <p className="muted">Gemini chỉ gợi ý tên món. Bạn cần xác nhận món và số gam trước khi lưu.</p>}
    </div>
    <div className="card">
      <h2>2. Xác nhận từng món</h2>
      {!scan && <p>Tải ảnh để xem gợi ý từ Gemini.</p>}
      {scan?.dishes.map((dish, index) => {
        const item = items[index];
        if (!item) return null;
        const selected = foods.find(food => food.id === item.foodId);
        const values = selected ? Object.fromEntries(['kcal','protein','carb','fat'].map(key => [key, selected[`${key}_100g`] * Number(item.grams || 0) / 100])) : null;
        const filtered = foods.filter(food => !item.search || food.name.toLocaleLowerCase('vi').includes(item.search.toLocaleLowerCase('vi')) || food.aliases.some(alias => alias.toLocaleLowerCase('vi').includes(item.search.toLocaleLowerCase('vi'))));
        return <div className="dish-review" key={index}>
          <div className="dish-heading"><h3>Món {index + 1}</h3><button className="text-button" onClick={() => update(index, {skipped:!item.skipped})}>{item.skipped ? 'Khôi phục' : 'Không có món này trong ảnh'}</button></div>
          {!item.skipped && <>
            {dish.suggested_labels.length > 0 && <p>Gemini thấy: <strong>{dish.suggested_labels.join(' / ')}</strong></p>}
            {dish.visible_ingredients.length > 0 && <p className="muted">Thành phần nhìn thấy: {dish.visible_ingredients.join(', ')}</p>}
            {dish.uncertainty_reason && <p className="muted">{dish.uncertainty_reason}</p>}
            {dish.candidates.length > 0 && !item.manual && <div className="candidate-list" role="group" aria-label={`Gợi ý cho món ${index+1}`}>
              {dish.candidates.map(food => <button key={food.id} className={`candidate ${item.foodId === food.id ? 'selected' : ''}`} aria-pressed={item.foodId === food.id} onClick={() => update(index,{foodId:food.id})}>{food.name}</button>)}
            </div>}
            {!item.manual && <button className="text-button" onClick={() => update(index,{manual:true,foodId:''})}>Không đúng món nào? Nhập tay</button>}
            {item.manual && <div className="manual-entry">
              <label>Nhập tên món<input value={item.search} onChange={event => update(index,{search:event.target.value,foodId:''})} placeholder="Tên món bạn thấy trong ảnh"/></label>
              <label>Chọn món trong danh mục<select value={item.foodId} onChange={event => update(index,{foodId:event.target.value})}><option value="">Chọn món</option>{filtered.map(food => <option value={food.id} key={food.id}>{food.name}</option>)}</select></label>
              {filtered.length === 0 && <p className="warn">Danh mục chưa có món này. Cần bổ sung dữ liệu có nguồn trước khi tính dinh dưỡng.</p>}
              {dish.candidates.length > 0 && <button className="text-button" onClick={() => update(index,{manual:false,foodId:'',search:''})}>Quay lại gợi ý Gemini</button>}
            </div>}
            <label>Khẩu phần đã xác nhận (g)<input type="number" min="1" max="2000" value={item.grams} onChange={event => update(index,{grams:event.target.value})}/></label>
            {values && <div className="result"><p><strong>{fmt(values.kcal)} kcal</strong> · Đạm {fmt(values.protein)} g · Bột đường {fmt(values.carb)} g · Béo {fmt(values.fat)} g</p><p>Nguồn: {selected.source_reference}</p>{!selected.is_verified && <p className="warn">Dữ liệu thử nghiệm, chưa được kiểm chứng.</p>}</div>}
          </>}
        </div>;
      })}
      {scan && <><button className="text-button" onClick={() => {
        if (items.length >= 5) { setMessage('Tối đa 5 món trong một ảnh.'); return; }
        setScan(current => ({...current,dishes:[...current.dishes,{suggested_labels:[],candidates:[],visible_ingredients:[],uncertainty_reason:'Món bạn tự thêm'}]}));
        setItems(current => [...current,emptyItem(true)]);
      }}>+ Thêm món Gemini bỏ sót</button>
      <label>Loại bữa<select value={mealType} onChange={event => setMealType(event.target.value)}><option value="breakfast">Sáng</option><option value="lunch">Trưa</option><option value="dinner">Tối</option><option value="snack">Phụ</option></select></label>
      <button disabled={busy || !canSave} onClick={save}>Xác nhận và lưu {activeItems.length} món</button></>}
    </div>
  </section>;
}
