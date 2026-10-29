# มิติผี · GHOST REALM

ระยะเกม: ง่าย 15 วัน / ปกติ 20 วัน / ฝันร้าย 25 วัน บอสเสือสมิงบุกคืนสุดท้าย
ของระดับนั้น วันเริ่มเจอผีแต่ละชนิดและความกดดันจากฝูงผี/เสบียงปรับตามสัดส่วน
ยังใช้ตั๋วหนีกลับก่อนกำหนดได้ เซฟที่เล่นค้างใช้จำนวนวันใหม่ ส่วนเกมที่จบแล้วคงผลเดิม

เปิดจากโฟลเดอร์ `rush`:

```powershell
python gui.py
```

ใช้ Python, Tkinter และ Pillow 9.1 ขึ้นไป เครื่องที่ยังไม่มีหรือเป็นรุ่นเก่า
ใช้ `python -m pip install --user -U Pillow` ก่อนเปิด

ฉากศาลาอยู่ด้านซ้ายเหนือการ์ดคน 3 ใบต่อแถว ผู้มาเยือนและเมนูศาลาอยู่ขวา
ปุ่มจัดงานและจบวันอยู่ด้านล่างเสมอ คนครบ 6 คนแสดง 3 คอลัมน์ 2 แถวโดยไม่ต้องเลื่อน
การ์ดเปลี่ยนเป็นภาพอยู่ซ้ายและข้อมูลอยู่ขวาเมื่อมีคนมากกว่า 3 คน เมนูศาลาด้านขวายังเลื่อนได้
คนในฉากใช้มาตราส่วนกับจุดพื้นเดียวกับฉาก ฉากสูง 210–320 ตามความกว้าง
เพื่อให้เห็นหลังคาศาลาครบ

มีรูปลักษณ์ผู้รอดชีวิตครบ 5 แบบและคนแปลกหน้าไม่เปิดเผยใบหน้า รวมทั้งผี
5 ชนิด คนที่สุ่มเข้ามาใช้ภาพตามช่อง `look` ของเกมเดิม ไม่ได้มีภาพเฉพาะทุกชื่อ
ภาพคนแปลกหน้าไม่บอกว่าใครถูกสิงจนกว่าจะตรวจ

ชื่อหลักคือ กล้า พิกุล สิงห์ รายชื่อสุ่มชุดใหม่ไม่มีแพร โหลดเซฟเก่าจะแปลงเฉพาะ
ชื่อสำเร็จรูปเดิมเป็นชื่อใหม่ ชื่ออื่นที่ผู้เล่นตั้งเองยังคงเดิม

ใช้กฎและไฟล์เซฟเดียวกับ `main.py` (Terminal) อ่านและบันทึกความคืบหน้าจริงเมื่อเล่น

ทดสอบแยกจากเซฟจริง:

```powershell
python gui.py --check
```

เพิ่ม `--capture` เพื่อบันทึกภาพหน้าต่างบน Windows ไว้ใน `assets/talung`.
การทดสอบใช้ `check-save.json` และ `check-history.json` ในโฟลเดอร์ภาพเท่านั้น

## Product and direction

Small Thai ghost survival management game on Windows desktop using existing
Python/Tkinter rules. Preserve TH/EN, difficulties, gate inspection, jobs,
construction, ghost tiers, logs and the advanced game systems.

User-approved style: a management game using Nang Talung art. Midnight-indigo
backgrounds, colored clothes and items, amber primary actions, moss-green jobs,
restrained blood-red ghost details. Three large survivor cards per row below
the left panorama; shelter menus and gate decisions on the right.

## Direction contract

THESIS: An intimate Thai ghost shelter managed through clear daily decisions.

OWN-WORLD: Indigo night, carved puppet figures with colored clothing, warm
pavilion light, ivory labels; restrained red means ghosts or danger.

STORY: Read supplies, inspect newcomers, assign work and end the day.

FIRST VIEWPORT: Responsive compact panorama above three large cards on the
left, shelter tabs and gate on the right, stock above and persistent actions below.

FORM: User-pinned Nang Talung management world. Job dropdowns and status copy
confirm actions immediately. Title, skippable new-game story, people details,
difficulty, help and night reports share the same palette and artwork.

FINISH: Check rendered Windows captures and integration behavior, review the
result, record the implemented system and image provenance. Original game
sources remain outside this presentation layer.
