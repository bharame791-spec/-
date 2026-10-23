# ما زلتُ أختاركِ: تصميم الكتاب

- `manuscript.txt`: نص الرواية. أي تعديل على النص بيصير هون.
- `build.py`: بيبني الكتاب كامل من النص (بيحتاج Python و Node مع Playwright و poppler-utils).
- `output/`: الملفات الجاهزة:
  - `ma-zilt-akhtaruki-print-interior.pdf`: داخل الكتاب للمطبعة، قياس A5، كل فصل بيبلش على صفحة يسار.
  - `ma-zilt-akhtaruki-cover.pdf`: الغلاف الأمامي والخلفي.
  - `ma-zilt-akhtaruki-screen.pdf`: نسخة كاملة للقراءة على الموبايل والكمبيوتر.

لإعادة البناء بعد أي تعديل: `python3 build.py`

الخطوط: أميري (النص)، عارف رقعة (العناوين)، ريم كوفي (التفاصيل الصغيرة)، وكلها مرخّصة برخصة SIL Open Font License.
