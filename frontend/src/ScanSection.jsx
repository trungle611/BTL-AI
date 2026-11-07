import React, {useRef, useState} from 'react';
import {AlertCircle, Check, CheckCircle2, CloudUpload, ImagePlus, LoaderCircle, RefreshCw, Search, Trash2, X} from 'lucide-react';

const fmt = value => Number(value || 0).toLocaleString('vi-VN',{maximumFractionDigits:1});
const mealLabels = {breakfast:'Bữa sáng',lunch:'Bữa trưa',dinner:'Bữa tối',snack:'Bữa phụ'};
const emptyItem = (manual=false) => ({foodId:'',grams:250,manual,search:'',custom:false,skipped:false,estimated:false,allowMissingNutrition:false,kcal:'',protein:'',carb:'',fat:''});
const nutrientKeys=['kcal','protein','carb','fat'];
const hasNutrition=food=>Number(food?.kcal_100g)>0;
function suggestedItem(dish) {
  const catalogFood=dish.candidates.find(hasNutrition);
  if(catalogFood)return {...emptyItem(),foodId:catalogFood.id};
  const estimate=dish.estimated_nutrition_100g;
  return {...emptyItem(true),search:dish.suggested_labels[0]||'',custom:true,estimated:!!estimate,
    ...Object.fromEntries(nutrientKeys.map(key=>[key,estimate?.[key]??'']))};
}

export default function ScanSection({call,foods,onAdded}) {
  const picker = useRef(null);
  const [file,setFile] = useState(null);
  const [preview,setPreview] = useState('');
  const [scan,setScan] = useState(null);
  const [items,setItems] = useState([]);
  const [mealType,setMealType] = useState('lunch');
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [success,setSuccess] = useState('');
  const [dragging,setDragging] = useState(false);

  function update(index,changes) {setItems(current=>current.map((item,i)=>i===index?{...item,...changes}:item));}
  function clearPhoto() {setFile(null);setPreview('');setScan(null);setItems([]);setError('');if(picker.current)picker.current.value='';}

  async function recognize(selected) {
    if (!selected) return;
    if (!['image/jpeg','image/png','image/webp'].includes(selected.type)) {clearPhoto();setError('Ảnh không hợp lệ. Hãy chọn JPG, PNG hoặc WEBP.');return;}
    if (selected.size > 5*1024*1024) {clearPhoto();setError('Ảnh vượt quá 5 MB. Hãy chọn ảnh nhỏ hơn.');return;}
    setFile(selected);setPreview(URL.createObjectURL(selected));setScan(null);setItems([]);setError('');setSuccess('');setBusy('scan');
    try {
      const form=new FormData();form.append('file',selected);
      const result=await call('/api/scan',{method:'POST',body:form});
      setScan(result);
      setItems(result.dishes.map(suggestedItem));
      if(result.status==='unknown')setError('Chưa nhận diện được món trong danh mục. Bạn có thể tìm tên món thủ công.');
    } catch(err) {
      setError(`${err.message}. Bạn có thể thử lại hoặc nhập món thủ công.`);
      setScan({request_id:crypto.randomUUID(),dishes:[{suggested_labels:[],candidates:[],visible_ingredients:[],uncertainty_reason:'Chưa có gợi ý từ AI'}],warnings:[]});
      setItems([emptyItem(true)]);
    } finally {setBusy('');}
  }

  async function demo(filename) {
    const response=await fetch(`/demo/${filename}`);
    if(!response.ok){setError('Không tải được ảnh mẫu.');return;}
    const selected=new File([await response.blob()],filename,{type:'image/png'});
    await recognize(selected);
  }

  const active=items.filter(item=>!item.skipped);
  const ready=active.length>0&&active.every(item=>
    (item.foodId||(item.custom&&item.search.trim().length>=2&&
      ((Number(item.kcal)>0&&nutrientKeys.every(key=>item[key]!==''&&item[key]!=null))||item.allowMissingNutrition)))&&
    Number(item.grams)>0&&Number(item.grams)<=2000);
  async function save() {
    if(!ready)return;
    setBusy('save');setError('');
    try {
      await call('/api/food-logs/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmation_id:scan.request_id,items:active.map(item=>({food_id:item.custom?null:item.foodId,custom_food:item.custom?{name:item.search.trim(),...Object.fromEntries(['kcal','protein','carb','fat'].map(key=>[`${key}_100g`,Number(item[key]||0)]))}:null,grams:Number(item.grams),meal_type:mealType,confirmed:true}))})});
      clearPhoto();setSuccess(`Đã thêm ${active.length} món vào thực đơn hôm nay.`);await onAdded();
    } catch(err){setError(err.message);} finally{setBusy('');}
  }

  return <div className="food-flow">
    <section className="panel upload-panel" aria-labelledby="upload-title">
      <div className="panel-heading"><div><div className="section-kicker"><ImagePlus size={15}/> NHẬN DIỆN MÓN ĂN</div><h2 id="upload-title">Tải ảnh bữa ăn</h2></div><span className="step-pill">BƯỚC 01</span></div>
      <p className="panel-lead">Chọn hoặc kéo thả ảnh. Gemini sẽ gợi ý từng món để bạn kiểm tra trước khi thêm.</p>
      <input ref={picker} className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" onChange={event=>{const selected=event.target.files[0];if(selected)void recognize(selected);}}/>
      <div className={`drop-zone ${dragging?'dragging':''} ${preview?'has-preview':''}`} onDragOver={event=>{event.preventDefault();setDragging(true);}} onDragLeave={()=>setDragging(false)} onDrop={event=>{event.preventDefault();setDragging(false);const selected=event.dataTransfer.files[0];if(selected)void recognize(selected);}}>
        {preview?<><img src={preview} alt="Ảnh bữa ăn đang được kiểm tra"/><div className="photo-actions"><button className="photo-button" disabled={busy} onClick={()=>picker.current?.click()}><RefreshCw size={16}/> Đổi ảnh</button><button className="photo-button" disabled={busy} onClick={clearPhoto}><Trash2 size={16}/> Xóa ảnh</button></div></>:<><div className="upload-icon"><CloudUpload size={28}/></div><strong>Kéo thả ảnh món ăn vào đây</strong><span>hoặc chọn ảnh từ thiết bị của bạn</span><button className="primary-button" onClick={()=>picker.current?.click()}><ImagePlus size={17}/> Tải ảnh</button><small>JPG, PNG hoặc WEBP · Tối đa 5 MB</small></>}
      </div>
      {preview&&!busy&&<button className="link-button retry-button" onClick={()=>recognize(file)}><RefreshCw size={15}/> Thử nhận diện lại</button>}
      {busy&&<div className="inline-state loading" role="status"><LoaderCircle size={18} className="spin"/><span>{busy==='scan'?'Đang phân tích ảnh…':'Đang thêm món…'}</span></div>}
      {error&&<div className="inline-state error" role="alert"><AlertCircle size={18}/><span>{error}</span></div>}
      {success&&<div className="inline-state success" role="status"><CheckCircle2 size={18}/><span>{success}</span></div>}
      <div className="demo-links"><span>Ảnh thử nhanh:</span><button disabled={busy} onClick={()=>demo('pho_bo_synthetic.png')}>Một món</button><button disabled={busy} onClick={()=>demo('pho_bo_com_tam_synthetic.png')}>Hai món</button></div>
    </section>

    {scan&&<section className="panel recognition-panel" aria-labelledby="recognition-title">
      <div className="panel-heading"><div><div className="section-kicker"><CheckCircle2 size={15}/> KIỂM TRA KẾT QUẢ</div><h2 id="recognition-title">Xác nhận món ăn</h2></div><span className="step-pill">BƯỚC 02</span></div>
      <p className="panel-lead">Chọn đúng món và chỉnh khẩu phần. Món chưa xác nhận sẽ không tính vào tổng dinh dưỡng.</p>
      {scan.dishes.map((dish,index)=>{
        const item=items[index];if(!item)return null;
        const usableCandidates=dish.candidates.filter(hasNutrition);
        const selected=foods.find(food=>food.id===item.foodId)||usableCandidates.find(food=>food.id===item.foodId);
        const previewFood=selected||(!item.manual?usableCandidates[0]:null);
        const values=item.custom&&nutrientKeys.some(key=>item[key]!==''&&item[key]!=null)?Object.fromEntries(nutrientKeys.map(key=>[key,Number(item[key]||0)*Number(item.grams||0)/100])):previewFood?Object.fromEntries(nutrientKeys.map(key=>[key,previewFood[`${key}_100g`]*Number(item.grams||0)/100])):null;
        const query=item.search.toLocaleLowerCase('vi');
        const filtered=foods.filter(food=>hasNutrition(food)&&(!query||food.name.toLocaleLowerCase('vi').includes(query)||food.aliases.some(alias=>alias.toLocaleLowerCase('vi').includes(query))));
        return <div className={`recognized-dish ${item.skipped?'is-skipped':''}`} key={index}>
          <div className="dish-top"><div><span className="dish-number">MÓN {String(index+1).padStart(2,'0')}</span><h3>{dish.suggested_labels[0]||'Món chưa rõ'}</h3></div><button className="subtle-button" onClick={()=>update(index,{skipped:!item.skipped})}>{item.skipped?'Khôi phục':'Bỏ qua món này'}</button></div>
          {!item.skipped&&<>
            {dish.visible_ingredients.length>0&&<p className="observed">Nhìn thấy: {dish.visible_ingredients.join(', ')}</p>}
            {dish.uncertainty_reason&&<p className="observed">{dish.uncertainty_reason}</p>}
            {!item.manual&&usableCandidates.length>0&&<div className="choice-grid" role="group" aria-label={`Gợi ý món ${index+1}`}>{usableCandidates.map(food=><button key={food.id} className={`food-choice ${item.foodId===food.id?'chosen':''}`} aria-pressed={item.foodId===food.id} onClick={()=>update(index,{foodId:food.id})}><span>{food.name}</span>{item.foodId===food.id&&<Check size={17}/>}</button>)}</div>}
            {!item.manual&&<button className="link-button" onClick={()=>update(index,{manual:true,custom:true,foodId:'',search:dish.suggested_labels[0]||'',estimated:!!dish.estimated_nutrition_100g,...Object.fromEntries(nutrientKeys.map(key=>[key,dish.estimated_nutrition_100g?.[key]??'']))})}><Search size={15}/> Gợi ý chưa đúng? Nhập tay</button>}
            {item.manual&&<div className="manual-fields">
              <label>Tên món bạn nhận ra<input value={item.search} onChange={event=>update(index,{search:event.target.value,foodId:'',custom:true,estimated:false,allowMissingNutrition:false,...Object.fromEntries(nutrientKeys.map(key=>[key,'']))})} placeholder="Nhập tên món"/></label>
              {filtered.length>0&&<label>Hoặc chọn món trong danh mục<select value={item.custom?'':item.foodId} onChange={event=>update(index,{foodId:event.target.value,custom:false})}><option value="">Chọn món</option>{filtered.map(food=><option key={food.id} value={food.id}>{food.name}</option>)}</select></label>}
              <label className="custom-choice"><input type="checkbox" checked={item.custom} onChange={event=>update(index,{custom:event.target.checked,foodId:''})}/> Món chưa có trong danh mục — tự xác nhận tên và dinh dưỡng</label>
              {item.custom&&<>
                <div className="custom-macros">{[['kcal','Calo (kcal)'],['protein','Protein (g)'],['carb','Carb (g)'],['fat','Chất béo (g)']].map(([key,label])=><label key={key}>{label} / 100 g<input type="number" min="0" step="0.1" value={item[key]} onChange={event=>update(index,{[key]:event.target.value,allowMissingNutrition:false})} placeholder="Chưa rõ"/></label>)}</div>
                <p className="data-note">{item.estimated?'Gemini ước tính theo 100 g, bạn hãy sửa nếu cần. ':'Chưa có đủ số liệu; bạn có thể nhập tay. '}Chỉ lưu đủ dinh dưỡng khi cả bốn ô đã được kiểm tra.</p>
                {!(Number(item.kcal)>0&&nutrientKeys.every(key=>item[key]!==''&&item[key]!=null))&&<label className="custom-choice"><input type="checkbox" checked={item.allowMissingNutrition} onChange={event=>update(index,{allowMissingNutrition:event.target.checked})}/> Vẫn thêm món dù thiếu dinh dưỡng (ô trống tính là 0)</label>}
              </>}
              {usableCandidates.length>0&&<button className="link-button" onClick={()=>update(index,{manual:false,custom:false,foodId:usableCandidates[0].id,search:''})}><X size={15}/> Quay lại gợi ý</button>}
            </div>}
            <div className="result-fields"><label>Khẩu phần<input type="number" min="1" max="2000" value={item.grams} onChange={event=>update(index,{grams:event.target.value})}/></label><span className="unit-label">gram</span></div>
            {values&&<div className={`food-nutrition ${!selected?'preview-values':''}`}><div><b>{fmt(values.kcal)}</b><span>kcal</span></div><div><b>{fmt(values.protein)}g</b><span>Protein</span></div><div><b>{fmt(values.carb)}g</b><span>Carb</span></div><div><b>{fmt(values.fat)}g</b><span>Chất béo</span></div></div>}
            {item.custom&&item.estimated&&<p className="source-note">Ước tính từ Gemini theo ảnh, chưa kiểm chứng; chỉ cộng vào thực đơn sau khi bạn xác nhận.</p>}
            {previewFood&&<p className="source-note">Nguồn: {previewFood.source_reference}{!previewFood.is_verified&&' · Dữ liệu demo chưa kiểm chứng'}</p>}
          </>}
        </div>;
      })}
      <button className="link-button add-missed" onClick={()=>{if(items.length>=5){setError('Tối đa 5 món trong một ảnh.');return;}setScan(current=>({...current,dishes:[...current.dishes,{suggested_labels:[],candidates:[],visible_ingredients:[],uncertainty_reason:'Món bạn tự thêm'}]}));setItems(current=>[...current,emptyItem(true)]);}}>+ Thêm món Gemini bỏ sót</button>
      <div className="confirm-footer"><label>Bữa ăn<select value={mealType} onChange={event=>setMealType(event.target.value)}>{Object.entries(mealLabels).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label><button className="primary-button" disabled={!ready||busy} onClick={save}><Check size={18}/> Xác nhận thêm {active.length} món</button></div>
    </section>}
  </div>;
}
