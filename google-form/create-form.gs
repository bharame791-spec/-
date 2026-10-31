/**
 * مبادرة «ارتقاء» | مركز 180 درجة
 * سكربت Google Apps Script ينشئ نموذج تسجيل Google Form جاهز
 * مع جدول بيانات (Google Sheets) لاستقبال الردود.
 *
 * طريقة الاستخدام: انظر google-form/README.md
 */
function createIrtiqaForm() {
  var form = FormApp.create('مبادرة «ارتقاء» | مركز 180 درجة - التسجيل');

  form.setDescription(
    'مبادرة تعليمية مجانية لمدة ثلاثة أشهر، تهدف إلى تعزيز التربية الإسلامية لدى طلبة ' +
    'المرحلتين الابتدائية والإعدادية، من خلال برنامج متكامل يجمع بين القرآن الكريم، ' +
    'والعقيدة، والفقه، والسيرة النبوية، والآداب والأخلاق الإسلامية، بأساليب تعليمية ' +
    'تفاعلية تسهم في بناء جيل واعٍ بقيمه ومتمسك بأخلاقه.\n\n' +
    'معًا نحو جيل يرتقي بعلمه وأخلاقه.'
  );
  form.setConfirmationMessage('تم استلام التسجيل بنجاح، جزاكم الله خيرًا. سنتواصل معكم عبر واتساب.');
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setLimitOneResponsePerUser(false);
  form.setProgressBar(true);

  // ===== أولًا: بيانات الطالب =====
  form.addSectionHeaderItem().setTitle('أولًا: بيانات الطالب');

  form.addTextItem()
    .setTitle('الاسم الرباعي للطالب')
    .setRequired(true);

  var stageItem = form.addMultipleChoiceItem()
    .setTitle('المرحلة الدراسية')
    .setRequired(true);

  // صفحة صفوف المرحلة الابتدائية
  var primaryPage = form.addPageBreakItem().setTitle('الصف الدراسي - المرحلة الابتدائية');
  form.addListItem()
    .setTitle('الصف الدراسي')
    .setChoiceValues(['الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس', 'السادس'])
    .setRequired(true);

  // صفحة صفوف المرحلة الإعدادية
  var prepPage = form.addPageBreakItem().setTitle('الصف الدراسي - المرحلة الإعدادية');
  form.addListItem()
    .setTitle('الصف الدراسي ')
    .setChoiceValues(['السابع', 'الثامن', 'التاسع'])
    .setRequired(true);

  // صفحة بقية البيانات
  var restPage = form.addPageBreakItem().setTitle('تكملة بيانات الطالب');

  form.addMultipleChoiceItem()
    .setTitle('أيام دوام الطالب في المدرسة')
    .setChoiceValues(['السبت - الاثنين - الأربعاء', 'الأحد - الثلاثاء - الخميس'])
    .setRequired(true);

  form.addTextItem()
    .setTitle('اسم المدرسة')
    .setRequired(true);

  form.addDateItem()
    .setTitle('تاريخ الميلاد (اختياري)')
    .setRequired(false);

  // ===== ثانيًا: بيانات ولي الأمر =====
  form.addSectionHeaderItem().setTitle('ثانيًا: بيانات ولي الأمر');

  form.addTextItem()
    .setTitle('اسم ولي الأمر')
    .setRequired(true);

  var phoneValidation = FormApp.createTextValidation()
    .setHelpText('يرجى إدخال رقم هاتف صحيح (أرقام فقط، ويمكن البدء بـ +)')
    .requireTextMatchesPattern('^\\+?[0-9 ]{8,16}$')
    .build();
  form.addTextItem()
    .setTitle('رقم هاتف ولي الأمر (واتساب)')
    .setValidation(phoneValidation)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('صلة القرابة بالطالب')
    .setChoiceValues(['الأب', 'الأم', 'الأخ', 'الأخت', 'الجد', 'الجدة'])
    .showOtherOption(true)
    .setRequired(true);

  // ===== التفرّع حسب المرحلة =====
  stageItem.setChoices([
    stageItem.createChoice('ابتدائية', primaryPage),
    stageItem.createChoice('إعدادية', prepPage)
  ]);
  // setGoToPage على فاصل صفحة يحدد الوجهة بعد إنهاء الصفحة التي قبله.
  // الصفحة التي قبل prepPage هي صفحة صفوف الابتدائي، فنقفز منها إلى بقية البيانات
  // حتى لا يرى طالب الابتدائي صفوف الإعدادي.
  prepPage.setGoToPage(restPage);

  // ===== جدول بيانات الردود =====
  var sheet = SpreadsheetApp.create('ردود التسجيل - مبادرة ارتقاء');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());

  var publicUrl = form.getPublishedUrl();
  var shortUrl = form.shortenFormUrl(publicUrl);

  Logger.log('رابط التسجيل (للمشاركة): ' + shortUrl);
  Logger.log('رابط التسجيل الكامل: ' + publicUrl);
  Logger.log('رابط تعديل النموذج: ' + form.getEditUrl());
  Logger.log('جدول الردود: ' + sheet.getUrl());
}
